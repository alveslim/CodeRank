import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state

def tela_login(page: ft.Page, navegar):
    campo_email = ft.TextField(label="E-mail", width=350, bgcolor=ft.Colors.GREEN_900)
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=350, bgcolor=ft.Colors.GREEN_900)
    feedback = ft.Text("", color=ft.Colors.RED_300, width=350)
    state = get_state(page)

    def entrar(e):
        feedback.value = ""
        try:
            state.session = state.backend.sign_in(
                campo_email.value or "", campo_senha.value or ""
            )
            grupos = state.backend.list_groups()
            state.selected_group_id = grupos[0]["id"] if grupos else None
            navegar("desafios")
        except BackendError as exc:
            feedback.value = str(exc)
            page.update()

    botao_entrar = ft.Container(
        content=ft.Text("Entrar na Conta", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREEN_700,
        padding=12,
        alignment=ft.Alignment.CENTER,
        width=350,
        border_radius=5,
        ink=True,
        on_click=entrar
    )

    modo = (
        "Modo demonstracao local — use demo@coderank.local / demo1234"
        if state.backend.mode == "demo"
        else "Conectado ao Supabase"
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Faça login para competir", color=ft.Colors.GREY_400),
            ft.Text(modo, color=ft.Colors.AMBER_300, size=12, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            feedback,
            botao_entrar,
            ft.TextButton("Ainda não tem conta? Registre-se", on_click=lambda e: navegar("cadastro"))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        expand=True,
        alignment=ft.Alignment.CENTER
    )
