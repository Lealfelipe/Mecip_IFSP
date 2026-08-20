from playwright.sync_api import Page, expect


class DashboardPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.url = f"{base_url}/dashboard/"

    def open(self):
        response = self.page.goto(
            self.url,
            wait_until="domcontentloaded",
        )
        assert response is not None
        assert response.ok
        self.assert_loaded()

    def assert_loaded(self):
        expect(
            self.page.get_by_role(
                "heading",
                name="Painel de Relatórios",
            )
        ).to_be_visible()

    def apply_filters(self, campus: str, team: str):
        comboboxes = self.page.get_by_role("combobox")
        comboboxes.nth(0).select_option(label=campus)
        comboboxes.nth(1).select_option(label=team)
        self.page.get_by_role(
            "button",
            name="Aplicar filtro",
        ).click()
