import django.db.models.deletion
from django.db import migrations, models


def remap_vers_membrereunion(apps, schema_editor):
    """Convertit mandant/mandataire (Membre) en MembreReunion de la réunion."""
    Procuration = apps.get_model('core', 'Procuration')
    MembreReunion = apps.get_model('core', 'MembreReunion')
    for p in Procuration.objects.all():
        mr_mandant = MembreReunion.objects.filter(
            reunion_id=p.reunion_id, membre_id=p.mandant_id
        ).first()
        mr_mandataire = MembreReunion.objects.filter(
            reunion_id=p.reunion_id, membre_id=p.mandataire_id
        ).first()
        if mr_mandant is None or mr_mandataire is None:
            raise RuntimeError(
                f"Procuration {p.pk}: MembreReunion introuvable "
                f"(mandant={mr_mandant}, mandataire={mr_mandataire})"
            )
        p.mandant_mr_id = mr_mandant.pk
        p.mandataire_mr_id = mr_mandataire.pk
        p.save(update_fields=['mandant_mr', 'mandataire_mr'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_documentreunion_reunion'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='procuration',
            name='unique_procuration_mandant_reunion',
        ),
        migrations.AddField(
            model_name='procuration',
            name='mandant_mr',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='core.membrereunion',
            ),
        ),
        migrations.AddField(
            model_name='procuration',
            name='mandataire_mr',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='core.membrereunion',
            ),
        ),
        migrations.RunPython(remap_vers_membrereunion, migrations.RunPython.noop),
        migrations.RemoveField(model_name='procuration', name='mandant'),
        migrations.RemoveField(model_name='procuration', name='mandataire'),
        migrations.RenameField(
            model_name='procuration', old_name='mandant_mr', new_name='mandant'
        ),
        migrations.RenameField(
            model_name='procuration', old_name='mandataire_mr', new_name='mandataire'
        ),
        migrations.AlterField(
            model_name='procuration',
            name='mandant',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='procuration_donnee',
                to='core.membrereunion',
            ),
        ),
        migrations.AlterField(
            model_name='procuration',
            name='mandataire',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='procurations_recues',
                to='core.membrereunion',
            ),
        ),
    ]