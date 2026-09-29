"""Estado compartilhado entre as telas do aplicativo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.services.backend import AuthSession, DemoBackend, SupabaseBackend


@dataclass
class AppState:
    backend: DemoBackend | SupabaseBackend
    session: AuthSession | None = None
    selected_group_id: str | None = None
    selected_challenge_id: str | None = None

    @property
    def authenticated(self) -> bool:
        return self.session is not None


def get_state(page: Any) -> AppState:
    state = getattr(page, "data", None)
    if not isinstance(state, AppState):
        raise RuntimeError("Estado do CodeRank nao foi inicializado.")
    return state
