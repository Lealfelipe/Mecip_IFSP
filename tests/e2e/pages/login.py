from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.url = f"{base_url}/login/"

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
            self.page.get_by_role("heading", name="Entrar")
        ).to_be_visible()

    def login(self, username: str, password: str):
        self.page.get_by_label("Usuário").fill(username)
        self.page.get_by_label("Senha").fill(password)
        self.page.get_by_role("button", name="Entrar").click()
