import unittest

import flet as ft

from src.ui.app import main_ui
from src.ui.views.cadastro import tela_cadastro
from src.ui.views.desafios import tela_desafios
from src.ui.views.editor import tela_editor
from src.ui.views.grupo import tela_grupo
from src.ui.views.lobby_grupos import tela_grupos
from src.ui.views.login import tela_login
from src.ui.views.perfil import tela_perfil
from src.ui.views.ranking import tela_ranking


class FakePage:
    def __init__(self):
        self.overlay = []
        self.controls = []
        self.appbar = None
        self.title = ""
        self.theme_mode = None

    def update(self):
        pass

    def clean(self):
        self.controls.clear()

    def add(self, *controls):
        self.controls.extend(controls)


class UISmokeTests(unittest.TestCase):
    def setUp(self):
        self.page = FakePage()
        self.navigate = lambda route: None

    def test_all_views_can_be_constructed(self):
        views = (
            ("login", lambda: tela_login(self.page, self.navigate)),
            ("cadastro", lambda: tela_cadastro(self.page, self.navigate)),
            ("desafios", lambda: tela_desafios(self.page, self.navigate)),
            ("editor", lambda: tela_editor(self.page)),
            ("grupos", lambda: tela_grupos(self.page, self.navigate)),
            ("grupo", lambda: tela_grupo(self.page, self.navigate)),
            ("perfil", lambda: tela_perfil(self.page, self.navigate)),
            ("ranking", lambda: tela_ranking(self.page, self.navigate)),
        )

        for name, build_view in views:
            with self.subTest(view=name):
                control = build_view()
                self.assertIsInstance(control, ft.Control)

    def test_main_ui_starts_on_login(self):
        main_ui(self.page)

        self.assertEqual("CodeRank", self.page.title)
        self.assertIsNotNone(self.page.controls)
        self.assertEqual(1, len(self.page.controls))
        self.assertIsNone(self.page.appbar)


if __name__ == "__main__":
    unittest.main()
