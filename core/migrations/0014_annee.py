from django.db import migrations, models


def remplir_annees(apps, schema_editor):
    Reunion = apps.get_model('core', 'Reunion')
    DocumentReunion = apps.get_model('core', 'DocumentReunion')
    for reunion in Reunion.objects.all():
        reunion.annee = reunion.debut.year
        reunion.save(update_fields=['annee'])
        DocumentReunion.objects.filter(reunion=reunion).update(annee=reunion.annee)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_procuration_vers_membrereunion'),
    ]

    operations = [
        migrations.AddField(
            model_name='reunion',
            name='annee',
            field=models.PositiveSmallIntegerField(null=True, blank=True, db_index=True, verbose_name='année'),
        ),
        migrations.AddField(
            model_name='documentreunion',
            name='annee',
            field=models.PositiveSmallIntegerField(
                blank=True, db_index=True, null=True, verbose_name='année',
                help_text='Reprise automatiquement de la réunion si le document y est lié.',
            ),
        ),
        migrations.RunPython(remplir_annees, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='reunion',
            name='annee',
            field=models.PositiveSmallIntegerField(
                blank=True, db_index=True, verbose_name='année',
                help_text="Laisser vide pour utiliser l'année de début de la réunion.",
            ),
        ),
    ]
