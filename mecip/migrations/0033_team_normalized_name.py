import unicodedata

from django.db import migrations, models


def normalize_team_name(value):
    decomposed_value = unicodedata.normalize('NFKD', value or '')
    return ''.join(
        character
        for character in decomposed_value
        if (
            not unicodedata.combining(character)
            and not character.isspace()
        )
    ).casefold()


def populate_normalized_team_names(apps, schema_editor):
    Team = apps.get_model('mecip', 'Team')
    teams = list(Team.objects.all())
    seen_teams = {}

    for team in teams:
        normalized_name = normalize_team_name(team.team_name)
        collision_key = (team.campus_id, normalized_name)
        existing_team_id = seen_teams.get(collision_key)

        if existing_team_id is not None:
            raise RuntimeError(
                'Colisão de equipes detectada no Campus '
                f'{team.campus_id}: IDs {existing_team_id} e {team.pk}.'
            )

        seen_teams[collision_key] = team.pk
        team.normalized_name = normalized_name

    Team.objects.bulk_update(
        teams,
        fields=('normalized_name',),
        batch_size=500,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0032_populate_missing_choice_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='normalized_name',
            field=models.CharField(
                editable=False,
                max_length=250,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_normalized_team_names,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='team',
            name='normalized_name',
            field=models.CharField(
                editable=False,
                max_length=250,
            ),
        ),
        migrations.AddConstraint(
            model_name='team',
            constraint=models.UniqueConstraint(
                fields=('campus', 'normalized_name'),
                name='unique_normalized_team_name_per_campus',
            ),
        ),
    ]
