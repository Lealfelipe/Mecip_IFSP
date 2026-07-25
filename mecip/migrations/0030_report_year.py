from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def populate_report_year(apps, schema_editor):
    Report = apps.get_model('mecip', 'Report')

    for report in Report.objects.only('id', 'created_date').iterator():
        report.year = report.created_date.year
        report.save(update_fields=['year'])


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0029_question_special_condition'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='year',
            field=models.PositiveSmallIntegerField(
                null=True,
                verbose_name='Ano',
                validators=[
                    MinValueValidator(1900),
                    MaxValueValidator(9999),
                ],
            ),
        ),
        migrations.RunPython(
            populate_report_year,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='report',
            name='year',
            field=models.PositiveSmallIntegerField(
                verbose_name='Ano',
                validators=[
                    MinValueValidator(1900),
                    MaxValueValidator(9999),
                ],
            ),
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together={('course', 'campus', 'year')},
        ),
    ]
