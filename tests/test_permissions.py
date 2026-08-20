import pytest
from django.contrib.auth.models import AnonymousUser, Group
from rest_framework import status

from mecip.permissions import (
    ROLE_COORDENADOR,
    ROLE_EQUIPE,
    ROLE_SUPERADMIN,
    USER_ROLE_NAMES,
    access_required,
    assign_role,
    can_answer_report,
    can_manage_records,
    can_manage_users,
    can_view_all_records,
    can_view_report_questionnaire,
    is_coordinator,
    is_superadmin,
    is_team_user,
    user_belongs_to_report_team,
    user_has_role,
)
from tests.factories import (
    CoordinatorFactory,
    SuperAdminFactory,
    TeamUserFactory,
)


pytestmark = pytest.mark.django_db


@pytest.mark.api
def test_usuario_sem_token_recebe_401_ao_listar_campus(api_client):
    response = api_client.get("/api/v1/campus/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
def test_equipe_lista_campus_mas_nao_pode_criar(
    authenticate_api_client,
    team_user,
    campus,
):
    client = authenticate_api_client(team_user)

    assert (
        client.get("/api/v1/campus/").status_code
        == status.HTTP_200_OK
    )

    response = client.post(
        "/api/v1/campus/",
        {
            "campus_name": "Novo",
            "city": "Cidade",
            "street": "Rua",
            "neighborhood": "Bairro",
            "number": "10",
            "contact_number": "1100000000",
            "email_campus": "novo@example.com",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
def test_coordenador_cria_e_atualiza_campus(
    authenticate_api_client,
    coordinator,
):
    client = authenticate_api_client(coordinator)

    response = client.post(
        "/api/v1/campus/",
        {
            "campus_name": "Campus Norte",
            "city": "Cidade",
            "street": "Rua",
            "neighborhood": "Bairro",
            "number": "10",
            "contact_number": "1100000000",
            "email_campus": "norte@example.com",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.patch(
        f"/api/v1/campus/{response.data['id']}/",
        {"city": "Outra"},
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
def test_superadmin_cria_e_atualiza_questionario(
    authenticate_api_client,
    superadmin,
    campus,
):
    client = authenticate_api_client(superadmin)

    response = client.post(
        "/api/v1/questionarios/",
        {
            "name": "Novo Questionario",
            "description": "Descricao",
            "campus": campus.id,
            "active": True,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.patch(
        f"/api/v1/questionarios/{response.data['id']}/",
        {"active": False},
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
def test_equipe_nao_responde_questionario_de_outra_equipe(
    authenticate_api_client,
    questionnaire,
    report,
    text_question,
):
    unrelated_user = TeamUserFactory()
    client = authenticate_api_client(unrelated_user)

    response = client.post(
        f"/api/v1/questionarios/{questionnaire.id}/responder/",
        {
            "report": report.id,
            "question": text_question.id,
            "answer": "Resposta indevida",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
def test_equipe_nao_pode_importar_questionario(
    authenticate_api_client,
    team_user,
):
    client = authenticate_api_client(team_user)

    response = client.post(
        "/api/v1/questionarios/importar/",
        {
            "questionario": "Bloqueado",
            "dimensao": "DIMENSAO",
            "questao": "Pergunta",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


ROLE_PERMISSION_CASES = (
    pytest.param(
        TeamUserFactory,
        (True, False, False, False, False, False),
        id="equipe",
    ),
    pytest.param(
        CoordinatorFactory,
        (False, True, False, True, False, True),
        id="coordenador",
    ),
    pytest.param(
        SuperAdminFactory,
        (False, False, True, True, True, True),
        id="superadmin",
    ),
    pytest.param(
        None,
        (False, False, False, False, False, False),
        id="anonimo",
    ),
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("user_factory", "expected"),
    ROLE_PERMISSION_CASES,
)
def test_matriz_de_papeis_aplica_permissoes_corretas(
    user_factory,
    expected,
):
    user = user_factory() if user_factory else AnonymousUser()

    actual = (
        is_team_user(user),
        is_coordinator(user),
        is_superadmin(user),
        can_manage_records(user),
        can_manage_users(user),
        can_view_all_records(user),
    )

    assert actual == expected


REPORT_PERMISSION_CASES = (
    pytest.param(
        TeamUserFactory,
        True,
        True,
        True,
        id="equipe-membro",
    ),
    pytest.param(
        TeamUserFactory,
        False,
        False,
        False,
        id="equipe-nao-membro",
    ),
    pytest.param(
        CoordinatorFactory,
        False,
        False,
        True,
        id="coordenador",
    ),
    pytest.param(
        SuperAdminFactory,
        False,
        False,
        True,
        id="superadmin",
    ),
    pytest.param(
        None,
        False,
        False,
        False,
        id="anonimo",
    ),
)


@pytest.mark.unit
@pytest.mark.parametrize(
    (
        "user_factory",
        "add_to_team",
        "expected_membership",
        "expected_access",
    ),
    REPORT_PERMISSION_CASES,
)
def test_matriz_de_papeis_controla_visualizacao_e_resposta(
    report,
    user_factory,
    add_to_team,
    expected_membership,
    expected_access,
):
    user = user_factory() if user_factory else AnonymousUser()
    if add_to_team:
        report.assigned_team.users.add(user)

    assert (
        user_belongs_to_report_team(user, report)
        is expected_membership
    )
    assert (
        can_view_report_questionnaire(user, report)
        is expected_access
    )
    assert can_answer_report(user, report) is expected_access


@pytest.mark.unit
def test_troca_de_papel_remove_papel_anterior_e_preserva_outros_grupos():
    user = TeamUserFactory()
    unrelated_group = Group.objects.create(name="Auditoria")
    user.groups.add(unrelated_group)

    assign_role(user, ROLE_COORDENADOR)

    assert not user_has_role(user, ROLE_EQUIPE)
    assert user_has_role(user, ROLE_COORDENADOR)
    assert set(
        user.groups.filter(name__in=USER_ROLE_NAMES).values_list(
            "name",
            flat=True,
        )
    ) == {ROLE_COORDENADOR}
    assert user.groups.filter(pk=unrelated_group.pk).exists()

    assign_role(user, ROLE_SUPERADMIN)

    assert not user_has_role(user, ROLE_COORDENADOR)
    assert user_has_role(user, ROLE_SUPERADMIN)


@pytest.mark.unit
def test_access_required_redireciona_usuario_anonimo_para_login(rf):
    protected_view = access_required(lambda user: True)(
        lambda request: None
    )
    request = rf.get("/area-restrita/")
    request.user = AnonymousUser()

    response = protected_view(request)

    assert response.status_code == 302
    assert response.url == "/login/"
