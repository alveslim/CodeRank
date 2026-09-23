import flet as ft
from src.ui.views.editor import tela_editor
from src.ui.components.navbar import criar_navbar

def main_ui(page: ft.Page):
    page.title = "CodeRank"
    page.theme_mode = ft.ThemeMode.DARK
    page.appbar = criar_navbar(page)
    page.clean()
    page.add(tela_editor(page))
