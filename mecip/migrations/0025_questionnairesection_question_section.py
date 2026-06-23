from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def create_default_sections(apps, schema_editor):
    Questionnaire = apps.get_model('mecip', 'Questionnaire')
    QuestionnaireSection = apps.get_model('mecip', 'QuestionnaireSection')
    Question = apps.get_model('mecip', 'Question')

    for questionnaire in Questionnaire.objects.all():
        section, _ = QuestionnaireSection.objects.get_or_create(
            questionnaire=questionnaire,
            name='Geral',
            defaults={
                'order': 0,
                'created_date': django.utils.timezone.now(),
            },
        )
        Question.objects.filter(questionnaire=questionnaire, section__isnull=True).update(section=section)


def restore_questionnaire_field(apps, schema_editor):
    Question = apps.get_model('mecip', 'Question')

    for question in Question.objects.select_related('section'):
        if question.section_id:
            question.questionnaire_id = question.section.questionnaire_id
            question.save(update_fields=['questionnaire'])


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0024_reportquestionanswer_free_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='mecip.questionnaire')),
                ('teams', models.ManyToManyField(blank=True, related_name='questionnaire_sections', to='mecip.team')),
            ],
            options={
                'ordering': ['questionnaire', 'order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='question',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='mecip.questionnairesection'),
        ),
        migrations.RunPython(create_default_sections, restore_questionnaire_field),
        migrations.AlterField(
            model_name='question',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='mecip.questionnairesection'),
        ),
        migrations.RemoveField(
            model_name='question',
            name='questionnaire',
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['section__questionnaire', 'section__order', 'order']},
        ),
    ]
