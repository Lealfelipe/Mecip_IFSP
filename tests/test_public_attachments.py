import uuid

import pytest
from django.urls import reverse

from tests.factories import (
    CataloguedAttachmentFactory,
    DirectAttachmentFactory,
    ReferenceAttachmentFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def response_body(response):
    return b''.join(response.streaming_content)


@pytest.mark.parametrize(
    ('attachment_factory', 'prefix'),
    (
        (ReferenceAttachmentFactory, '/a/r/'),
        (DirectAttachmentFactory, '/a/d/'),
    ),
)
def test_link_publico_gerado_e_curto(
    attachment_factory,
    prefix,
):
    attachment = attachment_factory()

    assert attachment.public_path.startswith(prefix)
    assert len(attachment.public_path) == len(prefix) + 23
    assert str(attachment.public_id) not in attachment.public_path


def test_anexo_de_referencia_e_publico_sem_autenticacao(client):
    attachment = ReferenceAttachmentFactory()

    response = client.get(
        reverse(
            'mecip:public_reference_attachment',
            args=(attachment.public_id,),
        )
    )

    assert response.status_code == 200
    assert response_body(response) == b'conteudo de arquivo para teste'


def test_upload_direto_e_publico_sem_autenticacao(client):
    attachment = DirectAttachmentFactory()

    response = client.get(
        reverse(
            'mecip:public_answer_attachment',
            args=(attachment.public_id,),
        )
    )

    assert response.status_code == 200
    assert response_body(response) == b'conteudo de arquivo para teste'


@pytest.mark.parametrize(
    ('route_name', 'attachment_factory'),
    (
        (
            'mecip:legacy_public_reference_attachment',
            ReferenceAttachmentFactory,
        ),
        (
            'mecip:legacy_public_answer_attachment',
            DirectAttachmentFactory,
        ),
    ),
)
def test_link_publico_legado_continua_funcionando(
    client,
    route_name,
    attachment_factory,
):
    attachment = attachment_factory()

    response = client.get(
        reverse(route_name, args=(attachment.public_id,))
    )

    assert response.status_code == 200
    assert response_body(response) == (
        b'conteudo de arquivo para teste'
    )


def test_anexo_catalogado_usa_o_mesmo_link_da_referencia():
    attachment = CataloguedAttachmentFactory()

    assert attachment.public_path == (
        attachment.reference_attachment.public_path
    )


@pytest.mark.parametrize(
    'route_name',
    (
        'mecip:public_reference_attachment',
        'mecip:public_answer_attachment',
    ),
)
def test_uuid_publico_inexistente_retorna_404_sem_login(
    client,
    route_name,
):
    response = client.get(reverse(route_name, args=(uuid.uuid4(),)))

    assert response.status_code == 404


def test_rota_de_resposta_nao_expoe_anexo_catalogado(client):
    attachment = CataloguedAttachmentFactory()

    response = client.get(
        reverse(
            'mecip:public_answer_attachment',
            args=(attachment.public_id,),
        )
    )

    assert response.status_code == 404
