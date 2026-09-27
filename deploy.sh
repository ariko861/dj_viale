#!/bin/bash
# Reconstruit l'image et relance web et cron, puis attend que web ait démarré.
# Les migrations sont appliquées par web à son démarrage (entrypoint.sh).
#
# Usage : ./deploy.sh
#         COMPOSE="podman-compose" ./deploy.sh   pour un autre outil compose
set -eo pipefail

cd "$(dirname "$0")"
COMPOSE="${COMPOSE:-docker compose}"
# --profile prod : sans effet en production ; en développement, compose.override.yml
# place web et cron dans ce profil.
COMPOSE="$COMPOSE --profile prod"
TIMEOUT=180

echo "=== Construction de l'image ==="
$COMPOSE build web cron

echo ""
echo "=== Relance des services ==="
$COMPOSE up -d db
$COMPOSE up -d --force-recreate web cron

echo ""
echo "=== Démarrage de web (migrations) ==="
for (( i = 0; i < TIMEOUT; i += 2 )); do
    LOGS=$($COMPOSE logs web 2>&1 || true)
    if grep -q "Listening at" <<< "$LOGS"; then
        grep -E "Applying|No migrations to apply" <<< "$LOGS" || true
        echo "  -> web a démarré."
        exit 0
    fi
    if grep -qE "Traceback|CommandError|Worker failed to boot" <<< "$LOGS"; then
        echo "$LOGS" | tail -30 >&2
        echo "Échec du démarrage de web." >&2
        exit 1
    fi
    sleep 2
done
echo "web n'a pas démarré après ${TIMEOUT}s : voir « $COMPOSE logs web »." >&2
exit 1
