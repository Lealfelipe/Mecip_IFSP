import pytest
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.urls import reverse

from mecip.models import (
    Campus,
    Course,
    Question,
    Questionnaire,
    QuestionnaireSection,
    ReferenceAttachment,
    Team,
    Type_Course,
)
from mecip.permissions import ROLE_EQUIPE
from tests.factories import (
    CataloguedAttachmentFactory,
    CourseCategoryFactory,
    CourseFactory,
    QuestionAnswerOptionFactory,
    ReferenceAttachmentFactory,
    TeamFactory,
    UserFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def response_messages(response):
    return [
        str(message)
        for message in get_messages(response.wsgi_request)
    ]


def campus_payload(**overrides):
    payload = {
        "campus_name": "Campus Web",
        "city": "Cidade Web",
        "street": "Rua Web",
        "neighborhood": "Centro",
        "number": "100",
        "contact_number": "11999999999",
        "email_campus": "campus-web@example.com",
    }
    payload.update(overrides)
    return payload


def question_payload(section, **overrides):
    payload = {
        "section": section.id,
        "indicator": "Indicador Web",
        "special_condition": "",
        "text": "Pergunta criada pela view",
        "field_type": "text",
        "required": "on",
        "order": "1",
        "choices": "",
        "answer_options-TOTAL_FORMS": "1",
        "answer_options-INITIAL_FORMS": "0",
        "answer_options-MIN_NUM_FORMS": "0",
        "answer_options-MAX_NUM_FORMS": "1000",
        "answer_options-0-id": "",
        "answer_options-0-answer_value": "",
        "answer_options-0-acceptance_criteria": "",
    }
    payload.update(overrides)
    return payload


def test_coordenador_cria_edita_e_valida_campus(
    client,
    coordinator,
):
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create"),
        campus_payload(),
    )

    campus = Campus.objects.get(campus_name="Campus Web")
    assert response.status_code == 302
    assert response.url == reverse("mecip:update", args=(campus.id,))
    assert "Campus inserido com sucesso!" in response_messages(response)

    response = client.post(
        reverse("mecip:update", args=(campus.id,)),
        campus_payload(city="Cidade Atualizada"),
    )
    campus.refresh_from_db()

    assert response.status_code == 302
    assert campus.city == "Cidade Atualizada"
    assert "Campus alterado com sucesso!" in response_messages(response)

    response = client.post(reverse("mecip:create"), {})

    assert response.status_code == 200
    assert response.context["form"].errors
    assert "Erro ao inserir Campus" in response_messages(response)


def test_coordenador_cria_e_edita_tipo_e_curso(
    client,
    coordinator,
    campus,
):
    category = CourseCategoryFactory()
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create_type"),
        {
            "type_name_course": "Tipo Web",
            "duration": "4",
            "type_categorie": category.id,
        },
    )
    course_type = Type_Course.objects.get(type_name_course="Tipo Web")

    assert response.status_code == 302
    assert "Curso cadastrado com sucesso" in response_messages(response)

    response = client.post(
        reverse("mecip:update_type", args=(course_type.id,)),
        {
            "type_name_course": "Tipo Web Atualizado",
            "duration": "5",
            "type_categorie": category.id,
        },
    )
    course_type.refresh_from_db()

    assert response.status_code == 302
    assert course_type.duration == "5"

    response = client.post(
        reverse("mecip:create_course"),
        {
            "type_course": course_type.id,
            "description": "Curso criado pela view",
            "campus": campus.id,
        },
    )
    course = Course.objects.get(
        type_course=course_type,
        campus=campus,
    )

    assert response.status_code == 302
    assert "Curso cadastrado com sucesso" in response_messages(response)

    response = client.post(
        reverse("mecip:update_course", args=(course.id,)),
        {
            "type_course": course_type.id,
            "description": "Curso atualizado pela view",
            "campus": campus.id,
        },
    )
    course.refresh_from_db()

    assert response.status_code == 302
    assert course.description == "Curso atualizado pela view"


def test_coordenador_cria_edita_e_gerencia_usuarios_da_equipe(
    client,
    coordinator,
    campus,
):
    user = UserFactory()
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create_team"),
        {"team_name": "Equipe Web", "campus": campus.id},
    )
    team = Team.objects.get(team_name="Equipe Web")

    assert response.status_code == 302
    assert "Equipe inserida com sucesso!" in response_messages(response)

    response = client.post(
        reverse("mecip:update_team", args=(team.id,)),
        {"team_name": "Equipe Web Atualizada", "campus": campus.id},
    )
    team.refresh_from_db()

    assert response.status_code == 302
    assert team.team_name == "Equipe Web Atualizada"

    response = client.post(
        reverse("mecip:add_user_to_team", args=(team.id,)),
        {"user_ids": [str(user.id), "999999"]},
    )

    assert response.status_code == 302
    assert team.users.filter(pk=user.pk).exists()
    assert any(
        "adicionado" in message
        for message in response_messages(response)
    )

    response = client.post(
        reverse(
            "mecip:remove_user_from_team",
            args=(team.id, user.id),
        )
    )

    assert response.status_code == 302
    assert not team.users.filter(pk=user.pk).exists()
    assert any(
        "removido" in message
        for message in response_messages(response)
    )


def test_superadmin_cria_usuario_com_papel_equipe(
    client,
    superadmin,
):
    client.force_login(superadmin)

    response = client.post(
        reverse("mecip:register"),
        {
            "first_name": "Usuario",
            "last_name": "Web",
            "email": "usuario-web@example.com",
            "username": "usuario-web",
            "password1": "SenhaForte123!",
            "password2": "SenhaForte123!",
        },
    )

    user = User.objects.get(username="usuario-web")
    assert response.status_code == 302
    assert response.url == reverse("mecip:register")
    assert user.groups.filter(name=ROLE_EQUIPE).exists()
    assert any(
        "criado com sucesso" in message
        for message in response_messages(response)
    )


def test_coordenador_cria_e_edita_questionario_secao_e_pergunta(
    client,
    coordinator,
    campus,
    team,
):
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create_questionnaire"),
        {
            "name": "Questionario Web",
            "description": "Criado pela view",
            "campus": campus.id,
            "active": "on",
        },
    )
    questionnaire = Questionnaire.objects.get(name="Questionario Web")

    assert response.status_code == 302
    assert "Questionario cadastrado com sucesso" in response_messages(
        response
    )

    response = client.post(
        reverse(
            "mecip:update_questionnaire",
            args=(questionnaire.id,),
        ),
        {
            "name": "Questionario Web Atualizado",
            "description": "Atualizado pela view",
            "campus": campus.id,
            "active": "on",
        },
    )
    questionnaire.refresh_from_db()

    assert response.status_code == 302
    assert questionnaire.name == "Questionario Web Atualizado"

    response = client.post(
        reverse(
            "mecip:create_questionnaire_section",
            args=(questionnaire.id,),
        ),
        {
            "name": "Secao Web",
            "teams": [team.id],
            "order": "1",
        },
    )
    section = QuestionnaireSection.objects.get(
        questionnaire=questionnaire,
        name="Secao Web",
    )

    assert response.status_code == 302
    assert list(section.teams.all()) == [team]

    response = client.post(
        reverse(
            "mecip:update_questionnaire_section",
            args=(questionnaire.id, section.id),
        ),
        {
            "name": "Secao Web Atualizada",
            "teams": [team.id],
            "order": "2",
        },
    )
    section.refresh_from_db()

    assert response.status_code == 302
    assert section.order == 2

    response = client.post(
        reverse(
            "mecip:create_question",
            args=(questionnaire.id,),
        ),
        question_payload(section),
    )
    question = Question.objects.get(
        section=section,
        text="Pergunta criada pela view",
    )

    assert response.status_code == 302
    assert "Questao cadastrada com sucesso" in response_messages(response)

    response = client.post(
        reverse(
            "mecip:update_question",
            args=(questionnaire.id, question.id),
        ),
        question_payload(
            section,
            text="Pergunta atualizada pela view",
        ),
    )
    question.refresh_from_db()

    assert response.status_code == 302
    assert question.text == "Pergunta atualizada pela view"


def test_get_exclui_pergunta_e_documenta_risco_de_csrf(
    client,
    coordinator,
    questionnaire,
    text_question,
):
    client.force_login(coordinator)

    response = client.get(
        reverse(
            "mecip:delete_question",
            args=(questionnaire.id, text_question.id),
        )
    )

    assert response.status_code == 302
    assert not Question.objects.filter(pk=text_question.pk).exists()


def test_get_exclui_secao_e_documenta_risco_de_csrf(
    client,
    coordinator,
    questionnaire,
    section,
):
    client.force_login(coordinator)

    response = client.get(
        reverse(
            "mecip:delete_questionnaire_section",
            args=(questionnaire.id, section.id),
        )
    )

    assert response.status_code == 302
    assert not QuestionnaireSection.objects.filter(pk=section.pk).exists()


def test_coordenador_cria_edita_e_exclui_anexo_de_referencia(
    client,
    coordinator,
    valid_upload,
):
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create_reference_attachment"),
        {
            "name": "Anexo Web",
            "file": valid_upload,
            "description": "Criado pela view",
            "active": "on",
        },
    )
    attachment = ReferenceAttachment.objects.get(name="Anexo Web")

    assert response.status_code == 302
    assert any(
        "cadastrado com sucesso" in message
        for message in response_messages(response)
    )

    response = client.post(
        reverse(
            "mecip:update_reference_attachment",
            args=(attachment.id,),
        ),
        {
            "name": "Anexo Web Atualizado",
            "description": "Atualizado pela view",
            "active": "on",
        },
    )
    attachment.refresh_from_db()

    assert response.status_code == 302
    assert attachment.name == "Anexo Web Atualizado"

    response = client.get(
        reverse(
            "mecip:delete_reference_attachment",
            args=(attachment.id,),
        )
    )
    assert response.status_code == 302
    assert ReferenceAttachment.objects.filter(pk=attachment.pk).exists()

    response = client.post(
        reverse(
            "mecip:delete_reference_attachment",
            args=(attachment.id,),
        )
    )

    assert response.status_code == 302
    assert not ReferenceAttachment.objects.filter(pk=attachment.pk).exists()


def test_anexo_catalogado_em_uso_nao_pode_ser_excluido(
    client,
    coordinator,
):
    attachment = ReferenceAttachmentFactory()
    CataloguedAttachmentFactory(reference_attachment=attachment)
    client.force_login(coordinator)

    response = client.post(
        reverse(
            "mecip:delete_reference_attachment",
            args=(attachment.id,),
        )
    )

    assert response.status_code == 302
    assert ReferenceAttachment.objects.filter(pk=attachment.pk).exists()
    assert any(
        "nao pode ser excluido" in message
        for message in response_messages(response)
    )
