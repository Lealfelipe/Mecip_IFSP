import pytest
from rest_framework import status

from mecip.models import Campus, Course, Questionnaire, Report
from mecip.models import ReportQuestionAnswer
from tests.factories import (
    CampusFactory,
    CoordinatorFactory,
    CourseFactory,
    CourseTypeFactory,
    MultipleChoiceQuestionFactory,
    QuestionAnswerOptionFactory,
    QuestionnaireFactory,
    ReportFactory,
    SuperAdminFactory,
    TeamFactory,
    TeamUserFactory,
    TextQuestionFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.api]

RESOURCE_NAMES = ("campus", "cursos", "relatorios", "questionarios")

RESOURCE_FACTORIES = {
    "campus": CampusFactory,
    "cursos": CourseFactory,
    "relatorios": ReportFactory,
    "questionarios": QuestionnaireFactory,
}

READ_ROLE_CASES = (
    pytest.param(TeamUserFactory, status.HTTP_200_OK, id="equipe"),
    pytest.param(CoordinatorFactory, status.HTTP_200_OK, id="coordenador"),
    pytest.param(SuperAdminFactory, status.HTTP_200_OK, id="superadmin"),
    pytest.param(None, status.HTTP_401_UNAUTHORIZED, id="anonimo"),
)

WRITE_ROLE_CASES = (
    pytest.param(
        TeamUserFactory,
        status.HTTP_403_FORBIDDEN,
        id="equipe",
    ),
    pytest.param(
        CoordinatorFactory,
        status.HTTP_201_CREATED,
        id="coordenador",
    ),
    pytest.param(
        SuperAdminFactory,
        status.HTTP_201_CREATED,
        id="superadmin",
    ),
)


def campus_payload(name="Campus API", **overrides):
    payload = {
        "campus_name": name,
        "city": "Cidade API",
        "street": "Rua API",
        "neighborhood": "Bairro API",
        "number": "100",
        "contact_number": "11999999999",
        "email_campus": "campus-api@example.com",
    }
    payload.update(overrides)
    return payload


def course_payload(course_type, campus, **overrides):
    payload = {
        "type_course": course_type.id,
        "description": "Curso criado pela API",
        "campus": campus.id,
    }
    payload.update(overrides)
    return payload


def questionnaire_payload(campus, name="Questionario API", **overrides):
    payload = {
        "name": name,
        "description": "Questionario criado pela API",
        "campus": campus.id,
        "active": True,
    }
    payload.update(overrides)
    return payload


def report_payload(
    course,
    campus,
    questionnaire,
    team,
    user,
    year,
    **overrides,
):
    payload = {
        "course": course.id,
        "campus": campus.id,
        "year": year,
        "questionnaire": questionnaire.id,
        "assessment": "Avaliacao criada pela API",
        "assigned_team": team.id,
        "assigned_user": user.id,
        "due_date": "2027-12-31",
        "notes": "Observacoes da API",
        "status": "Pendente",
    }
    payload.update(overrides)
    return payload


def build_resource_case(resource_name):
    if resource_name == "campus":
        instance = CampusFactory()
        return {
            "model": Campus,
            "instance": instance,
            "payload": campus_payload("Novo Campus API"),
            "put_payload": campus_payload(
                "Campus atualizado por PUT",
                city="Cidade PUT",
            ),
            "patch_payload": {"city": "Cidade PATCH"},
            "assertion_field": "city",
        }

    if resource_name == "cursos":
        campus = CampusFactory()
        instance = CourseFactory(campus=campus)
        target_type = CourseTypeFactory()
        return {
            "model": Course,
            "instance": instance,
            "payload": course_payload(target_type, campus),
            "put_payload": course_payload(
                target_type,
                campus,
                description="Curso atualizado por PUT",
            ),
            "patch_payload": {
                "description": "Curso atualizado por PATCH",
            },
            "assertion_field": "description",
        }

    if resource_name == "relatorios":
        campus = CampusFactory()
        course = CourseFactory(campus=campus)
        questionnaire = QuestionnaireFactory(campus=campus)
        team_user = TeamUserFactory()
        team = TeamFactory(campus=campus, users=(team_user,))
        instance = ReportFactory(
            campus=campus,
            course=course,
            questionnaire=questionnaire,
            assigned_team=team,
            assigned_user=team_user,
        )
        return {
            "model": Report,
            "instance": instance,
            "payload": report_payload(
                course,
                campus,
                questionnaire,
                team,
                team_user,
                instance.year + 1,
            ),
            "put_payload": report_payload(
                course,
                campus,
                questionnaire,
                team,
                team_user,
                instance.year + 2,
                status="Em andamento",
            ),
            "patch_payload": {"status": "Bloqueado"},
            "assertion_field": "status",
        }

    campus = CampusFactory()
    instance = QuestionnaireFactory(campus=campus)
    return {
        "model": Questionnaire,
        "instance": instance,
        "payload": questionnaire_payload(
            campus,
            name="Novo Questionario API",
        ),
        "put_payload": questionnaire_payload(
            campus,
            name="Questionario atualizado por PUT",
            active=False,
        ),
        "patch_payload": {"active": False},
        "assertion_field": "active",
    }


def authenticated_client(authenticate_api_client, user_factory):
    return authenticate_api_client(user_factory())


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
@pytest.mark.parametrize(
    ("user_factory", "expected_status"),
    READ_ROLE_CASES,
)
def test_matriz_de_papeis_controla_listagem_dos_recursos(
    api_client,
    authenticate_api_client,
    resource_name,
    user_factory,
    expected_status,
):
    build_resource_case(resource_name)
    client = api_client
    if user_factory:
        client = authenticated_client(
            authenticate_api_client,
            user_factory,
        )

    response = client.get(f"/api/v1/{resource_name}/")

    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        assert "results" in response.data


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
@pytest.mark.parametrize(
    ("user_factory", "expected_status"),
    WRITE_ROLE_CASES,
)
def test_matriz_de_papeis_controla_criacao_dos_recursos(
    authenticate_api_client,
    resource_name,
    user_factory,
    expected_status,
):
    case = build_resource_case(resource_name)
    client = authenticated_client(
        authenticate_api_client,
        user_factory,
    )
    count_before = case["model"].objects.count()

    response = client.post(
        f"/api/v1/{resource_name}/",
        case["payload"],
        format="json",
    )

    assert response.status_code == expected_status
    expected_increment = (
        1 if expected_status == status.HTTP_201_CREATED else 0
    )
    assert (
        case["model"].objects.count()
        == count_before + expected_increment
    )


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_detalhe_retorna_objeto_existente(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    case = build_resource_case(resource_name)
    client = authenticate_api_client(coordinator)

    response = client.get(
        f"/api/v1/{resource_name}/{case['instance'].id}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == case["instance"].id


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_put_atualiza_recurso_com_payload_completo(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    case = build_resource_case(resource_name)
    client = authenticate_api_client(coordinator)

    response = client.put(
        f"/api/v1/{resource_name}/{case['instance'].id}/",
        case["put_payload"],
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    field = case["assertion_field"]
    assert response.data[field] == case["put_payload"][field]


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_patch_atualiza_apenas_campos_informados(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    case = build_resource_case(resource_name)
    client = authenticate_api_client(coordinator)

    response = client.patch(
        f"/api/v1/{resource_name}/{case['instance'].id}/",
        case["patch_payload"],
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    field = case["assertion_field"]
    assert response.data[field] == case["patch_payload"][field]


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_delete_nao_e_permitido_nem_para_superadmin(
    authenticate_api_client,
    superadmin,
    resource_name,
):
    case = build_resource_case(resource_name)
    client = authenticate_api_client(superadmin)

    response = client.delete(
        f"/api/v1/{resource_name}/{case['instance'].id}/"
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert case["model"].objects.filter(
        pk=case["instance"].pk
    ).exists()


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_detalhe_inexistente_retorna_404(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    client = authenticate_api_client(coordinator)

    response = client.get(
        f"/api/v1/{resource_name}/999999/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_criacao_com_payload_invalido_retorna_400(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    client = authenticate_api_client(coordinator)

    response = client.post(
        f"/api/v1/{resource_name}/",
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_listagem_aplica_paginacao_de_dez_itens(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    RESOURCE_FACTORIES[resource_name].create_batch(11)
    client = authenticate_api_client(coordinator)

    response = client.get(f"/api/v1/{resource_name}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] >= 11
    assert len(response.data["results"]) == 10
    assert response.data["next"] is not None


def build_search_case(resource_name):
    if resource_name == "campus":
        return (
            CampusFactory(campus_name="BuscaCampusUnica"),
            CampusFactory(campus_name="OutroCampus"),
            "BuscaCampusUnica",
        )

    if resource_name == "cursos":
        return (
            CourseFactory(
                type_course=CourseTypeFactory(
                    type_name_course="BuscaCursoUnica"
                )
            ),
            CourseFactory(
                type_course=CourseTypeFactory(
                    type_name_course="OutroCurso"
                )
            ),
            "BuscaCursoUnica",
        )

    if resource_name == "relatorios":
        return (
            ReportFactory(status="BuscaStatusUnico"),
            ReportFactory(status="OutroStatus"),
            "BuscaStatusUnico",
        )

    return (
        QuestionnaireFactory(name="BuscaQuestionarioUnica"),
        QuestionnaireFactory(name="OutroQuestionario"),
        "BuscaQuestionarioUnica",
    )


@pytest.mark.parametrize("resource_name", RESOURCE_NAMES)
def test_busca_filtra_listagem_pelos_campos_configurados(
    authenticate_api_client,
    coordinator,
    resource_name,
):
    matching, nonmatching, term = build_search_case(resource_name)
    client = authenticate_api_client(coordinator)

    response = client.get(
        f"/api/v1/{resource_name}/",
        {"search": term},
    )

    assert response.status_code == status.HTTP_200_OK
    result_ids = {item["id"] for item in response.data["results"]}
    assert matching.id in result_ids
    assert nonmatching.id not in result_ids


def test_equipe_visualiza_relatorios_somente_por_assigned_team(
    authenticate_api_client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    visible_by_team = ReportFactory(
        campus=team.campus,
        course=CourseFactory(campus=team.campus),
        questionnaire=QuestionnaireFactory(campus=team.campus),
        assigned_team=team,
        assigned_user=None,
    )
    assigned_user_only = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    hidden = ReportFactory()
    client = authenticate_api_client(team_user)

    response = client.get("/api/v1/relatorios/")

    assert response.status_code == status.HTTP_200_OK
    result_ids = {item["id"] for item in response.data["results"]}
    assert visible_by_team.id in result_ids
    assert assigned_user_only.id not in result_ids
    assert hidden.id not in result_ids
    assert (
        client.get(f"/api/v1/relatorios/{hidden.id}/").status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client.get(
            f"/api/v1/relatorios/{assigned_user_only.id}/"
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_equipe_visualiza_questionarios_somente_por_assigned_team(
    authenticate_api_client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    visible_by_team = QuestionnaireFactory(campus=team.campus)
    ReportFactory(
        campus=team.campus,
        course=CourseFactory(campus=team.campus),
        questionnaire=visible_by_team,
        assigned_team=team,
        assigned_user=None,
    )
    assigned_user_only = QuestionnaireFactory()
    ReportFactory(
        campus=assigned_user_only.campus,
        course=CourseFactory(campus=assigned_user_only.campus),
        questionnaire=assigned_user_only,
        assigned_team=None,
        assigned_user=team_user,
    )
    hidden = QuestionnaireFactory()
    ReportFactory(
        campus=hidden.campus,
        course=CourseFactory(campus=hidden.campus),
        questionnaire=hidden,
    )
    client = authenticate_api_client(team_user)

    response = client.get("/api/v1/questionarios/")

    assert response.status_code == status.HTTP_200_OK
    result_ids = {item["id"] for item in response.data["results"]}
    assert visible_by_team.id in result_ids
    assert assigned_user_only.id not in result_ids
    assert hidden.id not in result_ids
    assert (
        client.get(
            f"/api/v1/questionarios/{hidden.id}/"
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client.get(
            f"/api/v1/questionarios/{assigned_user_only.id}/"
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_login_sem_campos_obrigatorios_retorna_400(api_client):
    response = api_client.post(
        "/api/v1/auth/login/",
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert set(response.data) == {"username", "password"}


def test_importacao_com_json_malformado_retorna_400(
    authenticate_api_client,
    coordinator,
    invalid_questionnaire_content,
):
    client = authenticate_api_client(coordinator)

    response = client.generic(
        "POST",
        "/api/v1/questionarios/importar/",
        data=invalid_questionnaire_content,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_importacao_com_campos_ausentes_retorna_400(
    authenticate_api_client,
    coordinator,
):
    client = authenticate_api_client(coordinator)

    response = client.post(
        "/api/v1/questionarios/importar/",
        {"questionario": "Importacao incompleta"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert set(response.data) == {"dimensao", "questao"}


def test_superadmin_pode_importar_questionario(
    authenticate_api_client,
    superadmin,
    valid_questionnaire_payload,
):
    client = authenticate_api_client(superadmin)

    response = client.post(
        "/api/v1/questionarios/importar/",
        valid_questionnaire_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Questionnaire.objects.filter(
        pk=response.data["questionnaire_id"]
    ).exists()


def test_anonimo_nao_pode_importar_questionario(
    api_client,
    valid_questionnaire_payload,
):
    response = api_client.post(
        "/api/v1/questionarios/importar/",
        valid_questionnaire_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_equipe_responde_com_alternativa_e_persiste_criterio(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    multiple_choice_question,
    answer_options,
):
    client = authenticate_api_client(team_user)
    selected_option = answer_options[0]

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": multiple_choice_question.id,
            "selected_answer_option": selected_option.id,
            "free_text": "Argumentacao da equipe",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=multiple_choice_question,
    )
    assert answer.selected_answer_option == selected_option
    assert answer.answer == selected_option.answer_value
    assert answer.free_text == "Argumentacao da equipe"


def test_api_rejeita_argumentacao_acima_do_limite(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    text_question,
):
    questionnaire.argumentation_character_limit = 10
    questionnaire.save(update_fields=('argumentation_character_limit',))
    client = authenticate_api_client(team_user)

    response = client.post(
        f'/api/v1/questionarios/{questionnaire.id}/responder/',
        {
            'report': report.id,
            'question': text_question.id,
            'free_text': 'Onze letras',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'free_text' in response.data
    assert not ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()


def test_api_aceita_argumentacao_no_limite_exato(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    text_question,
):
    questionnaire.argumentation_character_limit = 10
    questionnaire.save(update_fields=('argumentation_character_limit',))
    client = authenticate_api_client(team_user)

    response = client.post(
        f'/api/v1/questionarios/{questionnaire.id}/responder/',
        {
            'report': report.id,
            'question': text_question.id,
            'free_text': 'Linha 1\r\nxx',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
        free_text='Linha 1\nxx',
    ).exists()


def test_resposta_rejeita_pergunta_de_outro_questionario(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
):
    other_question = TextQuestionFactory()
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": other_question.id,
            "answer": "Resposta indevida",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_resposta_rejeita_alternativa_de_outra_pergunta(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    multiple_choice_question,
):
    unrelated_option = QuestionAnswerOptionFactory()
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": multiple_choice_question.id,
            "selected_answer_option": unrelated_option.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_resposta_rejeita_relatorio_de_outro_questionario(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
    text_question,
):
    other_report = ReportFactory(assigned_user=team_user)
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": other_report.id,
            "question": text_question.id,
            "answer": "Resposta indevida",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "manager_factory",
    (
        pytest.param(CoordinatorFactory, id="coordenador"),
        pytest.param(SuperAdminFactory, id="superadmin"),
    ),
)
def test_gestor_responde_questionario_de_qualquer_relatorio(
    authenticate_api_client,
    questionnaire,
    report,
    text_question,
    manager_factory,
):
    client = authenticated_client(
        authenticate_api_client,
        manager_factory,
    )

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta do gestor",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
        answer="Resposta do gestor",
    ).exists()


def test_resposta_sem_pergunta_retorna_400(
    authenticate_api_client,
    team_user,
    questionnaire,
    report,
):
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {"report": report.id, "answer": "Sem pergunta"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "question" in response.data


def test_equipe_fora_de_assigned_team_recebe_403_ao_responder(
    authenticate_api_client,
    questionnaire,
    report,
    text_question,
):
    outsider = TeamUserFactory()
    client = authenticate_api_client(outsider)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta indevida",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()


def test_anonimo_recebe_401_ao_responder(
    api_client,
    questionnaire,
    report,
    text_question,
):
    response = api_client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta anônima",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()


def test_assigned_user_sem_assigned_team_nao_responde_relatorio(
    authenticate_api_client,
    team_user,
    questionnaire,
    text_question,
):
    report = ReportFactory(
        campus=questionnaire.campus,
        course=CourseFactory(campus=questionnaire.campus),
        questionnaire=questionnaire,
        assigned_team=None,
        assigned_user=team_user,
    )
    client = authenticate_api_client(team_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta do usuario atribuido",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()
