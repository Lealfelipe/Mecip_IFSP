import pytest
from django.test import Client
from django.urls import reverse

from mecip.models import Question, QuestionnaireSection, Report
from tests.factories import (
    QuestionnaireFactory,
    QuestionnaireSectionFactory,
    ReportFactory,
    ReportQuestionAnswerFactory,
    TeamFactory,
    TeamUserFactory,
    TextQuestionFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]

MUTATION_CASES = (
    "assign",
    "advance",
    "change_status",
    "delete_section",
    "delete_question",
)


@pytest.fixture
def assignable_report(team):
    return ReportFactory(
        campus=team.campus,
        assigned_team=team,
        assigned_user=None,
        status="Pendente",
    )


@pytest.fixture
def complete_report(report, text_question):
    ReportQuestionAnswerFactory(
        report=report,
        question=text_question,
        answer="Resposta completa",
    )
    return report


def mutation_url(
    case,
    assignable_report,
    complete_report,
    questionnaire,
    section,
    text_question,
):
    if case == "assign":
        return reverse("mecip:assign_report", args=(assignable_report.id,))
    if case == "advance":
        return reverse(
            "mecip:advance_report_status",
            args=(complete_report.id,),
        )
    if case == "change_status":
        return reverse(
            "mecip:change_report_status",
            args=(complete_report.id, "aprovar"),
        )
    if case == "delete_section":
        return reverse(
            "mecip:delete_questionnaire_section",
            args=(questionnaire.id, section.id),
        )
    return reverse(
        "mecip:delete_question",
        args=(questionnaire.id, text_question.id),
    )


def mutation_state(
    assignable_report,
    complete_report,
    section,
    text_question,
):
    return (
        Report.objects.values_list("assigned_user_id", "status").get(
            pk=assignable_report.pk
        ),
        Report.objects.values_list("assigned_user_id", "status").get(
            pk=complete_report.pk
        ),
        QuestionnaireSection.objects.filter(pk=section.pk).exists(),
        Question.objects.filter(pk=text_question.pk).exists(),
    )


def authorized_user(case, team_user, coordinator):
    if case in {"assign", "advance"}:
        return team_user
    return coordinator


@pytest.mark.parametrize("case", MUTATION_CASES)
def test_get_retorna_405_sem_modificar_dados(
    case,
    client,
    team_user,
    coordinator,
    assignable_report,
    complete_report,
    questionnaire,
    section,
    text_question,
):
    url = mutation_url(
        case,
        assignable_report,
        complete_report,
        questionnaire,
        section,
        text_question,
    )
    before = mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    )
    client.force_login(authorized_user(case, team_user, coordinator))

    response = client.get(url)

    assert response.status_code == 405
    assert mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    ) == before


@pytest.mark.parametrize("case", MUTATION_CASES)
def test_post_autorizado_modifica_somente_o_objeto_esperado(
    case,
    client,
    team_user,
    coordinator,
    assignable_report,
    complete_report,
    questionnaire,
    section,
    text_question,
):
    untouched_report = ReportFactory(status="Bloqueado")
    sibling_section = QuestionnaireSectionFactory(
        questionnaire=questionnaire,
        teams=(TeamFactory(),),
    )
    sibling_question = TextQuestionFactory(section=sibling_section)
    url = mutation_url(
        case,
        assignable_report,
        complete_report,
        questionnaire,
        section,
        text_question,
    )
    client.force_login(authorized_user(case, team_user, coordinator))

    response = client.post(url)

    assert response.status_code == 302
    untouched_report.refresh_from_db()
    assert untouched_report.status == "Bloqueado"

    if case == "assign":
        assignable_report.refresh_from_db()
        assert assignable_report.assigned_user == team_user
        assert assignable_report.status == "Em andamento"
    elif case == "advance":
        complete_report.refresh_from_db()
        assert complete_report.status == "Pendente avaliação"
    elif case == "change_status":
        complete_report.refresh_from_db()
        assert complete_report.status == "Aprovado"
    elif case == "delete_section":
        assert not QuestionnaireSection.objects.filter(
            pk=section.pk
        ).exists()
        assert QuestionnaireSection.objects.filter(
            pk=sibling_section.pk
        ).exists()
        assert Question.objects.filter(pk=sibling_question.pk).exists()
    else:
        assert not Question.objects.filter(pk=text_question.pk).exists()
        assert QuestionnaireSection.objects.filter(pk=section.pk).exists()
        assert Question.objects.filter(pk=sibling_question.pk).exists()


@pytest.mark.parametrize("case", MUTATION_CASES)
def test_post_sem_csrf_e_rejeitado_sem_modificar_dados(
    case,
    team_user,
    coordinator,
    assignable_report,
    complete_report,
    questionnaire,
    section,
    text_question,
):
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(
        authorized_user(case, team_user, coordinator)
    )
    url = mutation_url(
        case,
        assignable_report,
        complete_report,
        questionnaire,
        section,
        text_question,
    )
    before = mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    )

    response = csrf_client.post(url)

    assert response.status_code == 403
    assert mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    ) == before


@pytest.mark.parametrize(
    ("case", "expected_status"),
    (
        ("assign", 302),
        ("advance", 302),
        ("change_status", 302),
        ("delete_section", 403),
        ("delete_question", 403),
    ),
)
def test_post_sem_permissao_nao_modifica_dados(
    case,
    expected_status,
    client,
    team_user,
    assignable_report,
    complete_report,
    questionnaire,
    section,
    text_question,
):
    user = (
        team_user
        if case in {"change_status", "delete_section", "delete_question"}
        else TeamUserFactory()
    )
    client.force_login(user)
    url = mutation_url(
        case,
        assignable_report,
        complete_report,
        questionnaire,
        section,
        text_question,
    )
    before = mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    )

    response = client.post(url)

    assert response.status_code == expected_status
    assert mutation_state(
        assignable_report,
        complete_report,
        section,
        text_question,
    ) == before


@pytest.mark.parametrize("object_kind", ("section", "question"))
def test_delete_nao_manipula_id_de_outro_questionario(
    object_kind,
    client,
    coordinator,
    questionnaire,
):
    other_questionnaire = QuestionnaireFactory()
    foreign_section = QuestionnaireSectionFactory(
        questionnaire=other_questionnaire
    )
    foreign_question = TextQuestionFactory(section=foreign_section)
    client.force_login(coordinator)

    if object_kind == "section":
        url = reverse(
            "mecip:delete_questionnaire_section",
            args=(questionnaire.id, foreign_section.id),
        )
    else:
        url = reverse(
            "mecip:delete_question",
            args=(questionnaire.id, foreign_question.id),
        )

    response = client.post(url)

    assert response.status_code == 404
    assert QuestionnaireSection.objects.filter(
        pk=foreign_section.pk
    ).exists()
    assert Question.objects.filter(pk=foreign_question.pk).exists()


def test_modal_de_exclusao_referencia_endpoints_corretos(
    client,
    coordinator,
    questionnaire,
    section,
    text_question,
):
    client.force_login(coordinator)

    response = client.get(
        reverse(
            "mecip:update_questionnaire",
            args=(questionnaire.id,),
        )
    )

    assert response.status_code == 200
    assert response.content.count(b'name="csrfmiddlewaretoken"') >= 2
    assert b'id="questionnaire-delete-form"' in response.content
    assert (
        f'data-delete-url="{reverse(
            "mecip:delete_questionnaire_section",
            args=(questionnaire.id, section.id),
        )}"'.encode()
        in response.content
    )
    assert (
        f'data-delete-url="{reverse(
            "mecip:delete_question",
            args=(questionnaire.id, text_question.id),
        )}"'.encode()
        in response.content
    )
