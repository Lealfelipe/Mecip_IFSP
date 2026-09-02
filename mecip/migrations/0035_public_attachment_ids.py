import uuid

from django.db import migrations, models


def populate_public_ids(apps, schema_editor):
    for model_name in ('ReferenceAttachment', 'Attachments'):
        model = apps.get_model('mecip', model_name)
        for attachment in model.objects.filter(public_id__isnull=True).iterator():
            attachment.public_id = uuid.uuid4()
            attachment.save(update_fields=('public_id',))


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0034_questionnaire_argumentation_character_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='referenceattachment',
            name='public_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='attachments',
            name='public_id',
            field=models.UUIDField(null=True),
        ),
        migrations.RunPython(
            populate_public_ids,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='referenceattachment',
            name='public_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='attachments',
            name='public_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
