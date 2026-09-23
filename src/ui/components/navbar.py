import flet as ft

def criar_navbar(page: ft.Page):
    return ft.AppBar(
        leading=ft.Icon(ft.Icons.CODE),
        leading_width=40,
        title=ft.Text("CodeRank", weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=ft.Colors.GREY_900,
        actions=[
            ft.TextButton("Desafios", icon=ft.Icons.LIST_ALT),
            ft.TextButton("Ranking", icon=ft.Icons.LEADERBOARD),
            ft.IconButton(ft.Icons.PERSON, tooltip="Perfil"),
        ]
    )