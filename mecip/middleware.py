from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url


class LoginRequiredMiddleware:
    """Exige autenticação para todas as páginas da aplicação."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = resolve_url(settings.LOGIN_URL)
        static_url = f"/{settings.STATIC_URL.lstrip('/')}"

        is_public_request = (
            request.path_info == login_url
            or request.path_info.startswith('/api/v1/')
            or request.path_info.startswith('/a/r/')
            or request.path_info.startswith('/a/d/')
            or request.path_info.startswith('/anexos/publicos/')
            or request.path_info.startswith(static_url)
        )

        if request.user.is_authenticated or is_public_request:
            return self.get_response(request)

        return redirect_to_login(
            request.get_full_path(),
            login_url=login_url,
        )
