import django.db.models.deletion
from django.db import migrations, models


def link_reference_attachments(apps, schema_editor):
    Attachments = apps.get_model('mecip', 'Attachments')
    ReferenceAttachment = apps.get_model('mecip', 'ReferenceAttachment')

    references_by_file = {
        str(reference.file): reference.pk
        for reference in ReferenceAttachment.objects.exclude(file='')
    }

    for attachment in Attachments.objects.exclude(file='').iterator():
        reference_id = references_by_file.get(str(attachment.file))
        if reference_id:
            Attachments.objects.filter(pk=attachment.pk).update(
                reference_attachment_id=reference_id,
                file='',
            )


def restore_reference_files(apps, schema_editor):
    Attachments = apps.get_model('mecip', 'Attachments')

    attachments = Attachments.objects.exclude(
        reference_attachment=None
    ).select_related('reference_attachment')

    for attachment in attachments.iterator():
        Attachments.objects.filter(pk=attachment.pk).update(
            file=str(attachment.reference_attachment.file),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0030_report_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachments',
            name='reference_attachment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='answer_attachments',
                to='mecip.referenceattachment',
            ),
        ),
        migrations.AlterField(
            model_name='attachments',
            name='file',
            field=models.FileField(
                blank=True,
                upload_to='answer_attachments/',
            ),
        ),
        migrations.RunPython(
            link_reference_attachments,
            restore_reference_files,
        ),
        migrations.AddConstraint(
            model_name='attachments',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(reference_attachment__isnull=False)
                    | ~models.Q(file='')
                ),
                name='attachment_has_file_or_reference',
            ),
        ),
        migrations.AddConstraint(
            model_name='attachments',
            constraint=models.UniqueConstraint(
                fields=('answer', 'reference_attachment'),
                condition=models.Q(reference_attachment__isnull=False),
                name='unique_reference_attachment_per_answer',
            ),
        ),
    ]
