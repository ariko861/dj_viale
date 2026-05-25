# dj-asbl

Application de gestion pour ASBL (Association Sans But Lucratif). Permet de gérer les membres, les organes, les réunions, les mandats et la communication par email.

## Fonctionnalités

- **Membres & organes** — gestion des membres, de leurs adhésions aux organes (conseil d'administration, assemblée générale, etc.) avec dates de début/fin de mandat
- **Réunions** — planification des réunions par organe, suivi des présences (accepté, absent, procuration), export iCalendar
- **Procurations** — gestion des délégations de vote entre membres
- **Documents** — modèles de documents Word (`.docx`) générés à la volée avec les données de la réunion ; documents attachés aux réunions (publics via lien ou privés)
- **Envoi d'emails** — envoi groupé aux membres d'une réunion depuis l'admin, avec éditeur rich text, pièce jointe iCal et documents

## Prérequis

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL

## Installation

```bash
git clone git@github.com-ariko:ariko681/dj-asbl.git
cd dj-asbl
uv sync
```

Créer un fichier `.env` à la racine :

```dotenv
DATABASE_URL=postgres://user:password@localhost:5432/dj_asbl
SECRET_KEY=une-clé-secrète

POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=dj_asbl

SMTP_HOST=127.0.0.1
SMTP_PORT=1025
```

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

L'interface d'administration est accessible sur `http://localhost:8000/admin/`.

## Déploiement (Docker / Podman)

```bash
podman compose up -d --build
```

Les variables d'environnement sont lues depuis le fichier `.env`. Les variables obligatoires sont `SECRET_KEY`, `POSTGRES_PASSWORD` et `DJANGO_ALLOWED_HOSTS` (nom de domaine de production).

Le dossier `media/` (fichiers uploadés) est persisté dans un volume nommé.

### Override

Un fichier `compose.override.yml` permet de personnaliser le déploiement sans modifier `compose.yml` :

```yaml
services:
  web:
    container_name: mon_asbl_web
    ports: []           # désactiver si derrière un reverse proxy
    environment:
      MA_VARIABLE: valeur
  db:
    container_name: mon_asbl_db
```

Le préfixe des noms de conteneurs se configure via `CONTAINER_PREFIX` dans `.env`.

## Configuration dynamique

Certains paramètres sont modifiables depuis l'admin sans redéploiement (*Configuration > Config*) :

| Paramètre | Description |
|---|---|
| `REPLY_TO_EMAIL` | Adresse reply-to par défaut pour les envois d'emails |