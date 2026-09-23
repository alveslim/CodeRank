import flet as ft

def main_ui(page: ft.Page):
    page.title = "CodeRank"
    page.theme_mode = ft.ThemeMode.Dark

    page.add(ft.Text("Ambiente configurado com sucesso!", size=20, color=ft.colors.GREEN_400))