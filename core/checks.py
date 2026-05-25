from datetime import date

from django.contrib import messages


def dashboard_callback(request, context):
    from core.models import Adhesion, Membre

    adhesions_expirees = Adhesion.objects.filter(
        active=True,
        statut=Adhesion.Statut.MEMBRE_OFFICIEL,
        fin__lt=date.today(),
    ).select_related('membre', 'organe')

    for adhesion in adhesions_expirees:
        messages.warning(
            request,
            f"Mandat expiré : {adhesion.membre} dans {adhesion.organe} "
            f"(fin le {adhesion.fin.strftime('%d/%m/%Y')}).",
        )

    membres_sans_adresse = Membre.objects.filter(
        adhesion__active=True,
        adhesion__statut=Adhesion.Statut.MEMBRE_OFFICIEL,
        adresse__isnull=True,
    ).distinct()

    for membre in membres_sans_adresse:
        messages.warning(request, f"Membre sans adresse : {membre}.")

    return context