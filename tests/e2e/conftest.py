from collections.abc import Iterator
from dataclasses import dataclass, field
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page, Response, Route, sync_playwright

from tests.e2e.pages import DashboardPage, LoginPage
from tests.factories import DEFAULT_PASSWORD


@pytest.fixture
def playwright():
    with sync_playwright() as playwright_instance:
        yield playwright_instance


@pytest.fixture
def browser(
    playwright,
    browser_name,
    browser_type_launch_args,
) -> Iterator[Browser]:
    browser_type = getattr(playwright, browser_name)
    browser_instance = browser_type.launch(**browser_type_launch_args)
    yield browser_instance
    browser_instance.close()


@dataclass
class BrowserDiagnostics:
    javascript_errors: list[str] = field(default_factory=list)
    external_requests: list[str] = field(default_factory=list)
    local_assets: dict[str, int] = field(default_factory=dict)


@pytest.fixture
def browser_context_args():
    return {
        "accept_downloads": True,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        "viewport": {
            "width": 1440,
            "height": 900,
        },
    }


@pytest.fixture
def e2e_base_url(live_server) -> str:
    return live_server.url


@pytest.fixture
def browser_diagnostics(
    page: Page,
    live_server,
) -> Iterator[BrowserDiagnostics]:
    diagnostics = BrowserDiagnostics()
    local_origin = urlparse(live_server.url).netloc

    def handle_route(route: Route):
        request_url = route.request.url
        parsed_url = urlparse(request_url)
        is_network_request = parsed_url.scheme in ("http", "https")

        if is_network_request and parsed_url.netloc != local_origin:
            diagnostics.external_requests.append(request_url)
            route.abort()
            return

        route.continue_()

    def record_response(response: Response):
        parsed_url = urlparse(response.url)
        if parsed_url.path.startswith("/static/"):
            diagnostics.local_assets[parsed_url.path] = response.status

    page.route("**/*", handle_route)
    page.on(
        "pageerror",
        lambda error: diagnostics.javascript_errors.append(str(error)),
    )
    page.on("response", record_response)

    yield diagnostics

    assert diagnostics.javascript_errors == []


def login_as(page: Page, base_url: str, user):
    login_page = LoginPage(page, base_url)
    login_page.open()
    login_page.login(user.username, DEFAULT_PASSWORD)
    DashboardPage(page, base_url).assert_loaded()
    return page


@pytest.fixture
def team_page(
    team_user,
    browser_diagnostics,
    page,
    e2e_base_url,
):
    return login_as(page, e2e_base_url, team_user)


@pytest.fixture
def coordinator_page(
    coordinator,
    browser_diagnostics,
    page,
    e2e_base_url,
):
    return login_as(page, e2e_base_url, coordinator)


@pytest.fixture
def superadmin_page(
    superadmin,
    browser_diagnostics,
    page,
    e2e_base_url,
):
    return login_as(page, e2e_base_url, superadmin)
