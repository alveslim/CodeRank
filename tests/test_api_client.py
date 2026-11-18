import asyncio
import unittest
from unittest import mock

from src import state
from src.services import api


def run(coro):
    return asyncio.run(coro)


class FakeFetch:
    """Substitui fetch_json devolvendo respostas enfileiradas e guardando as chamadas."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def __call__(self, method, url, body=None, headers=None, timeout=25.0):
        self.calls.append((method, url, body, dict(headers or {})))
        return self.responses.pop(0)


class ApiClientTests(unittest.TestCase):
    def setUp(self):
        state.clear_session()

    def tearDown(self):
        state.clear_session()

    def test_login_stores_session(self):
        fake = FakeFetch((200, {
            "access_token": "tok", "refresh_token": "ref",
            "user": {"id": "u1", "email": "a@b.com"},
            "profile": {"username": "ana"},
        }))
        with mock.patch.object(api, "fetch_json", fake):
            run(api.login("a@b.com", "senha1234"))
        self.assertTrue(state.session.logged_in)
        self.assertEqual("ana", state.session.profile["username"])
        self.assertEqual("POST", fake.calls[0][0])
        self.assertTrue(fake.calls[0][1].endswith("/auth/login"))
        self.assertNotIn("Authorization", fake.calls[0][3])

    def test_error_message_comes_from_api(self):
        fake = FakeFetch((401, {"error": "E-mail ou senha incorretos."}))
        with mock.patch.object(api, "fetch_json", fake):
            with self.assertRaises(api.ApiError) as ctx:
                run(api.login("a@b.com", "x"))
        self.assertEqual(401, ctx.exception.status)
        self.assertEqual("E-mail ou senha incorretos.", ctx.exception.message)
        self.assertFalse(state.session.logged_in)

    def test_network_failure_is_friendly(self):
        with mock.patch.object(api, "fetch_json", FakeFetch((0, None))):
            with self.assertRaises(api.ApiError) as ctx:
                run(api.get("/problems", auth=False))
        self.assertEqual(0, ctx.exception.status)
        self.assertIn("conectar", ctx.exception.message)

    def test_authenticated_call_sends_bearer_and_refreshes_once_on_401(self):
        state.start_session({"access_token": "old", "refresh_token": "ref", "user": {"id": "u1"}})
        fake = FakeFetch(
            (401, {"error": "Sessão expirada."}),
            (200, {"access_token": "new", "refresh_token": "ref2", "user": {"id": "u1"}}),
            (200, {"ok": True}),
        )
        with mock.patch.object(api, "fetch_json", fake):
            result = run(api.get("/me"))
        self.assertEqual({"ok": True}, result)
        self.assertEqual("Bearer old", fake.calls[0][3]["Authorization"])
        self.assertTrue(fake.calls[1][1].endswith("/auth/refresh"))
        self.assertEqual("Bearer new", fake.calls[2][3]["Authorization"])
        self.assertEqual("new", state.session.access_token)

    def test_refresh_failure_keeps_401(self):
        state.start_session({"access_token": "old", "refresh_token": "ref", "user": {"id": "u1"}})
        fake = FakeFetch((401, {"error": "Sessão expirada."}), (401, {"error": "x"}))
        with mock.patch.object(api, "fetch_json", fake):
            with self.assertRaises(api.ApiError) as ctx:
                run(api.get("/me"))
        self.assertEqual(401, ctx.exception.status)

    def test_logout_clears_session_even_if_api_fails(self):
        state.start_session({"access_token": "tok", "refresh_token": "ref", "user": {"id": "u1"}})
        with mock.patch.object(api, "fetch_json", FakeFetch((500, {"error": "boom"}))):
            run(api.logout())
        self.assertFalse(state.session.logged_in)
        self.assertIsNone(state.session.profile)


class SessionStorageTests(unittest.TestCase):
    def test_load_session_without_browser_storage_is_false(self):
        state.clear_session()
        self.assertFalse(state.load_session())


if __name__ == "__main__":
    unittest.main()
