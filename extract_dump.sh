#!/bin/bash
# Exporte la base de viale-manager-2 (Laravel, en production dans Docker) pour
# import_viale_dump.sh. À lancer sur le serveur, où tourne le conteneur de la base.
#
# Usage : ./extract_dump.sh [dump]   (par défaut ./viale_dump.dump)
#         CONTAINER=... DB_USER=... DB_NAME=... ./extract_dump.sh   si les noms diffèrent
set -eo pipefail

DUMP="${1:-./viale_dump.dump}"
CONTAINER="${CONTAINER:-viale_manager_db}"
DB_USER="${DB_USER:-viale}"
DB_NAME="${DB_NAME:-viale_manager}"

# Écrit dans un fichier temporaire : un échec ne laisse pas un dump tronqué à la place de l'ancien.
trap 'rm -f "$DUMP.tmp"' EXIT
docker exec "$CONTAINER" pg_dump -Fc -U "$DB_USER" "$DB_NAME" > "$DUMP.tmp"
mv "$DUMP.tmp" "$DUMP"
echo "Dump écrit : $DUMP ($(du -h "$DUMP" | cut -f1))"
