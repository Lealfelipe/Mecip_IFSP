import pytest
from django.urls import reverse

from mecip.models import Team
from tests.factories import TeamFactory, UserFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_admin_rejeita_equipe_equivalente_no_mesmo_campus(client):
    administrator = UserFactory(
        is_staff=True,
        is_superuser=True,
    )
    existing_team = TeamFactory(team_name="Équipe A")
    client.force_login(administrator)

    response = client.post(
        reverse("admin:mecip_team_add"),
        {
            "team_name": " EQUIPE A ",
            "campus": existing_team.campus_id,
            "users": [administrator.pk],
        },
    )

    assert response.status_code == 200
    assert (
        "Já existe uma equipe com este nome neste campus"
        in response.context["adminform"].form.errors["team_name"]
    )
    assert Team.objects.filter(campus=existing_team.campus).count() == 1
