import pytest
from django.contrib.auth import SESSION_KEY
from django.urls import reverse

from tests.factories import (
    CampusFactory,
    CoordinatorFactory,
    CourseFactory,
    CourseTypeFactory,
    QuestionnaireFactory,
    QuestionnaireSectionFactory,
    ReferenceAttachmentFactory,
    ReportFactory,
    TeamFactory,
    TeamUserFactory,
    TextQuestionFactory,
    UserFactory,
)
from tests.factories import DEFAULT_PASSWORD


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


@pytest.fixture
def web_objects():
    campus = CampusFactory()
    course = CourseFactory(campus=campus)
    team_user = TeamUserFactory()
    team = TeamFactory(campus=campus, users=(team_user,))
    questionnaire = QuestionnaireFactory(campus=campus)
    section = QuestionnaireSectionFactory(
        questionnaire=questionnaire,
        teams=(team,),
    )
    question = TextQuestionFactory(section=section)
    report = ReportFactory(
        campus=campus,
        course=course,
        questionnaire=questionnaire,
        assigned_team=team,
        assigned_user=None,
        status="Em andamento",
    )
    return {
        "campus": campus,
        "course": course,
        "type_course": course.type_course,
        "team_user": team_user,
        "team": team,
        "other_user": UserFactory(),
        "questionnaire": questionnaire,
        "section": section,
        "question": question,
        "report": report,
        "reference_attachment": ReferenceAttachmentFactory(),
    }


def build_url(route_name, kwargs_spec, objects):
    kwargs = {
        parameter: (
            objects[value].pk if value in objects else value
        )
        for parameter, value in kwargs_spec.items()
    }
    return reverse(f"mecip:{route_name}", kwargs=kwargs)


WEB_ROUTE_CASES = (
    pytest.param("connected_index", {}, id="dashboard-raiz"),
    pytest.param("index", {}, id="index-raiz-duplicado"),
    pytest.param("login", {}, id="login"),
    pytest.param("campus", {"campus_id": "campus"}, id="campus"),
    pytest.param("create", {}, id="campus-criar"),
    pytest.param("update", {"campus_id": "campus"}, id="campus-editar"),
    pytest.param("index_course", {}, id="curso-listar"),
    pytest.param("course", {"course_id": "course"}, id="curso-detalhe"),
    pytest.param("create_course", {}, id="curso-criar"),
    pytest.param(
        "update_course",
        {"course_id": "course"},
        id="curso-editar",
    ),
    pytest.param("index_type", {}, id="tipo-listar"),
    pytest.param(
        "type_course",
        {"type_course_id": "type_course"},
        id="tipo-detalhe",
    ),
    pytest.param("create_type", {}, id="tipo-criar"),
    pytest.param(
        "update_type",
        {"type_course_id": "type_course"},
        id="tipo-editar",
    ),
    pytest.param("register", {}, id="usuario-criar"),
    pytest.param("logout", {}, id="logout"),
    pytest.param("index_report", {}, id="relatorio-listar"),
    pytest.param(
        "report",
        {"report_id": "report"},
        id="relatorio-detalhe",
    ),
    pytest.param(
        "assign_report",
        {"report_id": "report"},
        id="relatorio-atribuir",
    ),
    pytest.param(
        "view_questionnaire",
        {"report_id": "report"},
        id="relatorio-questionario",
    ),
    pytest.param(
        "answer_questionnaire",
        {"report_id": "report"},
        id="relatorio-responder",
    ),
    pytest.param(
        "advance_report_status",
        {"report_id": "report"},
        id="relatorio-avancar-status",
    ),
    pytest.param(
        "change_report_status",
        {"report_id": "report", "action": "aprovar"},
        id="relatorio-alterar-status",
    ),
    pytest.param(
        "report_pdf_download",
        {"report_id": "report"},
        id="relatorio-pdf",
    ),
    pytest.param("create_report", {}, id="relatorio-criar"),
    pytest.param(
        "create_report_params",
        {"course_id": "course", "campus_id": "campus"},
        id="relatorio-criar-parametros",
    ),
    pytest.param(
        "update_report",
        {"report_id": "report"},
        id="relatorio-editar",
    ),
    pytest.param(
        "get_campus_for_course",
        {"course_id": "type_course"},
        id="campus-por-curso",
    ),
    pytest.param(
        "get_courses_for_campus",
        {"campus_id": "campus"},
        id="curso-por-campus",
    ),
    pytest.param("dashboard", {}, id="dashboard"),
    pytest.param(
        "index_reference_attachment",
        {},
        id="anexo-referencia-listar",
    ),
    pytest.param(
        "create_reference_attachment",
        {},
        id="anexo-referencia-criar",
    ),
    pytest.param(
        "update_reference_attachment",
        {"reference_attachment_id": "reference_attachment"},
        id="anexo-referencia-editar",
    ),
    pytest.param(
        "delete_reference_attachment",
        {"reference_attachment_id": "reference_attachment"},
        id="anexo-referencia-excluir",
    ),
    pytest.param("index_team", {}, id="equipe-listar"),
    pytest.param("team", {"team_id": "team"}, id="equipe-detalhe"),
    pytest.param("create_team", {}, id="equipe-criar"),
    pytest.param(
        "update_team",
        {"team_id": "team"},
        id="equipe-editar",
    ),
    pytest.param(
        "add_user_to_team",
        {"team_id": "team"},
        id="equipe-adicionar-usuario",
    ),
    pytest.param(
        "remove_user_from_team",
        {"team_id": "team", "user_id": "team_user"},
        id="equipe-remover-usuario",
    ),
    pytest.param(
        "index_questionnaire",
        {},
        id="questionario-listar",
    ),
    pytest.param(
        "questionnaire",
        {"questionnaire_id": "questionnaire"},
        id="questionario-detalhe",
    ),
    pytest.param(
        "create_questionnaire",
        {},
        id="questionario-criar",
    ),
    pytest.param(
        "update_questionnaire",
        {"questionnaire_id": "questionnaire"},
        id="questionario-editar",
    ),
    pytest.param(
        "create_questionnaire_section",
        {"questionnaire_id": "questionnaire"},
        id="secao-criar",
    ),
    pytest.param(
        "update_questionnaire_section",
        {
            "questionnaire_id": "questionnaire",
            "section_id": "section",
        },
        id="secao-editar",
    ),
    pytest.param(
        "delete_questionnaire_section",
        {
            "questionnaire_id": "questionnaire",
            "section_id": "section",
        },
        id="secao-excluir",
    ),
    pytest.param(
        "create_question",
        {"questionnaire_id": "questionnaire"},
        id="pergunta-criar",
    ),
    pytest.param(
        "update_question",
        {
            "questionnaire_id": "questionnaire",
            "question_id": "question",
        },
        id="pergunta-editar",
    ),
    pytest.param(
        "delete_question",
        {
            "questionnaire_id": "questionnaire",
            "question_id": "question",
        },
        id="pergunta-excluir",
    ),
)


@pytest.mark.parametrize(
    ("route_name", "kwargs_spec"),
    WEB_ROUTE_CASES,
)
def test_matriz_anonima_protege_todas_as_rotas_web(
    client,
    web_objects,
    route_name,
    kwargs_spec,
):
    url = build_url(route_name, kwargs_spec, web_objects)

    response = client.get(url)

    if route_name == "login":
        assert response.status_code == 200
        assert "mecip/login.html" in [
            template.name for template in response.templates
        ]
    else:
        assert response.status_code == 302
        assert response.url.startswith("/login/?next=")


AUTHENTICATED_TEMPLATE_CASES = (
    pytest.param(
        "connected_index", {}, "mecip/dashboard.html", "reports",
        id="dashboard-raiz",
    ),
    pytest.param(
        "dashboard", {}, "mecip/dashboard.html", "reports",
        id="dashboard",
    ),
    pytest.param(
        "campus", {"campus_id": "campus"}, "mecip/campus.html",
        "campus", id="campus",
    ),
    pytest.param(
        "index_course", {}, "mecip/index_course.html", "page_obj",
        id="curso-listar",
    ),
    pytest.param(
        "course", {"course_id": "course"}, "mecip/course.html",
        "course", id="curso-detalhe",
    ),
    pytest.param(
        "index_type", {}, "mecip/index_type_course.html", "page_obj",
        id="tipo-listar",
    ),
    pytest.param(
        "type_course", {"type_course_id": "type_course"},
        "mecip/type.html", "type_course", id="tipo-detalhe",
    ),
    pytest.param(
        "index_report", {}, "mecip/index_report.html", "page_obj",
        id="relatorio-listar",
    ),
    pytest.param(
        "report", {"report_id": "report"}, "mecip/report.html",
        "report", id="relatorio-detalhe",
    ),
    pytest.param(
        "index_team", {}, "mecip/index_team.html", "page_obj",
        id="equipe-listar",
    ),
    pytest.param(
        "team", {"team_id": "team"}, "mecip/team.html",
        "team", id="equipe-detalhe",
    ),
    pytest.param(
        "index_questionnaire", {},
        "mecip/index_questionnaire.html", "page_obj",
        id="questionario-listar",
    ),
    pytest.param(
        "questionnaire", {"questionnaire_id": "questionnaire"},
        "mecip/questionnaire.html", "questionnaire",
        id="questionario-detalhe",
    ),
    pytest.param(
        "view_questionnaire", {"report_id": "report"},
        "mecip/view_questionnaire.html", "answers",
        id="questionario-visualizar",
    ),
    pytest.param(
        "answer_questionnaire", {"report_id": "report"},
        "mecip/answer_questionnaire.html", "answer",
        id="questionario-responder",
    ),
)


@pytest.mark.parametrize(
    ("route_name", "kwargs_spec", "template_name", "context_key"),
    AUTHENTICATED_TEMPLATE_CASES,
)
def test_rotas_autenticadas_renderizam_template_e_contexto(
    client,
    web_objects,
    route_name,
    kwargs_spec,
    template_name,
    context_key,
):
    client.force_login(web_objects["team_user"])

    response = client.get(
        build_url(route_name, kwargs_spec, web_objects)
    )

    assert response.status_code == 200
    assert template_name in [template.name for template in response.templates]
    assert context_key in response.context


MANAGEMENT_GET_CASES = (
    pytest.param("create", {}, "mecip/create.html", id="campus-criar"),
    pytest.param(
        "update", {"campus_id": "campus"}, "mecip/create.html",
        id="campus-editar",
    ),
    pytest.param(
        "create_course", {}, "mecip/create.html", id="curso-criar",
    ),
    pytest.param(
        "update_course", {"course_id": "course"}, "mecip/create.html",
        id="curso-editar",
    ),
    pytest.param(
        "create_type", {}, "mecip/create.html", id="tipo-criar",
    ),
    pytest.param(
        "update_type", {"type_course_id": "type_course"},
        "mecip/create.html", id="tipo-editar",
    ),
    pytest.param(
        "create_report", {}, "mecip/create.html", id="relatorio-criar",
    ),
    pytest.param(
        "create_report_params",
        {"course_id": "course", "campus_id": "campus"},
        "mecip/create.html", id="relatorio-criar-parametros",
    ),
    pytest.param(
        "update_report", {"report_id": "report"},
        "mecip/create.html", id="relatorio-editar",
    ),
    pytest.param(
        "index_reference_attachment", {},
        "mecip/index_reference_attachment.html",
        id="anexo-listar",
    ),
    pytest.param(
        "create_reference_attachment", {},
        "mecip/reference_attachment_form.html",
        id="anexo-criar",
    ),
    pytest.param(
        "update_reference_attachment",
        {"reference_attachment_id": "reference_attachment"},
        "mecip/reference_attachment_form.html",
        id="anexo-editar",
    ),
    pytest.param(
        "create_team", {}, "mecip/create.html", id="equipe-criar",
    ),
    pytest.param(
        "update_team", {"team_id": "team"}, "mecip/create.html",
        id="equipe-editar",
    ),
    pytest.param(
        "add_user_to_team", {"team_id": "team"},
        "mecip/add_user_to_team.html", id="equipe-adicionar",
    ),
    pytest.param(
        "remove_user_from_team",
        {"team_id": "team", "user_id": "team_user"},
        "mecip/remove_user_to_team.html", id="equipe-remover",
    ),
    pytest.param(
        "create_questionnaire", {}, "mecip/create.html",
        id="questionario-criar",
    ),
    pytest.param(
        "update_questionnaire",
        {"questionnaire_id": "questionnaire"},
        "mecip/update_questionnaire.html",
        id="questionario-editar",
    ),
    pytest.param(
        "create_questionnaire_section",
        {"questionnaire_id": "questionnaire"},
        "mecip/create.html", id="secao-criar",
    ),
    pytest.param(
        "update_questionnaire_section",
        {
            "questionnaire_id": "questionnaire",
            "section_id": "section",
        },
        "mecip/create.html", id="secao-editar",
    ),
    pytest.param(
        "create_question",
        {"questionnaire_id": "questionnaire"},
        "mecip/create_question.html", id="pergunta-criar",
    ),
    pytest.param(
        "update_question",
        {
            "questionnaire_id": "questionnaire",
            "question_id": "question",
        },
        "mecip/create_question.html", id="pergunta-editar",
    ),
)


@pytest.mark.parametrize(
    ("route_name", "kwargs_spec", "template_name"),
    MANAGEMENT_GET_CASES,
)
def test_coordenador_acessa_rotas_de_gestao(
    client,
    coordinator,
    web_objects,
    route_name,
    kwargs_spec,
    template_name,
):
    client.force_login(coordinator)

    response = client.get(
        build_url(route_name, kwargs_spec, web_objects)
    )

    assert response.status_code == 200
    assert template_name in [template.name for template in response.templates]


@pytest.mark.parametrize(
    ("route_name", "kwargs_spec", "_template_name"),
    MANAGEMENT_GET_CASES,
)
def test_equipe_recebe_acesso_negado_nas_rotas_de_gestao(
    client,
    web_objects,
    route_name,
    kwargs_spec,
    _template_name,
):
    client.force_login(web_objects["team_user"])

    response = client.get(
        build_url(route_name, kwargs_spec, web_objects)
    )

    assert response.status_code == 403
    assert "mecip/access_denied.html" in [
        template.name for template in response.templates
    ]


def test_apenas_superadmin_acessa_cadastro_de_usuario(
    client,
    superadmin,
    coordinator,
):
    client.force_login(superadmin)
    response = client.get(reverse("mecip:register"))
    assert response.status_code == 200
    assert "mecip/register.html" in [
        template.name for template in response.templates
    ]

    client.force_login(coordinator)
    response = client.get(reverse("mecip:register"))
    assert response.status_code == 403


def test_login_valido_cria_sessao_e_logout_a_remove(
    client,
    team_user,
):
    response = client.post(
        reverse("mecip:login"),
        {
            "username": team_user.username,
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("mecip:connected_index")
    assert str(team_user.pk) == client.session[SESSION_KEY]

    response = client.get(reverse("mecip:logout"))

    assert response.status_code == 302
    assert response.url == reverse("mecip:login")
    assert SESSION_KEY not in client.session


def test_login_invalido_exibe_mensagem_de_erro(client, team_user):
    response = client.post(
        reverse("mecip:login"),
        {
            "username": team_user.username,
            "password": "senha-incorreta",
        },
    )

    assert response.status_code == 200
    assert "mecip/login.html" in [
        template.name for template in response.templates
    ]
    assert "Login inválido" in response.content.decode()


def test_equipe_nao_acessa_detalhe_de_outra_equipe(
    client,
    team_user,
):
    other_team = TeamFactory()
    client.force_login(team_user)

    response = client.get(
        reverse("mecip:team", args=(other_team.id,))
    )

    assert response.status_code == 404


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A segunda rota vazia, destinada ao index de Campus, fica "
        "sombreada pela rota anterior do dashboard."
    ),
)
def test_rota_index_renderiza_listagem_de_campus(
    client,
    coordinator,
):
    CampusFactory.create_batch(11)
    client.force_login(coordinator)

    response = client.get(reverse("mecip:index"), {"page": 2})

    assert response.status_code == 200
    assert "mecip/index.html" in [
        template.name for template in response.templates
    ]
    assert response.context["page_obj"].number == 2


PAGINATED_LIST_CASES = (
    pytest.param(CourseFactory, "index_course", id="cursos"),
    pytest.param(CourseTypeFactory, "index_type", id="tipos"),
    pytest.param(ReportFactory, "index_report", id="relatorios"),
    pytest.param(TeamFactory, "index_team", id="equipes"),
    pytest.param(
        QuestionnaireFactory,
        "index_questionnaire",
        id="questionarios",
    ),
    pytest.param(
        ReferenceAttachmentFactory,
        "index_reference_attachment",
        id="anexos-referencia",
    ),
)


@pytest.mark.parametrize(
    ("factory", "route_name"),
    PAGINATED_LIST_CASES,
)
def test_listagens_web_paginam_dez_registros(
    client,
    coordinator,
    factory,
    route_name,
):
    factory.create_batch(11)
    client.force_login(coordinator)

    response = client.get(
        reverse(f"mecip:{route_name}"),
        {"page": 2},
    )

    assert response.status_code == 200
    assert response.context["page_obj"].number == 2
    assert len(response.context["page_obj"]) == 1
