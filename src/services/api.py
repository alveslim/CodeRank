"""Cliente da API do CodeRank (Cloudflare Worker)."""

from __future__ import annotations

import os

from src import state
from src.services.http import fetch_json

API_URL = os.environ.get(
    "CODERANK_API_URL", "https://coderank-api.seguranca-paciente.workers.dev"
).rstrip("/")


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


async def _send(method: str, path: str, body: dict | None, auth: bool):
    headers = {}
    if auth and state.session.access_token:
        headers["Authorization"] = f"Bearer {state.session.access_token}"
    return await fetch_json(method, f"{API_URL}{path}", body, headers)


async def _refresh() -> bool:
    rt = state.session.refresh_token
    if not rt:
        return False
    status, data = await fetch_json("POST", f"{API_URL}/auth/refresh", {"refresh_token": rt})
    if status == 200 and isinstance(data, dict) and data.get("access_token"):
        state.start_session(data)
        return True
    return False


async def call(method: str, path: str, body: dict | None = None, auth: bool = True) -> dict:
    status, data = await _send(method, path, body, auth)
    if status == 401 and auth and path != "/auth/login" and await _refresh():
        status, data = await _send(method, path, body, auth)
    if status == 0:
        raise ApiError(0, "Não foi possível conectar ao servidor. Verifique sua internet.")
    if 200 <= status < 300 and isinstance(data, dict):
        return data
    message = data.get("error") if isinstance(data, dict) else None
    raise ApiError(status, message or f"Erro inesperado ({status}).")


async def get(path: str, auth: bool = True) -> dict:
    return await call("GET", path, None, auth)


async def post(path: str, body: dict | None = None, auth: bool = True) -> dict:
    return await call("POST", path, body or {}, auth)


async def patch(path: str, body: dict) -> dict:
    return await call("PATCH", path, body)


# --- Autenticação ---


async def login(email: str, password: str) -> dict:
    data = await post("/auth/login", {"email": email, "password": password}, auth=False)
    state.start_session(data)
    return data


async def signup(email: str, password: str, username: str, cidade: str = "") -> dict:
    return await post(
        "/auth/signup",
        {"email": email, "password": password, "username": username, "cidade": cidade},
        auth=False,
    )


async def logout() -> None:
    try:
        await post("/auth/logout")
    except ApiError:
        pass
    state.clear_session()
