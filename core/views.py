import os
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils._os import safe_join
from icalendar import Calendar, Event

from core.docx import generer_document
from core.models import DocumentReunion, ModeleDocument, Reunion

# Permission requise pour servir un fichier, selon son dossier dans MEDIA_ROOT.
# Un dossier absent de la liste n'est servi qu'aux superusers.
PERMISSIONS_MEDIA = {
    'documents/reunions/': 'core.view_documentreunion',
    'modeles_documents/': 'core.view_modeledocument',
    'procurations/': 'core.view_procuration',
}


def permission_requise(perm):
    """Connexion demandée aux anonymes, 403 pour les connectés sans ``perm``."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.has_perm(perm):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def document_reunion(request, token):
    doc = get_object_or_404(DocumentReunion, token=token)
    if not doc.public:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        # Les comptes visiteurs Viale sont aussi des utilisateurs connectés.
        if not request.user.is_staff:
            raise PermissionDenied
    if not doc.fichier:
        raise Http404
    as_attachment = 'dl' in request.GET
    return FileResponse(
        doc.fichier.open('rb'),
        as_attachment=as_attachment,
        filename=doc.fichier.name.split('/')[-1],
    )


def media_protege(request, path):
    """Sert un fichier de MEDIA_ROOT aux utilisateurs de l'admin qui ont le droit de le voir.

    Branché sur MEDIA_URL, ce qui fait fonctionner le lien de téléchargement natif
    des widgets FileField partout dans l'admin. La permission dépend du dossier
    du fichier (cf. ``PERMISSIONS_MEDIA``).
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect_to_login(request.get_full_path())
    try:
        full_path = safe_join(str(settings.MEDIA_ROOT), path)
    except (ValueError, SuspiciousFileOperation):
        raise Http404
    if not os.path.isfile(full_path):
        raise Http404
    relatif = os.path.relpath(full_path, settings.MEDIA_ROOT).replace(os.sep, '/')
    perm = next((p for dossier, p in PERMISSIONS_MEDIA.items() if relatif.startswith(dossier)), None)
    if not (request.user.is_superuser or (perm and request.user.has_perm(perm))):
        raise PermissionDenied
    as_attachment = 'dl' in request.GET
    return FileResponse(open(full_path, 'rb'), as_attachment=as_attachment)


@permission_requise('core.view_reunion')
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


@permission_requise('core.view_reunion')
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