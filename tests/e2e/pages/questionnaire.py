import re

from playwright.sync_api import Page, expect


class QuestionnairePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self, report_id: int):
        response = self.page.goto(
            (
                f"{self.base_url}/relatorio/{report_id}/"
                "questionario/"
            ),
            wait_until="domcontentloaded",
        )
        assert response is not None
        assert response.ok
        self.assert_loaded()

    def assert_loaded(self):
        expect(
            self.page.get_by_role(
                "heading",
                name=re.compile(r"^Questionario:"),
            )
        ).to_be_visible()

    def start_answering(self):
        self.page.get_by_role(
            "button",
            name="Responder Questionario",
        ).click()
