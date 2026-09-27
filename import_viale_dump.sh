#!/bin/bash
# Importe le dump de viale-manager-2 (cf. extract_dump.sh) dans le schéma viale_manager.
#
# Tout passe par les conteneurs docker compose : l'hôte n'a besoin que de Docker.
# Le dump est copié dans le service « db » (empreinte vérifiée), où tournent pg_restore
# et psql : aucun gros flux ne traverse « exec » dans un pipe (podman y perd parfois
# des données). Les commandes Django tournent dans « web » s'il tourne (production),
# sinon via uv sur l'hôte (développement).
#
# Prérequis : les migrations sont appliquées (au démarrage de « web » en production,
# « uv run python manage.py migrate » en développement) et les tables viale sont vides.
#
# Usage : ./import_viale_dump.sh [dump]   (par défaut ./viale_dump.dump)
#         COMPOSE="podman-compose" ./import_viale_dump.sh   pour un autre outil compose
set -eo pipefail

DUMP="${1:-./viale_dump.dump}"
COMPOSE="${COMPOSE:-docker compose}"
DUMP_DB=/tmp/viale_dump.dump

[ -f "$DUMP" ] || { echo "Dump introuvable : $DUMP" >&2; exit 1; }

# Exécute le script bash lu sur stdin dans le conteneur db, avec les arguments donnés.
in_db() {
    $COMPOSE exec -T db bash -s -- "$@"
}
if $COMPOSE exec -T web true > /dev/null 2>&1; then
    MANAGE="$COMPOSE exec -T web python manage.py"
else
    MANAGE="uv run python manage.py"
fi

echo "=== Étape 1 : copie du dump dans le conteneur db ==="
$COMPOSE exec -T db bash -c "cat > $DUMP_DB" < "$DUMP"
trap '$COMPOSE exec -T db rm -f "$DUMP_DB" > /dev/null 2>&1' EXIT
if [ "$(in_db "$DUMP_DB" <<< 'sha256sum "$1" | cut -d" " -f1')" != "$(sha256sum "$DUMP" | cut -d' ' -f1)" ]; then
    echo "Copie du dump corrompue : relancez le script." >&2
    exit 1
fi
echo "  -> OK"

# Étapes 2 à 4, dans le conteneur db. Délimiteur entre apostrophes : rien n'est
# interprété par l'hôte.
in_db "$DUMP_DB" <<'SCRIPT'
set -eo pipefail
DUMP="$1"
PSQL=(psql -v ON_ERROR_STOP=1 -q -U "$POSTGRES_USER" -d "$POSTGRES_DB")

# Tables gérées par Django (on ignore les tables Laravel: failed_jobs, jobs, migrations,
# model_has_permissions, model_has_roles, password_reset_tokens, permissions,
# personal_access_tokens, role_has_permissions, roles, users ; options sert à l'étape 5)
# Ordre des clés étrangères : une table après celles qu'elle référence, sinon
# le COPY entier échoue.
TABLES=(
    auto_mails
    messages
    profiles
    houses
    rooms
    maisonnees_planning
    houses_in_maisonnees_planning
    reservations
    visitors
    sejours
    assignations_maisonnees
)

# Données d'une table du dump, schéma public remplacé par viale_manager.
restore_data() {
    pg_restore --data-only -t "$1" -f - "$DUMP" | sed 's/^COPY public\./COPY viale_manager./'
}

echo ""
echo "=== Étape 2 : vérifications ==="
if [ -z "$("${PSQL[@]}" -tAc "SELECT to_regclass('viale_manager.visitors')")" ]; then
    echo "Le schéma viale_manager n'existe pas : appliquez d'abord les migrations." >&2
    exit 1
fi
for TABLE in "${TABLES[@]}"; do
    N=$("${PSQL[@]}" -tAc "SELECT count(*) FROM viale_manager.$TABLE")
    if [ "$N" != "0" ]; then
        echo "viale_manager.$TABLE contient déjà $N ligne(s) : import annulé pour éviter les doublons." >&2
        exit 1
    fi
done
echo "  -> OK"

echo ""
echo "=== Étape 3 : import des données ==="
for TABLE in "${TABLES[@]}"; do
    echo -n "  -> $TABLE ... "
    if [ "$TABLE" = "assignations_maisonnees" ]; then
        # house_id=0 (« à placer » en Laravel) : recréées à l'ouverture du planning.
        restore_data "$TABLE" | awk '/^COPY/{print; next} /^\\\./{print; next} $3 != "0"' | "${PSQL[@]}" > /dev/null
    else
        restore_data "$TABLE" | "${PSQL[@]}" > /dev/null
    fi
    echo "OK"
done

echo ""
echo "=== Étape 4 : recalage des séquences ==="
# Tables avec une PK serial (houses_in_maisonnees_planning n'a pas de séquence dans le dump)
for TABLE in "${TABLES[@]}"; do
    [ "$TABLE" = "houses_in_maisonnees_planning" ] && continue
    echo -n "  -> séquence $TABLE ... "
    "${PSQL[@]}" -c "SELECT setval(pg_get_serial_sequence('viale_manager.$TABLE', 'id'), COALESCE(MAX(id), 1)) FROM viale_manager.$TABLE" > /dev/null
    echo "OK"
done
SCRIPT

echo ""
echo "=== Étape 5 : coordonnées de la Viale (options Laravel → Constance) ==="
# La table options est lue via une table temporaire ; sortie : « CLÉ<tab>valeur ».
OPTIONS=$(in_db "$DUMP_DB" <<'SCRIPT'
set -eo pipefail
{
    echo "CREATE TEMP TABLE options (id bigint, name text, value text, created_at timestamp, updated_at timestamp, description text);"
    pg_restore --data-only -t options -f - "$1" | sed 's/^COPY public\.options /COPY options /'
    echo "SELECT CASE name WHEN 'email' THEN 'VIALE_EMAIL' WHEN 'phone' THEN 'VIALE_TELEPHONE' ELSE 'VIALE_ADRESSE' END,
                 translate(value, E'\t\n', '  ')
          FROM options WHERE name IN ('email', 'phone', 'address') AND coalesce(value, '') <> '';"
} | psql -v ON_ERROR_STOP=1 -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -F $'\t'
SCRIPT
)
while IFS=$'\t' read -r KEY VALUE; do
    [ -n "$KEY" ] || continue
    $MANAGE constance set "$KEY" "$VALUE" < /dev/null
    echo "  -> $KEY = $VALUE"
done <<< "$OPTIONS"

echo ""
echo "=== Import terminé ==="
