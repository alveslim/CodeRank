import flet as ft

from src.services import api
from src.ui.helpers import mensagem_erro


def tela_login(page: ft.Page, navegar):
    campo_email = ft.TextField(
        label="E-mail",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    campo_senha = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        width=350,
        bgcolor=ft.Colors.GREEN_900,
    )
    feedback = ft.Text("", color=ft.Colors.RED_300, width=350, text_align=ft.TextAlign.CENTER)
    progresso = ft.ProgressRing(width=22, height=22, visible=False)

    async def entrar():
        email = (campo_email.value or "").strip()
        senha = campo_senha.value or ""
        if not email or not senha:
            feedback.value = "Informe e-mail e senha."
            page.update()
            return

        botao_entrar.disabled = True
        progresso.visible = True
        feedback.value = ""
        page.update()
        try:
            await api.login(email, senha)
        except Exception as exc:  # noqa: BLE001
            feedback.value = mensagem_erro(exc)
            botao_entrar.disabled = False
            progresso.visible = False
            page.update()
            return
        navegar("desafios")

    def ao_clicar(e):
        page.run_task(entrar)

    campo_senha.on_submit = ao_clicar
    botao_entrar = ft.Button(
        content=ft.Text("Entrar na conta"),
        width=350,
        on_click=ao_clicar,
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Entre para competir", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            botao_entrar,
            progresso,
            feedback,
            ft.TextButton(
                "Ainda não tem conta? Cadastre-se",
                on_click=lambda e: navegar("cadastro"),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        expand=True,
        alignment=ft.Alignment.CENTER,
    )
