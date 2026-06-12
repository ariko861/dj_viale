import os

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils._os import safe_join
from icalendar import Calendar, Event

from core.docx import generer_document
from core.models import DocumentReunion, ModeleDocument, Reunion


def document_reunion(request, token):
    doc = get_object_or_404(DocumentReunion, token=token)
    if not doc.public and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not doc.fichier:
        raise Http404
    as_attachment = 'dl' in request.GET
    return FileResponse(
        doc.fichier.open('rb'),
        as_attachment=as_attachment,
        filename=doc.fichier.name.split('/')[-1],
    )


def media_protege(request, path):
    """Sert un fichier de MEDIA_ROOT aux seuls utilisateurs ayant accès à l'admin.

    Branché sur MEDIA_URL, ce qui fait fonctionner le lien de téléchargement natif
    des widgets FileField partout dans l'admin.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect_to_login(request.get_full_path())
    try:
        full_path = safe_join(str(settings.MEDIA_ROOT), path)
    except (ValueError, SuspiciousFileOperation):
        raise Http404
    if not os.path.isfile(full_path):
        raise Http404
    as_attachment = 'dl' in request.GET
    return FileResponse(open(full_path, 'rb'), as_attachment=as_attachment)


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

    nom_fichier = f"{modele.nom} - {reunion.debut.strftime('%Y-%m-%d')}.docx"
    response = HttpResponse(
        generer_document(reunion, modele),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response