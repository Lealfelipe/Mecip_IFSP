from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from mecip.models import Attachments, ReferenceAttachment


def _file_response(attachment_file):
    return FileResponse(
        attachment_file.open('rb'),
        as_attachment=False,
        filename=Path(attachment_file.name).name,
    )


@require_GET
def public_reference_attachment(request, public_id):
    attachment = get_object_or_404(
        ReferenceAttachment,
        public_id=public_id,
    )
    return _file_response(attachment.file)


@require_GET
def public_answer_attachment(request, public_id):
    attachment = get_object_or_404(
        Attachments,
        public_id=public_id,
        reference_attachment__isnull=True,
    )
    return _file_response(attachment.file)
