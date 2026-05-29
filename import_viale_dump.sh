#!/bin/bash
set -e

DUMP="./viale_dump.dump"
PGHOST=localhost
PGPORT=5996
PGUSER=postgres
PGPASSWORD=password
PGDATABASE=dj_asbl
export PGPASSWORD

PSQL="psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE"

# Tables gérées par Django (on ignore les tables Laravel: failed_jobs, jobs, migrations,
# model_has_permissions, model_has_roles, options, password_reset_tokens, permissions,
# personal_access_tokens, role_has_permissions, roles, users)
TABLES=(
    assignations_maisonnees
    auto_mails
    houses
    houses_in_maisonnees_planning
    maisonnees_planning
    messages
    profiles
    reservations
    rooms
    sejours
    visitors
)

echo "=== Étape 1 : migrations Django ==="
uv run python manage.py migrate

echo ""
echo "=== Étape 2 : import des données ==="
for TABLE in "${TABLES[@]}"; do
    echo -n "  -> $TABLE ... "
    # Extrait les données de la table, remplace le schéma public par viale_manager
    pg_restore --data-only -t "$TABLE" -f - "$DUMP" \
        | sed 's/COPY public\./COPY viale_manager./g' \
        | $PSQL -q
    echo "OK"
done

echo ""
echo "=== Étape 3 : recalage des séquences ==="
# Tables avec une PK serial (houses_in_maisonnees_planning n'a pas de séquence dans le dump)
TABLES_WITH_SEQ=(
    assignations_maisonnees
    auto_mails
    houses
    maisonnees_planning
    messages
    profiles
    reservations
    rooms
    sejours
    visitors
)

for TABLE in "${TABLES_WITH_SEQ[@]}"; do
    echo -n "  -> séquence $TABLE ... "
    $PSQL -q -c "SELECT setval(
        pg_get_serial_sequence('viale_manager.$TABLE', 'id'),
        COALESCE(MAX(id), 1)
    ) FROM viale_manager.$TABLE;"
    echo "OK"
done

echo ""
echo "=== Import terminé ==="