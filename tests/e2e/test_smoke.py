import pytest

from tests.e2e.pages import DashboardPage


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.django_db(transaction=True),
]


def test_smoke_abre_aplicacao_e_carrega_estaticos_locais(
    team_page,
    e2e_base_url,
    browser_diagnostics,
):
    DashboardPage(team_page, e2e_base_url).assert_loaded()

    assert (
        browser_diagnostics.local_assets[
            "/static/global/css/style.css"
        ]
        == 200
    )
    assert (
        browser_diagnostics.local_assets[
            "/static/mecip/js/dashboard.js"
        ]
        == 200
    )
    assert browser_diagnostics.external_requests
    assert all(
        request_url.startswith("https://")
        for request_url in browser_diagnostics.external_requests
    )
    assert browser_diagnostics.javascript_errors == []
