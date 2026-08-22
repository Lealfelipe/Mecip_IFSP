from django.db import migrations


def populate_missing_choice_options(apps, schema_editor):
    Question = apps.get_model('mecip', 'Question')
    QuestionAnswerOption = apps.get_model(
        'mecip',
        'QuestionAnswerOption',
    )

    questions_without_options = Question.objects.filter(
        field_type='choice',
        answer_options__isnull=True,
    ).only('pk')

    QuestionAnswerOption.objects.bulk_create([
        QuestionAnswerOption(
            question_id=question.pk,
            answer_value='Alternativa pendente de revisão',
            acceptance_criteria='',
        )
        for question in questions_without_options
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0031_attachments_reference_attachment'),
    ]

    operations = [
        migrations.RunPython(
            populate_missing_choice_options,
            migrations.RunPython.noop,
        ),
    ]
