import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from docxtpl import DocxTemplate
from icalendar import Calendar, Event

from core.models import ModeleDocument, Reunion


def reunion_ical(request, pk):
    reunion = get_object_or_404(Reunion.objects.select_related('organe', 'adresse'), pk=pk)

    cal = Calendar()
    cal.add('prodid', '-//dj-asbl//FR')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', str(reunion))
    event.add('dtstart', reunion.debut)
    event.add('dtend', reunion.fin or reunion.debut)
    event.add('uid', f'reunion-{reunion.pk}@dj-asbl')

    if reunion.adresse:
        location = f"{reunion.adresse.adresse}, {reunion.adresse.code_postal} {reunion.adresse.ville}"
        event.add('location', location)

    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reunion-{reunion.pk}.ics"'
    return response


def reunion_document(request, reunion_pk, modele_pk):
    reunion = get_object_or_404(
        Reunion.objects.select_related('organe', 'adresse'),
        pk=reunion_pk,
    )
    modele = get_object_or_404(
        ModeleDocument.objects.filter(organes=reunion.organe),
        pk=modele_pk,
    )

    membres = (
        reunion.membrereunion_set
        .select_related('membre')
        .order_by('membre__nom', 'membre__prenom')
    )

    context = {
        'reunion': reunion,
        'organe': reunion.organe,
        'adresse': reunion.adresse,
        'membres': list(membres),
        'date': reunion.debut.strftime('%d/%m/%Y'),
        'heure': reunion.debut.strftime('%H:%M'),
    }

    tpl = DocxTemplate(modele.fichier.path)
    tpl.render(context)

    buffer = io.BytesIO()
    tpl.save(buffer)
    buffer.seek(0)

    nom_fichier = f"{modele.nom} - {reunion.debut.strftime('%Y-%m-%d')}.docx"
    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response