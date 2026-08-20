import re

from playwright.sync_api import Page, expect


class ReportPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self, report_id: int):
        response = self.page.goto(
            f"{self.base_url}/relatorio/{report_id}/",
            wait_until="domcontentloaded",
        )
        assert response is not None
        assert response.ok
        self.assert_loaded()

    def assert_loaded(self):
        expect(
            self.page.get_by_role(
                "heading",
                name=re.compile(r"^Relatorio:"),
            )
        ).to_be_visible()

    def assign_to_me(self):
        self.page.get_by_role(
            "button",
            name="Atribuir a mim",
        ).click()

    def open_questionnaire(self):
        self.page.get_by_role(
            "button",
            name="Ver Questionário",
        ).click()
