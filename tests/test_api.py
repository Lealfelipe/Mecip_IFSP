import pytest
from rest_framework import status

from mecip.models import Question, QuestionAnswerOption
from mecip.models import ReportQuestionAnswer
from tests.factories import TeamUserFactory


pytestmark = [pytest.mark.django_db, pytest.mark.api]


def test_login_com_credenciais_validas_retorna_token(api_client):
    TeamUserFactory(username="equipe", password="senha123")

    response = api_client.post(
        "/api/v1/auth/login/",
        {
            "username": "equipe",
            "password": "senha123",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.data


def test_login_com_credenciais_invalidas_retorna_400(api_client):
    TeamUserFactory(username="equipe", password="senha123")

    response = api_client.post(
        "/api/v1/auth/login/",
        {
            "username": "equipe",
            "password": "senha-incorreta",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_equipe_responde_questionario_atribuido_e_persiste_resposta(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    text_question,
):
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta da equipe",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
        answer="Resposta da equipe",
    ).exists()


def test_coordenador_importa_questionario_com_secao_e_alternativas(
    authenticate_api_client,
    coordinator,
    valid_questionnaire_payload,
):
    client = authenticate_api_client(coordinator)

    response = client.post(
        "/api/v1/questionarios/importar/",
        valid_questionnaire_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    question = Question.objects.get(pk=response.data["question_id"])
    first_concept = valid_questionnaire_payload["conceitos"][0]

    assert question.indicator == "Indicador 1.1"
    assert question.field_type == "choice"
    assert question.required
    assert question.answer_options.count() == 2
    assert QuestionAnswerOption.objects.filter(
        question=question,
        answer_value=first_concept["conceito"],
        acceptance_criteria=first_concept["criterio_de_aceite"],
    ).exists()


def test_importacao_rejeita_choice_sem_alternativas(
    authenticate_api_client,
    coordinator,
    valid_questionnaire_payload,
):
    client = authenticate_api_client(coordinator)
    payload = {
        **valid_questionnaire_payload,
        "questionario": "Questionário sem alternativas",
        "questao": "Choice inválida",
        "conceitos": [],
    }

    response = client.post(
        "/api/v1/questionarios/importar/",
        payload,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Question.objects.filter(text="Choice inválida").exists()
