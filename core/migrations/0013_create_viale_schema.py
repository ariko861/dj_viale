from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_documentreunion_reunion'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE SCHEMA IF NOT EXISTS viale_manager',
            reverse_sql='DROP SCHEMA IF EXISTS viale_manager CASCADE',
        ),
    ]
