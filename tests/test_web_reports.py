import pytest
from datetime import timedelta

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from mecip.models import (
    Attachments,
    ReferenceAttachment,
    Report,
    ReportQuestionAnswer,
)
from tests.factories import (
    CoordinatorFactory,
    CourseFactory,
    QuestionnaireFactory,
    ReferenceAttachmentFactory,
    ReportFactory,
    ReportQuestionAnswerFactory,
    SuperAdminFactory,
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


def test_dashboard_filtra_por_curso_e_ano(client, coordinator):
    course = CourseFactory()
    matching = ReportFactory(
        campus=course.campus,
        course=course,
        year=2030,
    )
    ReportFactory(
        campus=course.campus,
        course=course,
        year=2031,
    )
    other_course = CourseFactory(campus=course.campus)
    ReportFactory(
        campus=course.campus,
        course=other_course,
        year=2030,
    )
    client.force_login(coordinator)

    response = client.get(
        reverse("mecip:dashboard"),
        {"course": course.id, "year": 2030},
    )

    assert response.status_code == 200
    assert list(response.context["reports"]) == [matching]
    assert response.context["selected_course"] == str(course.id)
    assert response.context["selected_year"] == "2030"


@pytest.mark.parametrize(
    ("sort_field", "direction", "expected_indexes"),
    (
        ("course", "asc", (0, 1, 2)),
        ("course", "desc", (2, 1, 0)),
        ("year", "asc", (0, 2, 1)),
        ("year", "desc", (1, 2, 0)),
        ("created", "asc", (0, 1, 2)),
        ("created", "desc", (2, 1, 0)),
    ),
)
def test_dashboard_ordena_colunas_permitidas(
    client,
    coordinator,
    sort_field,
    direction,
    expected_indexes,
):
    now = timezone.now()
    report_data = (
        ("Arquitetura", 2022, now - timedelta(days=2)),
        ("Direito", 2024, now - timedelta(days=1)),
        ("Medicina", 2023, now),
    )
    reports = []
    for course_name, year, created_date in report_data:
        course = CourseFactory(
            type_course__type_name_course=course_name,
        )
        reports.append(
            ReportFactory(
                campus=course.campus,
                course=course,
                year=year,
                created_date=created_date,
            )
        )
    client.force_login(coordinator)

    response = client.get(
        reverse("mecip:dashboard"),
        {"sort": sort_field, "direction": direction},
    )

    assert response.status_code == 200
    assert list(response.context["reports"]) == [
        reports[index] for index in expected_indexes
    ]


def test_dashboard_ignora_ordenacao_invalida(client, coordinator):
    older = ReportFactory(created_date=timezone.now() - timedelta(days=1))
    newer = ReportFactory(created_date=timezone.now())
    client.force_login(coordinator)

    response = client.get(
        reverse("mecip:dashboard"),
        {"sort": "campo_inexistente", "direction": "invalida"},
    )

    assert response.status_code == 200
    assert list(response.context["reports"]) == [newer, older]
    assert response.context["selected_sort"] == "created"
    assert response.context["selected_direction"] == "desc"


def test_dashboard_de_equipe_usa_somente_assigned_team(
    client,
    team_user,
):
    team = TeamFactory(users=(team_user,))
    visible = ReportFactory(
        assigned_team=team,
        assigned_user=None,
    )
    assigned_user_only = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    hidden = ReportFactory()
    client.force_login(team_user)

    response = client.get(reverse("mecip:dashboard"))

    report_ids = {report.id for report in response.context["reports"]}
    assert report_ids == {visible.id}
    assert assigned_user_only.id not in report_ids
    assert hidden.id not in report_ids
    assert response.context["total_reports"] == 1


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


def test_assigned_user_isolado_nao_visualiza_relatorio_na_listagem(
    client,
    team_user,
):
    report = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    client.force_login(team_user)

    response = client.get(reverse("mecip:index_report"))

    assert report not in response.context["page_obj"]


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


def test_assigned_user_isolado_recebe_403_no_detalhe(
    client,
    team_user,
):
    report = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:report", args=(report.id,))
    )

    assert response.status_code == 403
    assert "mecip/access_denied.html" in [
        template.name for template in response.templates
    ]
    assert "report" not in response.context


@pytest.mark.parametrize(
    "manager_factory",
    (
        pytest.param(CoordinatorFactory, id="coordenador"),
        pytest.param(SuperAdminFactory, id="superadmin"),
    ),
)
def test_gestor_acessa_detalhe_de_qualquer_relatorio(
    client,
    manager_factory,
):
    report = ReportFactory()
    client.force_login(manager_factory())

    response = client.get(
        reverse("mecip:report", args=(report.id,))
    )

    assert response.status_code == 200
    assert response.context["report"] == report


def test_detalhe_de_curso_exibe_relatorio_alheio_sem_conceder_acesso(
    client,
    team_user,
):
    course = CourseFactory()
    foreign_report = ReportFactory(
        campus=course.campus,
        course=course,
    )
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:course", args=(course.id,))
    )

    assert response.status_code == 200
    assert foreign_report in response.context["reports"]

    report_response = client.get(
        reverse("mecip:report", args=(foreign_report.id,))
    )
    assert report_response.status_code == 403


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


def test_campos_textuais_iniciam_vazios_quando_resposta_e_nula(
    client,
    team_user,
    report,
    text_question,
):
    client.force_login(team_user)
    client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )

    answer.answer = None
    answer.free_text = None
    answer.save(update_fields=('answer', 'free_text'))

    response = client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert '>None</textarea>' not in content
    assert f'class="form-control"></textarea>' in content


def test_questionario_exibe_contador_e_limite_configurado(
    client,
    team_user,
    report,
    text_question,
):
    report.questionnaire.argumentation_character_limit = 25
    report.questionnaire.save(
        update_fields=('argumentation_character_limit',)
    )
    client.force_login(team_user)

    response = client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert 'maxlength="25"' in content
    assert 'data-character-limit="25"' in content
    assert '0 / 25' in content
    assert 'is-warning' in content
    assert 'is-limit-exceeded' in content


def test_tela_de_resposta_exibe_acao_para_copiar_link_do_anexo(
    client,
    team_user,
    report,
    text_question,
):
    client.force_login(team_user)
    client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    attachment = Attachments.objects.create(
        answer=answer,
        name='Anexo com link copiável',
        file='answer_attachments/anexo.pdf',
    )

    response = client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert 'data-copy-attachment-link' in content
    assert 'data-copy-attachment-alert' in content
    assert (
        f'data-attachment-url="{attachment.public_path}"'
        in content
    )
    assert 'aria-label="Copiar link do anexo"' in content


def test_resposta_web_rejeita_argumentacao_acima_do_limite(
    client,
    team_user,
    report,
    text_question,
):
    report.questionnaire.argumentation_character_limit = 10
    report.questionnaire.save(
        update_fields=('argumentation_character_limit',)
    )
    client.force_login(team_user)
    client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    original_free_text = answer.free_text
    payload = {
        f'answer_{answer.id}': 'Resposta não persistida',
        f'free_text_{answer.id}': 'Onze letras',
        'action': 'save_and_exit',
    }
    payload.update(empty_attachment_formset(answer))

    response = client.post(
        reverse('mecip:answer_questionnaire', args=(report.id,)),
        payload,
    )
    answer.refresh_from_db()

    assert response.status_code == 200
    assert answer.free_text == original_free_text
    assert any(
        'não pode ultrapassar 10 caracteres' in message
        for message in response_messages(response)
    )


def test_resposta_web_normaliza_quebras_de_linha_antes_de_contar(
    client,
    team_user,
    report,
    text_question,
):
    report.questionnaire.argumentation_character_limit = 10
    report.questionnaire.save(
        update_fields=('argumentation_character_limit',)
    )
    client.force_login(team_user)
    client.get(
        reverse('mecip:answer_questionnaire', args=(report.id,))
    )
    answer = ReportQuestionAnswer.objects.get(
        report=report,
        question=text_question,
    )
    payload = {
        f'answer_{answer.id}': 'Resposta válida',
        f'free_text_{answer.id}': 'Linha 1\r\nxx',
        'action': 'save_and_exit',
    }
    payload.update(empty_attachment_formset(answer))

    response = client.post(
        reverse('mecip:answer_questionnaire', args=(report.id,)),
        payload,
    )
    answer.refresh_from_db()

    assert response.status_code == 302
    assert answer.free_text == 'Linha 1\nxx'


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
    assert ReferenceAttachment.objects.filter(
        name="Upload da interface"
    ).count() == 1


def test_resposta_rejeita_upload_acima_do_limite(
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
    attachment_count = Attachments.objects.count()
    reference_count = ReferenceAttachment.objects.count()
    prefix = f"attachments_{answer.id}"

    response = client.post(
        reverse("mecip:answer_questionnaire", args=(report.id,)),
        {
            f"answer_{answer.id}": "Resposta com upload inválido",
            "action": "save_and_exit",
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": "",
            f"{prefix}-0-name": "Upload acima do limite",
            f"{prefix}-0-description": "Documento inválido",
            f"{prefix}-0-file": SimpleUploadedFile(
                "documento.pdf",
                b"x" * (10_000_000 + 1),
                content_type="application/pdf",
            ),
        },
    )

    assert response.status_code == 200
    assert Attachments.objects.count() == attachment_count
    assert ReferenceAttachment.objects.count() == reference_count


@pytest.mark.parametrize(
    "route_name",
    ("view_questionnaire", "answer_questionnaire"),
)
def test_usuario_sem_acesso_recebe_403_antes_de_carregar_respostas(
    client,
    report,
    route_name,
):
    unrelated_user = TeamUserFactory()
    client.force_login(unrelated_user)
    answer_count = ReportQuestionAnswer.objects.count()

    response = client.get(
        reverse(f"mecip:{route_name}", args=(report.id,))
    )

    assert response.status_code == 403
    assert "mecip/access_denied.html" in [
        template.name for template in response.templates
    ]
    assert ReportQuestionAnswer.objects.count() == answer_count


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

    response = client.post(
        reverse("mecip:advance_report_status", args=(report.id,))
    )
    report.refresh_from_db()

    assert response.status_code == 302
    assert report.status == original_status
    assert any(
        "Todas as questoes" in message
        for message in response_messages(response)
    )


@pytest.mark.parametrize(
    "manager_factory",
    (
        pytest.param(CoordinatorFactory, id="coordenador"),
        pytest.param(SuperAdminFactory, id="superadmin"),
    ),
)
def test_gestor_baixa_pdf_valido(
    client,
    report,
    manager_factory,
):
    client.force_login(manager_factory())

    response = client.get(
        reverse("mecip:report_pdf_download", args=(report.id,))
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"].startswith("attachment;")
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 100


def test_html_do_pdf_separa_por_indicador_e_exibe_argumentacao(
    report,
    text_question,
):
    answer = ReportQuestionAnswer.objects.create(
        report=report,
        question=text_question,
        answer='5',
        free_text='Primeira linha.\nSegunda linha.',
    )

    html = render_to_string(
        'mecip/report_pdf.html',
        {
            'report': report,
            'answers': [answer],
        },
    )

    assert f'Indicador: {text_question.indicator}' in ' '.join(
        html.split()
    )
    assert '<strong>Argumentação:</strong>' in html
    assert 'Primeira linha.<br>Segunda linha.' in html
    assert 'Seção:' not in html


def test_pdf_usa_link_publico_absoluto_configurado(
    client,
    coordinator,
    report,
    text_question,
    reference_attachment,
    settings,
):
    answer = ReportQuestionAnswer.objects.create(
        report=report,
        question=text_question,
        answer='Resposta com link publico',
    )
    attachment = Attachments.objects.create(
        answer=answer,
        reference_attachment=reference_attachment,
        name=reference_attachment.name,
    )
    settings.PUBLIC_BASE_URL = 'https://mecip.example.test'
    client.force_login(coordinator)

    response = client.get(
        reverse('mecip:report_pdf_download', args=(report.id,))
    )

    assert response.status_code == 200
    assert (
        f'{settings.PUBLIC_BASE_URL}{attachment.public_path}'.encode()
        in response.content
    )


def test_membro_de_assigned_team_baixa_pdf(
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
        reverse("mecip:report_pdf_download", args=(report.id,))
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_usuario_fora_de_assigned_team_recebe_403_sem_gerar_pdf(
    client,
    team_user,
    monkeypatch,
):
    report = ReportFactory(
        assigned_team=None,
        assigned_user=team_user,
    )
    client.force_login(team_user)

    def forbidden_builder(*args, **kwargs):
        pytest.fail("O gerador de PDF não deveria ser chamado")

    monkeypatch.setattr(
        "mecip.views.report_view._build_report_pdf",
        forbidden_builder,
    )

    response = client.get(
        reverse("mecip:report_pdf_download", args=(report.id,))
    )

    assert response.status_code == 403
    assert "mecip/access_denied.html" in [
        template.name for template in response.templates
    ]


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
