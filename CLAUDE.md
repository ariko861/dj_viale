# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django application for managing an **ASBL (Association Sans But Lucratif — Belgian non-profit association)**. It handles members, organizational bodies (organes), meetings (réunions), attendance tracking, proxies (procurations), and document/email generation.

## Commands

This project uses `uv` for package management.

```bash
# Install dependencies
uv sync

# Run development server
uv run python manage.py runserver

# Database migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Run tests
uv run python manage.py test

# Django shell
uv run python manage.py shell
```

## Environment

Requires a `.env` file at the project root. Key variables:

```
SECRET_KEY=...
DEBUG=True
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
```

## Architecture

Single Django app: `core`, with a custom User model (`AUTH_USER_MODEL = 'core.User'`).

Admin UI uses **django-unfold** (replaces standard Django admin). Document generation uses **docxtpl** (Word templates). Calendar export uses **icalendar**.

### Core Data Model

```
Organe (committee)
  └─ Adhesion (membership) ──→ Membre (person) ──→ Adresse
  └─ Reunion (meeting) ──→ Adresse
       └─ MembreReunion (attendance record) ──→ Membre
            └─ Procuration (proxy) ──→ Membre (mandataire)
  └─ ModeleDocument (Word template) ──→ TagDocument
```

**Organe**: Organizational body (e.g., board, committee). Has a `duree_mandat` (mandate length in days).

**Adhesion**: Membership linking a `Membre` to an `Organe`. Status: `MEMBRE_OFFICIEL` or `INVITE_PERMANENT`. End date auto-set from `organe.duree_mandat` via signal.

**Reunion**: Meeting for an `Organe`. On creation, a signal (`creer_membres_reunion`) auto-creates `MembreReunion` records for all currently active `Adhesion` members.

**MembreReunion**: Junction table tracking each member's attendance state: `INVITE` (default) → `ACCEPTE` / `ABSENT` / `PROCURATION`.

**Procuration**: A proxy from `mandant` (absent member) to `mandataire` (proxy holder). Creating one auto-updates the mandant's `MembreReunion.etat` to `PROCURATION` via signal.

**ModeleDocument**: Word (`.docx`) template files associated with `Organe` objects, used to generate meeting documents via docxtpl context merging.

### Signals (in `core/signals.py`)

Three post-save signals with significant side effects:
1. `set_fin_adhesion` — sets `Adhesion.fin` based on `organe.duree_mandat`
2. `creer_membres_reunion` — creates `MembreReunion` rows when a `Reunion` is created
3. `set_etat_procuration` — updates mandant's attendance state when a `Procuration` is created

### Views (`core/views.py`)

- `GET /reunions/<pk>/ical/` — downloads `.ics` calendar file for a meeting
- `GET /reunions/<reunion_pk>/documents/<modele_pk>/` — generates and downloads a `.docx` from a Word template with meeting context
- `POST /admin/core/reunion/<pk>/email/` — custom admin action to send emails with optional document attachments to reunion members

### Media Files

Uploaded files (Word templates, procuration documents) are stored in the `media/` directory (excluded from git).