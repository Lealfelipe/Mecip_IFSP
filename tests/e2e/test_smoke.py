import pytest
from playwright.sync_api import expect

from tests.e2e.pages import DashboardPage


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.django_db(transaction=True),
]


def test_smoke_abre_aplicacao_e_carrega_estaticos_locais(
    report,
    team_page,
    e2e_base_url,
    browser_diagnostics,
):
    DashboardPage(team_page, e2e_base_url).assert_loaded()

    expect(team_page.locator("#statusChart")).to_be_visible()
    chart_ready = team_page.wait_for_function(
        """
        () => {
            const canvas = document.getElementById("statusChart");
            const chart = window.Chart?.getChart(canvas);
            return Boolean(chart?.data.datasets[0].data.length);
        }
        """
    )
    assert chart_ready.json_value() is True

    font_loaded = team_page.evaluate(
        """
        async () => {
            const fonts = await document.fonts.load(
                '16px "uicons-solid-rounded"'
            );
            return fonts.length > 0;
        }
        """
    )
    assert font_loaded is True

    expected_assets = (
        "/static/global/css/style.css",
        "/static/mecip/js/dashboard.js",
        "/static/vendor/chart.js/4.5.1/chart.umd.min.js",
        (
            "/static/vendor/flaticon-uicons/4.0.0/"
            "css/uicons-solid-rounded.css"
        ),
        (
            "/static/vendor/flaticon-uicons/4.0.0/"
            "webfonts/uicons-solid-rounded.woff2"
        ),
        (
            "/static/vendor/tom-select/2.6.2/"
            "tom-select.bootstrap5.min.css"
        ),
    )
    for asset_path in expected_assets:
        assert browser_diagnostics.local_assets[asset_path] == 200

    assert browser_diagnostics.external_requests == []
    assert browser_diagnostics.javascript_errors == []


def test_tom_select_carrega_localmente_sem_rede_externa(
    team,
    coordinator_page,
    e2e_base_url,
    browser_diagnostics,
):
    response = coordinator_page.goto(
        f"{e2e_base_url}/equipe/{team.id}/adicionar-usuario/",
        wait_until="domcontentloaded",
    )

    assert response is not None
    assert response.ok
    expect(coordinator_page.locator(".ts-wrapper")).to_be_visible()
    assert coordinator_page.evaluate(
        "() => typeof window.TomSelect === 'function'"
    )
    assert (
        browser_diagnostics.local_assets[
            (
                "/static/vendor/tom-select/2.6.2/"
                "tom-select.complete.min.js"
            )
        ]
        == 200
    )
    assert browser_diagnostics.external_requests == []
    assert browser_diagnostics.javascript_errors == []
