"""Estado de sessão do CodeRank (por aba do navegador ou por processo local)."""

from __future__ import annotations

import json

_STORAGE_KEY = "coderank.session"


class Session:
    access_token: str | None = None
    refresh_token: str | None = None
    user: dict | None = None
    profile: dict | None = None

    # Navegação entre telas
    selected_problem: str | None = None
    selected_group: int | None = None

    @property
    def logged_in(self) -> bool:
        return bool(self.access_token)


session = Session()


def _storage():
    """localStorage do navegador (build web/Pyodide); None fora do navegador."""
    try:
        import js  # type: ignore

        return js.localStorage
    except Exception:  # noqa: BLE001
        return None


def start_session(data: dict) -> None:
    session.access_token = data.get("access_token")
    session.refresh_token = data.get("refresh_token", session.refresh_token)
    session.user = data.get("user") or session.user
    if data.get("profile"):
        session.profile = data["profile"]
    save_session()


def save_session() -> None:
    storage = _storage()
    if storage is None:
        return
    try:
        storage.setItem(
            _STORAGE_KEY,
            json.dumps(
                {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "user": session.user,
                    "profile": session.profile,
                }
            ),
        )
    except Exception:  # noqa: BLE001
        pass


def load_session() -> bool:
    storage = _storage()
    if storage is None:
        return False
    try:
        raw = storage.getItem(_STORAGE_KEY)
        if not raw:
            return False
        data = json.loads(str(raw))
    except Exception:  # noqa: BLE001
        return False
    session.access_token = data.get("access_token")
    session.refresh_token = data.get("refresh_token")
    session.user = data.get("user")
    session.profile = data.get("profile")
    return session.logged_in


def clear_session() -> None:
    session.access_token = None
    session.refresh_token = None
    session.user = None
    session.profile = None
    session.selected_problem = None
    session.selected_group = None
    storage = _storage()
    if storage is not None:
        try:
            storage.removeItem(_STORAGE_KEY)
        except Exception:  # noqa: BLE001
            pass
