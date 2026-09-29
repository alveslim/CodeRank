"""Camada de dados do CodeRank.

O aplicativo usa Supabase quando ``SUPABASE_URL`` e ``SUPABASE_ANON_KEY``
estao definidos. Sem essas variaveis, um backend local em memoria permite
demonstrar e testar o fluxo completo sem fingir que existe conexao externa.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import secrets
import time
import uuid
from typing import Any

import requests


class BackendError(RuntimeError):
    """Erro de negocio ou comunicacao apresentado de forma amigavel na UI."""


def _mensagem_backend_amigavel(message: str | None, status_code: int) -> str:
    """Traduz erros comuns do Supabase Auth sem esconder erros desconhecidos."""

    if not message:
        return f"Falha no backend ({status_code})."
    normalized = message.casefold()
    if "email rate limit exceeded" in normalized:
        return (
            "O limite temporario de e-mails do Supabase foi atingido. "
            "Use o primeiro e-mail recebido ou aguarde a liberacao do envio."
        )
    if "for security purposes" in normalized and "request this after" in normalized:
        match = re.search(r"after\s+(\d+)\s+seconds?", normalized)
        espera = f" Aguarde {match.group(1)} segundos." if match else " Aguarde um minuto."
        return "Muitas tentativas seguidas foram detectadas." + espera
    if "user already registered" in normalized or "already been registered" in normalized:
        return "Este e-mail ja esta cadastrado. Confirme o e-mail e entre pela tela de login."
    if "email not confirmed" in normalized:
        return "Confirme seu e-mail antes de entrar. Verifique tambem a caixa de spam."
    if "invalid login credentials" in normalized:
        return "E-mail ou senha incorretos."
    if "email address" in normalized and "invalid" in normalized:
        return "Informe um endereco de e-mail valido."
    return message


@dataclass(frozen=True)
class AuthSession:
    user_id: str
    email: str
    access_token: str | None = None


class DemoBackend:
    """Backend efemero para testes locais e apresentacao sem credenciais."""

    mode = "demo"

    def __init__(self) -> None:
        self.session: AuthSession | None = None
        self._users: dict[str, dict[str, Any]] = {}
        self._groups: dict[str, dict[str, Any]] = {}
        self._members: dict[str, dict[str, int]] = {}
        self._roles: dict[str, dict[str, str]] = {}
        self._submissions: list[dict[str, Any]] = []
        self._notifications: dict[str, list[dict[str, Any]]] = {}
        self._challenges = [
            {
                "id": "demo-python-soma",
                "title": "Soma simples",
                "description": "Imprima o resultado de 2 + 3.",
                "language": "python",
                "difficulty": "Facil",
                "points": 100,
                "expected_output": "5",
            },
            {
                "id": "demo-java-soma",
                "title": "Soma simples em Java",
                "description": "Imprima o resultado de 2 + 3.",
                "language": "java",
                "difficulty": "Facil",
                "points": 100,
                "expected_output": "5",
            },
            {
                "id": "demo-python-lista",
                "title": "Maior numero",
                "description": "Imprima o maior valor da lista [3, 8, 2, 5].",
                "language": "python",
                "difficulty": "Medio",
                "points": 150,
                "expected_output": "8",
            },
        ]
        self._seed_demo()

    @staticmethod
    def _password_hash(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120_000
        ).hex()

    def _seed_demo(self) -> None:
        self.sign_up(
            "demo@coderank.local",
            "demo1234",
            {
                "name": "Usuario Demo",
                "city": "Manaus",
                "state": "AM",
                "course": "Engenharia de Software",
                "institution": "FAMETRO",
            },
        )
        group = self.create_group("Equipe CodeRank")
        self._members[group["id"]][self.session.user_id] = 300
        self.session = None

    def _require_session(self) -> AuthSession:
        if not self.session:
            raise BackendError("Faca login para continuar.")
        return self.session

    def sign_up(
        self, email: str, password: str, profile: dict[str, Any]
    ) -> AuthSession:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise BackendError("Informe um e-mail valido.")
        if len(password) < 8:
            raise BackendError("A senha deve ter no minimo 8 caracteres.")
        if email in self._users:
            raise BackendError("E-mail ja cadastrado.")

        user_id = str(uuid.uuid4())
        salt = secrets.token_hex(12)
        self._users[email] = {
            "id": user_id,
            "email": email,
            "salt": salt,
            "password_hash": self._password_hash(password, salt),
            "name": profile.get("name") or email.split("@", 1)[0],
            "cep": profile.get("cep", ""),
            "city": profile.get("city", ""),
            "state": profile.get("state", ""),
            "course": profile.get("course", "Engenharia de Software"),
            "institution": profile.get("institution", "FAMETRO"),
            "avatar_url": None,
        }
        self._notifications[user_id] = []
        self.session = AuthSession(user_id=user_id, email=email)
        return self.session

    def sign_in(self, email: str, password: str) -> AuthSession:
        email = email.strip().lower()
        user = self._users.get(email)
        if not user or self._password_hash(password, user["salt"]) != user["password_hash"]:
            raise BackendError("E-mail ou senha incorretos.")
        self.session = AuthSession(user_id=user["id"], email=email)
        return self.session

    def sign_out(self) -> None:
        self.session = None

    def list_groups(self) -> list[dict[str, Any]]:
        session = self._require_session()
        return [
            {
                **group,
                "points": self._members[group_id].get(session.user_id, 0),
                "role": self._roles[group_id].get(session.user_id, "member"),
            }
            for group_id, group in self._groups.items()
            if session.user_id in self._members[group_id]
        ]

    def create_group(self, name: str) -> dict[str, Any]:
        session = self._require_session()
        name = name.strip()
        if not 3 <= len(name) <= 30:
            raise BackendError("O nome do grupo deve ter entre 3 e 30 caracteres.")
        group_id = str(uuid.uuid4())
        invite_code = secrets.token_hex(4).upper()
        group = {
            "id": group_id,
            "name": name,
            "invite_code": invite_code,
            "owner_id": session.user_id,
        }
        self._groups[group_id] = group
        self._members[group_id] = {session.user_id: 0}
        self._roles[group_id] = {session.user_id: "owner"}
        return group

    def join_group(self, invite_code: str) -> dict[str, Any]:
        session = self._require_session()
        normalized = invite_code.strip().upper()
        for group_id, group in self._groups.items():
            if group["invite_code"] == normalized:
                self._members[group_id].setdefault(session.user_id, 0)
                self._roles[group_id].setdefault(session.user_id, "member")
                return group
        raise BackendError("Codigo de convite invalido.")

    def list_challenges(self, language: str | None = None) -> list[dict[str, Any]]:
        self._require_session()
        if not language or language == "todos":
            return list(self._challenges)
        return [item for item in self._challenges if item["language"] == language]

    def get_challenge(self, challenge_id: str) -> dict[str, Any]:
        self._require_session()
        for challenge in self._challenges:
            if challenge["id"] == challenge_id:
                return challenge
        raise BackendError("Desafio nao encontrado.")

    def get_ranking(self, group_id: str | None = None) -> list[dict[str, Any]]:
        session = self._require_session()
        if group_id is None:
            groups = self.list_groups()
            group_id = groups[0]["id"] if groups else None
        if not group_id or session.user_id not in self._members.get(group_id, {}):
            return []

        users_by_id = {item["id"]: item for item in self._users.values()}
        rows = [
            {
                "user_id": user_id,
                "name": users_by_id[user_id]["name"],
                "points": points,
            }
            for user_id, points in self._members[group_id].items()
        ]
        rows.sort(key=lambda item: (-item["points"], item["name"].lower()))
        for position, row in enumerate(rows, start=1):
            row["position"] = position
        return rows

    def list_group_members(self, group_id: str) -> list[dict[str, Any]]:
        session = self._require_session()
        if session.user_id not in self._members.get(group_id, {}):
            raise BackendError("Voce nao participa deste grupo.")
        users_by_id = {item["id"]: item for item in self._users.values()}
        rows = [
            {
                "user_id": user_id,
                "name": users_by_id[user_id]["name"],
                "email": users_by_id[user_id]["email"],
                "role": self._roles[group_id][user_id],
                "points": points,
            }
            for user_id, points in self._members[group_id].items()
        ]
        return sorted(rows, key=lambda item: (item["role"] != "owner", item["name"].lower()))

    def remove_group_member(self, group_id: str, user_id: str) -> None:
        session = self._require_session()
        current_role = self._roles.get(group_id, {}).get(session.user_id)
        target_role = self._roles.get(group_id, {}).get(user_id)
        if current_role not in {"owner", "admin"}:
            raise BackendError("Somente administradores podem remover membros.")
        if target_role == "owner" or user_id == session.user_id:
            raise BackendError("O proprietario nao pode ser removido do grupo.")
        if current_role == "admin" and target_role == "admin":
            raise BackendError("Um administrador nao pode remover outro administrador.")
        if target_role is None:
            raise BackendError("Membro nao encontrado.")
        del self._members[group_id][user_id]
        del self._roles[group_id][user_id]

    def get_profile(self) -> dict[str, Any]:
        session = self._require_session()
        user = next(item for item in self._users.values() if item["id"] == session.user_id)
        points = sum(members.get(session.user_id, 0) for members in self._members.values())
        solved = {
            item["challenge_id"]
            for item in self._submissions
            if item["user_id"] == session.user_id and item["correct"]
        }
        return {
            key: value
            for key, value in user.items()
            if key not in {"salt", "password_hash"}
        } | {"points": points, "solved_count": len(solved)}

    def update_profile(self, changes: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session()
        user = next(item for item in self._users.values() if item["id"] == session.user_id)
        name = str(changes.get("name", user["name"])).strip()
        if not 2 <= len(name) <= 80:
            raise BackendError("O nome deve ter entre 2 e 80 caracteres.")
        for field in {"name", "cep", "city", "state", "course", "institution", "avatar_url"}:
            if field in changes:
                user[field] = changes[field]
        user["name"] = name
        return self.get_profile()

    def list_submission_history(self, limit: int = 10) -> list[dict[str, Any]]:
        session = self._require_session()
        challenges = {item["id"]: item for item in self._challenges}
        rows = [
            {
                **item,
                "challenge_title": challenges[item["challenge_id"]]["title"],
                "points": challenges[item["challenge_id"]]["points"] if item["correct"] else 0,
            }
            for item in reversed(self._submissions)
            if item["user_id"] == session.user_id
        ]
        return rows[:limit]

    def list_notifications(self, limit: int = 10) -> list[dict[str, Any]]:
        session = self._require_session()
        return list(reversed(self._notifications.get(session.user_id, [])))[:limit]

    def record_submission(
        self,
        challenge_id: str,
        group_id: str | None,
        language: str,
        source_code: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        correct: bool,
        execution_ms: int,
    ) -> dict[str, Any]:
        session = self._require_session()
        challenge = self.get_challenge(challenge_id)
        already_solved = any(
            item["user_id"] == session.user_id
            and item["challenge_id"] == challenge_id
            and item["group_id"] == group_id
            and item["correct"]
            for item in self._submissions
        )
        awarded = challenge["points"] if correct and not already_solved else 0
        self._submissions.append(
            {
                "user_id": session.user_id,
                "challenge_id": challenge_id,
                "group_id": group_id,
                "language": language,
                "source_code": source_code,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "correct": correct,
                "execution_ms": execution_ms,
                "created_at": time.time(),
            }
        )
        if awarded and group_id in self._members:
            self._members[group_id][session.user_id] += awarded
            self._notifications[session.user_id].append(
                {
                    "id": str(uuid.uuid4()),
                    "message": f"Voce ganhou {awarded} pontos em {challenge['title']}.",
                    "read": False,
                    "created_at": time.time(),
                }
            )
        return {"accepted": correct, "points_awarded": awarded}


class SupabaseBackend:
    """Cliente REST minimo para Supabase Auth, PostgREST e funcoes RPC."""

    mode = "supabase"

    def __init__(self, url: str, anon_key: str) -> None:
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.session: AuthSession | None = None

    def _headers(self, *, prefer: str | None = None) -> dict[str, str]:
        token = self.session.access_token if self.session else self.anon_key
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        prefer: str | None = None,
    ) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.url}{path}",
                headers=self._headers(prefer=prefer),
                json=json,
                params=params,
                timeout=12,
            )
        except requests.RequestException as exc:
            raise BackendError("Nao foi possivel conectar ao Supabase.") from exc

        if response.status_code >= 400:
            try:
                payload = response.json()
                message = (
                    payload.get("msg")
                    or payload.get("message")
                    or payload.get("error_description")
                    or payload.get("error")
                )
            except ValueError:
                message = None
            raise BackendError(
                _mensagem_backend_amigavel(message, response.status_code)
            )
        if not response.content:
            return None
        return response.json()

    def _require_session(self) -> AuthSession:
        if not self.session:
            raise BackendError("Faca login para continuar.")
        return self.session

    def sign_up(
        self, email: str, password: str, profile: dict[str, Any]
    ) -> AuthSession | None:
        payload = self._request(
            "POST",
            "/auth/v1/signup",
            json={"email": email.strip(), "password": password, "data": profile},
        )
        user = payload.get("user") or {}
        token = payload.get("access_token")
        if not token:
            return None
        self.session = AuthSession(user["id"], user.get("email", email), token)
        return self.session

    def sign_in(self, email: str, password: str) -> AuthSession:
        payload = self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email.strip(), "password": password},
        )
        user = payload["user"]
        self.session = AuthSession(user["id"], user["email"], payload["access_token"])
        return self.session

    def sign_out(self) -> None:
        if self.session:
            self._request("POST", "/auth/v1/logout")
        self.session = None

    def list_groups(self) -> list[dict[str, Any]]:
        session = self._require_session()
        rows = self._request(
            "GET",
            "/rest/v1/group_members",
            params={
                "select": "role,points,groups(id,name,invite_code,owner_id,created_at)",
                "user_id": f"eq.{session.user_id}",
                "order": "joined_at.asc",
            },
        )
        return [{**row["groups"], "role": row["role"], "points": row["points"]} for row in rows]

    def create_group(self, name: str) -> dict[str, Any]:
        self._require_session()
        return self._request("POST", "/rest/v1/rpc/create_group", json={"p_name": name})[0]

    def join_group(self, invite_code: str) -> dict[str, Any]:
        self._require_session()
        return self._request(
            "POST", "/rest/v1/rpc/join_group", json={"p_invite_code": invite_code}
        )[0]

    def list_challenges(self, language: str | None = None) -> list[dict[str, Any]]:
        self._require_session()
        params = {
            "select": "id,title,description,language,difficulty,points,expected_output",
            "active": "eq.true",
            "order": "title.asc",
        }
        if language and language != "todos":
            params["language"] = f"in.({language},any)"
        return self._request("GET", "/rest/v1/challenges", params=params)

    def get_challenge(self, challenge_id: str) -> dict[str, Any]:
        rows = self._request(
            "GET",
            "/rest/v1/challenges",
            params={"select": "*", "id": f"eq.{challenge_id}", "limit": "1"},
        )
        if not rows:
            raise BackendError("Desafio nao encontrado.")
        return rows[0]

    def get_ranking(self, group_id: str | None = None) -> list[dict[str, Any]]:
        self._require_session()
        if not group_id:
            groups = self.list_groups()
            group_id = groups[0]["id"] if groups else None
        if not group_id:
            return []
        return self._request(
            "POST", "/rest/v1/rpc/get_group_ranking", json={"p_group_id": group_id}
        )

    def list_group_members(self, group_id: str) -> list[dict[str, Any]]:
        self._require_session()
        rows = self._request(
            "GET",
            "/rest/v1/group_members",
            params={
                "select": "user_id,role,points,profiles(name,email)",
                "group_id": f"eq.{group_id}",
                "order": "points.desc",
            },
        )
        return [
            {
                "user_id": row["user_id"],
                "role": row["role"],
                "points": row["points"],
                "name": row["profiles"]["name"],
                "email": row["profiles"]["email"],
            }
            for row in rows
        ]

    def remove_group_member(self, group_id: str, user_id: str) -> None:
        self._require_session()
        self._request(
            "POST",
            "/rest/v1/rpc/remove_group_member",
            json={"p_group_id": group_id, "p_user_id": user_id},
        )

    def get_profile(self) -> dict[str, Any]:
        session = self._require_session()
        rows = self._request(
            "GET",
            "/rest/v1/profiles",
            params={"select": "*", "id": f"eq.{session.user_id}", "limit": "1"},
        )
        if not rows:
            raise BackendError("Perfil nao encontrado.")
        profile = rows[0]
        profile["points"] = sum(group.get("points", 0) for group in self.list_groups())
        solved = self._request(
            "GET",
            "/rest/v1/submissions",
            params={
                "select": "challenge_id",
                "user_id": f"eq.{session.user_id}",
                "correct": "eq.true",
            },
        )
        profile["solved_count"] = len({item["challenge_id"] for item in solved})
        return profile

    def update_profile(self, changes: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session()
        allowed = {"name", "cep", "city", "state", "course", "institution", "avatar_url"}
        payload = {key: value for key, value in changes.items() if key in allowed}
        payload["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows = self._request(
            "PATCH",
            "/rest/v1/profiles",
            params={"id": f"eq.{session.user_id}"},
            json=payload,
            prefer="return=representation",
        )
        if not rows:
            raise BackendError("Nao foi possivel atualizar o perfil.")
        return rows[0]

    def list_submission_history(self, limit: int = 10) -> list[dict[str, Any]]:
        session = self._require_session()
        rows = self._request(
            "GET",
            "/rest/v1/submissions",
            params={
                "select": "id,correct,language,exit_code,execution_ms,created_at,challenges(title,points)",
                "user_id": f"eq.{session.user_id}",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )
        return [
            {
                **row,
                "challenge_title": row["challenges"]["title"],
                "points": row["challenges"]["points"] if row["correct"] else 0,
            }
            for row in rows
        ]

    def list_notifications(self, limit: int = 10) -> list[dict[str, Any]]:
        session = self._require_session()
        return self._request(
            "GET",
            "/rest/v1/notifications",
            params={
                "select": "id,message,read,created_at",
                "user_id": f"eq.{session.user_id}",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )

    def record_submission(
        self,
        challenge_id: str,
        group_id: str | None,
        language: str,
        source_code: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        correct: bool,
        execution_ms: int,
    ) -> dict[str, Any]:
        self._require_session()
        rows = self._request(
            "POST",
            "/rest/v1/rpc/record_submission",
            json={
                "p_challenge_id": challenge_id,
                "p_group_id": group_id,
                "p_language": language,
                "p_source_code": source_code,
                "p_stdout": stdout,
                "p_stderr": stderr,
                "p_exit_code": exit_code,
                "p_correct": correct,
                "p_execution_ms": execution_ms,
            },
        )
        return rows[0]


def build_backend() -> DemoBackend | SupabaseBackend:
    """Constroi uma unica camada de dados de acordo com o ambiente."""

    env_file = Path(".env")
    if env_file.is_file():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if url and key:
        return SupabaseBackend(url, key)
    return DemoBackend()
