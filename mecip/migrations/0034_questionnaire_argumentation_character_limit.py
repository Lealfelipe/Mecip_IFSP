from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0033_team_normalized_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='argumentation_character_limit',
            field=models.PositiveIntegerField(
                default=2000,
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(100000),
                ],
            ),
        ),
    ]
