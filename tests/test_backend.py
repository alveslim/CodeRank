import unittest

from src.services.backend import (
    BackendError,
    DemoBackend,
    _mensagem_backend_amigavel,
)


class DemoBackendTests(unittest.TestCase):
    def setUp(self):
        self.backend = DemoBackend()

    def login_demo(self):
        return self.backend.sign_in("demo@coderank.local", "demo1234")

    def test_rejects_invalid_login(self):
        with self.assertRaisesRegex(BackendError, "incorretos"):
            self.backend.sign_in("demo@coderank.local", "senha-errada")

    def test_creates_account_and_profile(self):
        session = self.backend.sign_up(
            "vitor@example.com",
            "senha123",
            {"name": "Vitor", "city": "Manaus", "state": "AM"},
        )
        profile = self.backend.get_profile()

        self.assertEqual(session.user_id, profile["id"])
        self.assertEqual("Vitor", profile["name"])
        self.assertEqual("Manaus", profile["city"])

    def test_rejects_duplicate_account(self):
        self.login_demo()
        with self.assertRaisesRegex(BackendError, "cadastrado"):
            self.backend.sign_up("demo@coderank.local", "demo1234", {"name": "Outro"})

    def test_creates_and_joins_group(self):
        self.backend.sign_up("owner@example.com", "senha123", {"name": "Owner"})
        group = self.backend.create_group("Grupo Teste")
        self.backend.sign_out()
        self.backend.sign_up("member@example.com", "senha123", {"name": "Member"})

        joined = self.backend.join_group(group["invite_code"])

        self.assertEqual(group["id"], joined["id"])
        self.assertEqual(1, len(self.backend.list_groups()))

    def test_filters_challenges_by_language(self):
        self.login_demo()
        challenges = self.backend.list_challenges("java")

        self.assertTrue(challenges)
        self.assertTrue(all(item["language"] == "java" for item in challenges))

    def test_awards_points_only_once(self):
        session = self.login_demo()
        group = self.backend.list_groups()[0]
        challenge = self.backend.get_challenge("demo-python-soma")
        arguments = dict(
            challenge_id=challenge["id"],
            group_id=group["id"],
            language="python",
            source_code="print(2 + 3)",
            stdout="5\n",
            stderr="",
            exit_code=0,
            correct=True,
            execution_ms=30,
        )

        first = self.backend.record_submission(**arguments)
        second = self.backend.record_submission(**arguments)
        ranking = self.backend.get_ranking(group["id"])
        user_row = next(item for item in ranking if item["user_id"] == session.user_id)

        self.assertEqual(100, first["points_awarded"])
        self.assertEqual(0, second["points_awarded"])
        self.assertEqual(400, user_row["points"])
        self.assertEqual(2, len(self.backend.list_submission_history()))
        self.assertIn("100 pontos", self.backend.list_notifications()[0]["message"])

    def test_updates_profile(self):
        self.login_demo()

        profile = self.backend.update_profile(
            {
                "name": "Novo Nome",
                "course": "Ciencia da Computacao",
                "cep": "69005070",
                "city": "Manaus",
                "state": "AM",
            }
        )

        self.assertEqual("Novo Nome", profile["name"])
        self.assertEqual("Ciencia da Computacao", profile["course"])
        self.assertEqual("69005070", profile["cep"])
        self.assertEqual("Manaus", profile["city"])

    def test_translates_common_supabase_auth_errors(self):
        self.assertIn(
            "limite temporario",
            _mensagem_backend_amigavel("Email rate limit exceeded", 429),
        )
        self.assertIn(
            "Aguarde 54 segundos",
            _mensagem_backend_amigavel(
                "For security purposes, you can only request this after 54 seconds.",
                429,
            ),
        )
        self.assertIn(
            "ja esta cadastrado",
            _mensagem_backend_amigavel("User already registered", 422),
        )

    def test_owner_can_remove_member(self):
        owner = self.backend.sign_up(
            "owner2@example.com", "senha123", {"name": "Owner Dois"}
        )
        group = self.backend.create_group("Grupo Remocao")
        self.backend.sign_out()
        member = self.backend.sign_up(
            "member2@example.com", "senha123", {"name": "Member Dois"}
        )
        self.backend.join_group(group["invite_code"])
        self.backend.sign_out()
        self.backend.sign_in("owner2@example.com", "senha123")

        self.backend.remove_group_member(group["id"], member.user_id)

        members = self.backend.list_group_members(group["id"])
        self.assertEqual([owner.user_id], [item["user_id"] for item in members])

    def test_member_cannot_remove_owner(self):
        owner = self.backend.sign_up(
            "owner3@example.com", "senha123", {"name": "Owner Tres"}
        )
        group = self.backend.create_group("Grupo Protegido")
        self.backend.sign_out()
        self.backend.sign_up(
            "member3@example.com", "senha123", {"name": "Member Tres"}
        )
        self.backend.join_group(group["invite_code"])

        with self.assertRaisesRegex(BackendError, "administradores"):
            self.backend.remove_group_member(group["id"], owner.user_id)


if __name__ == "__main__":
    unittest.main()
