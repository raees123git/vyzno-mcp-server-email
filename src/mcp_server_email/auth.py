from mcp_server_email.config import Settings


def build_vyzno_auth_headers(settings: Settings) -> dict[str, str]:
    return {
        "Cookie": settings.vyzno_cookie_header.get_secret_value(),
        "X-CSRF-Token": settings.vyzno_csrf_token.get_secret_value(),
        "Origin": settings.vyzno_origin,
    }