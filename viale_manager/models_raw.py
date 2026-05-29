# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AssignationsMaisonnees(models.Model):
    id = models.BigAutoField(primary_key=True)
    sejour_id = models.BigIntegerField()
    house_id = models.BigIntegerField()
    planning_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'assignations_maisonnees'


class AutoMails(models.Model):
    id = models.BigAutoField(primary_key=True)
    sujet = models.CharField(max_length=255)
    body = models.TextField()
    type = models.CharField(max_length=255)
    time_delta = models.IntegerField(blank=True, null=True, db_comment="donne le nombre de jour de différence avec l'évènement visé")
    actif = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auto_mails'



class Houses(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    community = models.BooleanField()
    displayhousenamewithroom = models.BooleanField(db_column='displayHouseNameWithRoom')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'houses'


class HousesInMaisonneesPlanning(models.Model):
    house_id = models.BigIntegerField()
    planning_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'houses_in_maisonnees_planning'


class Jobs(models.Model):
    id = models.BigAutoField(primary_key=True)
    queue = models.CharField(max_length=255)
    payload = models.TextField()
    attempts = models.SmallIntegerField()
    reserved_at = models.IntegerField(blank=True, null=True)
    available_at = models.IntegerField()
    created_at = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'jobs'


class MaisonneesPlanning(models.Model):
    id = models.BigAutoField(primary_key=True)
    begin = models.DateField()
    end = models.DateField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maisonnees_planning'


class Messages(models.Model):
    id = models.BigAutoField(primary_key=True)
    message = models.TextField()
    type = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'messages'


class Migrations(models.Model):
    migration = models.CharField(max_length=255)
    batch = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'migrations'


class ModelHasPermissions(models.Model):
    pk = models.CompositePrimaryKey('permission_id', 'model_id', 'model_type')
    permission = models.ForeignKey('Permissions', models.DO_NOTHING)
    model_type = models.CharField(max_length=255)
    model_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_permissions'


class ModelHasRoles(models.Model):
    pk = models.CompositePrimaryKey('role_id', 'model_id', 'model_type')
    role = models.ForeignKey('Roles', models.DO_NOTHING)
    model_type = models.CharField(max_length=255)
    model_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_roles'


class Options(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'options'


class PasswordResetTokens(models.Model):
    email = models.CharField(primary_key=True, max_length=255)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'password_reset_tokens'


class Permissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    guard_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'permissions'
        unique_together = (('name', 'guard_name'),)


class PersonalAccessTokens(models.Model):
    id = models.BigAutoField(primary_key=True)
    tokenable_type = models.CharField(max_length=255)
    tokenable_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    token = models.CharField(unique=True, max_length=64)
    abilities = models.TextField(blank=True, null=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'personal_access_tokens'


class Profiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    is_default = models.BooleanField()
    remarques = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profiles'


class Reservations(models.Model):
    id = models.BigAutoField(primary_key=True)
    authorize_edition = models.BooleanField()
    link_token = models.UUIDField(unique=True)
    max_days_change = models.IntegerField()
    max_visitors = models.IntegerField()
    remarques_visiteur = models.TextField(blank=True, null=True)
    remarques_accueil = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    link_sent = models.BooleanField()
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=255, blank=True, null=True)
    all_mails_required = models.BooleanField()
    groupe = models.BooleanField(db_comment='Est-ce une réservation pour un groupe, active formulaire simplifié')
    nom_groupe = models.CharField(max_length=255, blank=True, null=True, db_comment='Nom du groupe')

    class Meta:
        managed = False
        db_table = 'reservations'


class RoleHasPermissions(models.Model):
    pk = models.CompositePrimaryKey('permission_id', 'role_id')
    permission = models.ForeignKey(Permissions, models.DO_NOTHING)
    role = models.ForeignKey('Roles', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'role_has_permissions'


class Roles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    guard_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'
        unique_together = (('name', 'guard_name'),)


class Rooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    house = models.ForeignKey(Houses, models.DO_NOTHING, blank=True, null=True)
    beds = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rooms'


class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(unique=True, max_length=255)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    password = models.CharField(max_length=255)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    visitor_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


