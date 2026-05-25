import io
from datetime import date

from constance import config
from django.utils.dateformat import format as django_date_format
from docxtpl import DocxTemplate
from jinja2 import Environment


def make_jinja_env():
    env = Environment()
    env.filters['date'] = lambda value, fmt='': django_date_format(value, fmt) if value else ''
    return env


def build_reunion_context(reunion):
    from core.models import Membre
    membres = (
        reunion.membrereunion_set
        .select_related('membre')
        .order_by('membre__nom', 'membre__prenom')
    )
    secretaire = Membre.objects.filter(pk=config.SECRETAIRE_ID).first() if config.SECRETAIRE_ID else None
    president = Membre.objects.filter(pk=config.PRESIDENT_ID).first() if config.PRESIDENT_ID else None
    return {
        'reunion': reunion,
        'organe': reunion.organe,
        'adresse': reunion.adresse,
        'membres': list(membres),
        'date': reunion.debut.strftime('%d/%m/%Y'),
        'heure': reunion.debut.strftime('%H:%M'),
        'debut': reunion.debut,
        'fin': reunion.fin,
        'secretaire': secretaire,
        'president': president,
        'today': date.today(),
    }


def generer_document(reunion, modele):
    context = build_reunion_context(reunion)
    tpl = DocxTemplate(modele.fichier.path)
    tpl.render(context, jinja_env=make_jinja_env())
    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)
    return buf.read()