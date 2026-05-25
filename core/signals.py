from dateutil.relativedelta import relativedelta

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='core.Adhesion')
def set_fin_adhesion(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.fin is not None:
        return
    duree = instance.organe.duree_mandat
    if duree > 0:
        sender.objects.filter(pk=instance.pk).update(fin=instance.debut + relativedelta(years=duree))


@receiver(post_save, sender='core.Reunion')
def creer_membres_reunion(sender, instance, created, **kwargs):
    if not created:
        return

    from core.models.adhesion import Adhesion
    from core.models.membre_reunion import MembreReunion

    STATUT_MAP = {
        Adhesion.Statut.MEMBRE_OFFICIEL: MembreReunion.Statut.MEMBRE_OFFICIEL,
        Adhesion.Statut.INVITE_PERMANENT: MembreReunion.Statut.INVITE,
    }

    adhesions = Adhesion.objects.filter(organe=instance.organe, active=True).select_related('membre')

    MembreReunion.objects.bulk_create([
        MembreReunion(
            reunion=instance,
            membre=adhesion.membre,
            statut=STATUT_MAP.get(adhesion.statut, MembreReunion.Statut.INVITE),
        )
        for adhesion in adhesions
    ])


@receiver(post_save, sender='core.Procuration')
def set_etat_procuration(sender, instance, **kwargs):
    from core.models.membre_reunion import MembreReunion

    MembreReunion.objects.filter(
        reunion=instance.reunion,
        membre=instance.mandant,
    ).update(etat=MembreReunion.Etat.PROCURATION)