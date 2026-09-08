from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.auth.security import decode_access_token


def key_by_student_or_ip(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            return f"student:{decode_access_token(token)}"
        except Exception:
            pass  # invalid/expired token -> fall through to IP-based limiting
    return f"ip:{get_remote_address(request)}"


# One shared limiter for the whole app — main.py registers it on app.state and
# adds the SlowAPIMiddleware/exception handler; auth_routes.py (and any other
# router module) imports this same instance to decorate its own endpoints.
# This has to be a single shared instance: SlowAPIMiddleware and the
# rate-limit-exceeded handler both key off whatever limiter is registered on
# app.state, so a route decorated with a *different* Limiter wouldn't be
# enforced correctly.
limiter = Limiter(key_func=key_by_student_or_ip)