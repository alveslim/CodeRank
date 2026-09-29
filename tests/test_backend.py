import unittest

from src.services.backend import BackendError, DemoBackend


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


if __name__ == "__main__":
    unittest.main()
