import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from mecip.models import Attachments, Report, ReportQuestionAnswer
from tests.factories import (
    CourseFactory,
    QuestionnaireFactory,
    ReferenceAttachmentFactory,
    ReportFactory,
    ReportQuestionAnswerFactory,
    TeamFactory,
    TeamUserFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def response_messages(response):
    return [
        str(message)
        for message in get_messages(response.wsgi_request)
    ]


def report_payload(
    course,
    campus,
    questionnaire,
    team,
    team_user,
    year,
    **overrides,
):
    payload = {
        "type_course": course.type_course_id,
        "campus": campus.id,
        "year": str(year),
        "questionnaire": questionnaire.id,
        "assigned_team": team.id,
        "assigned_user": team_user.id,
        "due_date": "2038-12-31",
        "notes": "Criado pela view",
        "status": "Pendente",
    }
    payload.update(overrides)
    return payload


def empty_attachment_formset(answer):
    prefix = f"attachments_{answer.id}"
    return {
        f"{prefix}-TOTAL_FORMS": "0",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_coordenador_cria_e_edita_relatorio_e_inicializa_respostas(
    client,
    coordinator,
    campus,
    course,
    questionnaire,
    team,
    team_user,
    text_question,
):
    client.force_login(coordinator)

    response = client.post(
        reverse("mecip:create_report"),
        report_payload(
            course,
            campus,
            questionnaire,
            team,
            team_user,
            2037,
        ),
    )
    report = Report.objects.get(
        course=course,
        campus=campus,
        year=2037,
    )

    assert response.status_code == 302
    assert ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()
    assert "Relatorio criado com sucesso!" in response_messages(response)

    response = client.post(
        reverse("mecip:update_report", args=(report.id,)),
        report_payload(
            course,
            campus,
            questionnaire,
            team,
            team_user,
            2037,
            assessment="Avaliacao atualizada",
            status="Em andamento",
        ),
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.assessment == "Avaliacao atualizada"
    assert report.status == "Em andamento"


def test_criacao_de_relatorio_parametrizada_prepara_curso_e_campus(
    client,
    coordinator,
    campus,
    course,
    questionnaire,
    team,
    team_user,
):
    client.force_login(coordinator)
    url = reverse(
        "mecip:create_report_params",
        args=(course.id, campus.id),
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["form"].initial["type_course"] == (
        course.type_course
    )
    assert response.context["form"].initial["campus"] == campus

    response = client.post(
        url,
        report_payload(
            course,
            campus,
            questionnaire,
            team,
            team_user,
            2038,
        ),
    )

    assert response.status_code == 302
    assert Report.objects.filter(
        course=course,
        campus=campus,
        year=2038,
    ).exists()


def test_dashboard_combina_filtros_e_calcula_contadores(
    client,
    coordinator,
):
    campus = CourseFactory().campus
    team = TeamFactory(campus=campus)
    matching = ReportFactory(
        campus=campus,
        course=CourseFactory(campus=campus),
        questionnaire=QuestionnaireFactory(campus=campus),
        assigned_team=team,
        status="Bloqueado",
    )
    ReportFactory(
        campus=campus,
        course=CourseFactory(campus=campus),
        questionnaire=QuestionnaireFactory(campus=campus),
        assigned_team=team,
        status="Pendente",
    )
    ReportFactory()
    client.force_login(coordinator)

    response = client.get(
        reverse("mecip:dashboard"),
        {
            "campus": campus.id,
            "team": team.id,
            "status": "Bloqueado",
        },
    )

    assert response.status_code == 200
    assert list(response.context["reports"]) == [matching]
    assert response.context["total_reports"] == 2
    assert response.context["selected_campus"] == str(campus.id)
    assert response.context["selected_team"] == str(team.id)
    assert response.context["selected_status"] == "Bloqueado"
    assert response.context["status_labels"]
    assert response.context["status_data"]


def test_listagem_de_relatorios_isola_equipes(
    client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    visible = ReportFactory(assigned_team=team, assigned_user=None)
    hidden = ReportFactory()
    client.force_login(team_user)

    response = client.get(reverse("mecip:index_report"))

    report_ids = {
        report.id for report in response.context["page_obj"]
    }
    assert visible.id in report_ids
    assert hidden.id not in report_ids


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A listagem web considera apenas assigned_team e ignora "
        "assigned_user quando nao existe equipe atribuida."
    ),
)
def test_usuario_atribuido_diretamente_visualiza_relatorio_na_listagem(
    client,
    team_user,
):
    report = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    client.force_login(team_user)

    response = client.get(reverse("mecip:index_report"))

    assert report in response.context["page_obj"]


def test_detalhe_indica_quando_usuario_pode_assumir_relatorio(
    client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    report = ReportFactory(
        assigned_team=team,
        assigned_user=None,
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:report", args=(report.id,))
    )

    assert response.status_code == 200
    assert response.context["can_assign"] is True


def test_get_atribui_relatorio_e_documenta_risco_de_csrf(
    client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    report = ReportFactory(
        assigned_team=team,
        assigned_user=None,
        status="Pendente",
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:assign_report", args=(report.id,))
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.assigned_user == team_user
    assert report.status == "Em andamento"


@pytest.mark.xfail(
    strict=True,
    reason="O detalhe de relatorio nao valida o escopo da equipe.",
)
def test_equipe_nao_acessa_detalhe_de_relatorio_alheio(
    client,
    team_user,
):
    report = ReportFactory()
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:report", args=(report.id,))
    )

    assert response.status_code == 404


@pytest.mark.xfail(
    strict=True,
    reason=(
        "O detalhe de curso inclui todos os relatorios sem filtrar "
        "pelo escopo do usuario."
    ),
)
def test_detalhe_de_curso_nao_expoe_relatorio_de_outra_equipe(
    client,
    team_user,
):
    course = CourseFactory()
    hidden = ReportFactory(
        campus=course.campus,
        course=course,
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:course", args=(course.id,))
    )

    assert hidden not in response.context["reports"]


def test_visualizacao_cria_respostas_e_exibe_contexto(
    client,
    team_user,
    report,
    text_question,
):
    client.force_login(team_user)
    ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).delete()

    response = client.get(
        reverse("mecip:view_questionnaire", args=(report.id,))
    )

    assert response.status_code == 200
    assert ReportQuestionAnswer.objects.filter(
        report=report,
        question=text_question,
    ).exists()
    assert response.context["can_answer"] is True
    assert response.context["all_answered"] is False


def test_equipe_responde_questionario_e_persiste_texto(
    client,
    team_user,
    report,
    text_question,
):
    client.force_login(team_user)
    client.get(
        reverse("mecip:answer_questionnaire", args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    payload = {
        f"answer_{answer.id}": "Resposta pela interface",
        f"free_text_{answer.id}": "Argumentacao pela interface",
        "action": "save_and_exit",
    }
    payload.update(empty_attachment_formset(answer))

    response = client.post(
        reverse("mecip:answer_questionnaire", args=(report.id,)),
        payload,
    )
    answer.refresh_from_db()

    assert response.status_code == 302
    assert response.url == reverse(
        "mecip:view_questionnaire",
        args=(report.id,),
    )
    assert answer.answer == "Resposta pela interface"
    assert answer.free_text == "Argumentacao pela interface"


def test_resposta_associa_anexo_catalogado(
    client,
    team_user,
    report,
    text_question,
):
    reference = ReferenceAttachmentFactory(active=True)
    client.force_login(team_user)
    client.get(
        reverse("mecip:answer_questionnaire", args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    payload = {
        f"answer_{answer.id}": "Resposta com anexo",
        "selected_reference_attachments": [reference.id],
        "action": "save_and_exit",
    }
    payload.update(empty_attachment_formset(answer))

    response = client.post(
        reverse("mecip:answer_questionnaire", args=(report.id,)),
        payload,
    )

    assert response.status_code == 302
    assert Attachments.objects.filter(
        answer=answer,
        reference_attachment=reference,
    ).exists()


def test_resposta_processa_upload_direto(
    client,
    team_user,
    report,
    text_question,
    valid_upload,
):
    client.force_login(team_user)
    client.get(
        reverse("mecip:answer_questionnaire", args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    prefix = f"attachments_{answer.id}"
    payload = {
        f"answer_{answer.id}": "Resposta com upload",
        "action": "save_and_exit",
        f"{prefix}-TOTAL_FORMS": "1",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
        f"{prefix}-0-id": "",
        f"{prefix}-0-name": "Upload da interface",
        f"{prefix}-0-description": "Documento enviado",
        f"{prefix}-0-file": valid_upload,
    }

    response = client.post(
        reverse("mecip:answer_questionnaire", args=(report.id,)),
        payload,
    )

    assert response.status_code == 302
    assert Attachments.objects.filter(
        answer=answer,
        reference_attachment__name="Upload da interface",
    ).exists()


def test_usuario_sem_acesso_e_redirecionado_do_questionario(
    client,
    report,
):
    unrelated_user = TeamUserFactory()
    client.force_login(unrelated_user)

    response = client.get(
        reverse("mecip:view_questionnaire", args=(report.id,))
    )

    assert response.status_code == 302
    assert response.url == reverse("mecip:report", args=(report.id,))
    assert any(
        "Somente membro" in message
        for message in response_messages(response)
    )


def test_relatorio_sem_questionario_redireciona_com_erro(
    client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    report = ReportFactory(
        questionnaire=None,
        assigned_team=team,
        assigned_user=None,
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:view_questionnaire", args=(report.id,))
    )

    assert response.status_code == 302
    assert any(
        "nao tem questionario" in message
        for message in response_messages(response)
    )


def test_get_avanca_status_e_documenta_risco_de_csrf(
    client,
    team_user,
    report,
    text_question,
):
    ReportQuestionAnswerFactory(
        report=report,
        question=text_question,
        answer="Resposta completa",
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:advance_report_status", args=(report.id,))
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.status == "Pendente avaliação"


@pytest.mark.parametrize(
    ("action", "expected_status"),
    (
        pytest.param("aprovar", "Aprovado", id="aprovar"),
        pytest.param("bloquear", "Bloqueado", id="bloquear"),
        pytest.param("ajustar", "Pendente ajuste", id="ajustar"),
        pytest.param("reprovar", "Reprovado", id="reprovar"),
    ),
)
def test_get_altera_status_e_documenta_risco_de_csrf(
    client,
    coordinator,
    report,
    text_question,
    action,
    expected_status,
):
    ReportQuestionAnswerFactory(
        report=report,
        question=text_question,
        answer="Resposta completa",
    )
    client.force_login(coordinator)

    response = client.get(
        reverse(
            "mecip:change_report_status",
            args=(report.id, action),
        )
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.status == expected_status


def test_status_nao_avanca_com_resposta_incompleta(
    client,
    team_user,
    report,
    text_question,
):
    ReportQuestionAnswer.objects.update_or_create(
        report=report,
        question=text_question,
        defaults={"answer": ""},
    )
    original_status = report.status
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:advance_report_status", args=(report.id,))
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.status == original_status
    assert any(
        "Todas as questoes" in message
        for message in response_messages(response)
    )


def test_download_pdf_retorna_arquivo_valido(
    client,
    coordinator,
    report,
):
    client.force_login(coordinator)

    response = client.get(
        reverse("mecip:report_pdf_download", args=(report.id,))
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"].startswith("attachment;")
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 100


@pytest.mark.xfail(
    strict=True,
    reason="O download de PDF nao valida o escopo do relatorio.",
)
def test_equipe_nao_baixa_pdf_de_relatorio_alheio(
    client,
    team_user,
):
    report = ReportFactory()
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:report_pdf_download", args=(report.id,))
    )

    assert response.status_code == 404


def test_endpoints_auxiliares_filtram_campus_e_cursos(
    client,
    coordinator,
    campus,
    course,
):
    client.force_login(coordinator)

    response = client.get(
        reverse(
            "mecip:get_campus_for_course",
            args=(course.type_course_id,),
        )
    )

    assert response.status_code == 200
    assert campus.id in {item["id"] for item in response.json()}

    response = client.get(
        reverse(
            "mecip:get_courses_for_campus",
            args=(campus.id,),
        )
    )

    assert response.status_code == 200
    assert course.type_course_id in {
        item["id"] for item in response.json()
    }
