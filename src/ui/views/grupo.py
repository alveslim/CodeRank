import flet as ft

def tela_desafios(page: ft.Page, navegar):
    def abrir_desafio(e):
        navegar("editor")

    botao_resolver = ft.Container(
        content=ft.Text("Resolver", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_700,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=abrir_desafio
    )

    card_problema = ft.Container(
        content=ft.Row([
            ft.Text("1. Two Sum", weight=ft.FontWeight.BOLD, size=16),
            ft.Text("Fácil", color=ft.Colors.GREEN_400),
            botao_resolver
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=15,
        bgcolor=ft.Colors.GREY_900,
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.OUTLINE)
    )

    return ft.Container(
        content=ft.Column([
            ft.Text("Desafios Disponiveis", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            card_problema,
        ]),
        padding=20,
        expand=True
    )