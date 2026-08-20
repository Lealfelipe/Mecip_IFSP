import pytest
from django.db import IntegrityError, transaction

from mecip.models import Attachments


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_anexo_catalogado_armazena_referencia_sem_upload_direto(
    answer,
    reference_attachment,
):
    attachment = Attachments.objects.create(
        answer=answer,
        reference_attachment=reference_attachment,
        name=reference_attachment.name,
    )

    assert not attachment.file
    assert attachment.reference_attachment == reference_attachment
    assert (
        attachment.attachment_file.name
        == reference_attachment.file.name
    )
    assert attachment.file_url == reference_attachment.file.url


def test_upload_direto_resolve_arquivo_sem_anexo_catalogado(answer):
    attachment = Attachments.objects.create(
        answer=answer,
        name="Upload direto",
        file="answer_attachments/upload.pdf",
    )

    assert attachment.reference_attachment is None
    assert attachment.attachment_file.name == (
        "answer_attachments/upload.pdf"
    )
    assert attachment.file_url == (
        "/media/answer_attachments/upload.pdf"
    )


def test_anexo_sem_arquivo_ou_referencia_viola_restricao(answer):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Attachments.objects.create(
                answer=answer,
                name="Anexo sem origem",
            )


def test_mesma_referencia_nao_pode_ser_repetida_na_resposta(
    answer,
    reference_attachment,
):
    Attachments.objects.create(
        answer=answer,
        reference_attachment=reference_attachment,
        name="Primeiro vinculo",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Attachments.objects.create(
                answer=answer,
                reference_attachment=reference_attachment,
                name="Vinculo duplicado",
            )
