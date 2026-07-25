from django.db import migrations


def create_user_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    equipe_group, _ = Group.objects.get_or_create(name='Equipe')
    Group.objects.get_or_create(name='Coordenador')
    superadmin_group, _ = Group.objects.get_or_create(name='SuperAdmin')

    for user in User.objects.all():
        if user.is_superuser:
            user.groups.add(superadmin_group)
        elif not user.groups.filter(name__in=['Equipe', 'Coordenador', 'SuperAdmin']).exists():
            user.groups.add(equipe_group)


def remove_user_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Equipe', 'Coordenador', 'SuperAdmin']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('mecip', '0025_questionnairesection_question_section'),
    ]

    operations = [
        migrations.RunPython(create_user_roles, remove_user_roles),
    ]
