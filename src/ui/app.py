import flet as ft
from src.ui.views.editor import tela_editor

def main_ui(page: ft.Page):
    page.title = "CodeRank"
    page.theme_mode = ft.ThemeMode.DARK

    page.clean()
    page.add(tela_editor(page))

