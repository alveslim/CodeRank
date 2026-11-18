import re

import flet as ft

from src import state
from src.services import api
from src.ui.helpers import botao, cartao, carregando, mensagem_erro, sessao_expirada


def _codigo(grupo_id: int) -> str:
    return f"{grupo_id:05d}"


def tela_grupos(page: ft.Page, navegar):
    nome_grupo_input = ft.TextField(label="Nome do Grupo", width=300, autofocus=True, max_length=40)
    desc_grupo_input = ft.TextField(label="Descrição (opcional)", width=300, multiline=True, max_length=200)
    erro_modal = ft.Text("", color=ft.Colors.RED_300)
    feedback_codigo = ft.Text("", color=ft.Colors.RED_300)
    lista_grupos = ft.Column([carregando()], scroll=ft.ScrollMode.AUTO, expand=True)

    def abrir_grupo(grupo_id: int):
        def _abrir(e):
            state.session.selected_group = grupo_id
            navegar("grupo")

        return _abrir

    def entrar_no_grupo(grupo_id: int):
        async def _entrar():
            try:
                await api.post(f"/groups/{grupo_id}/join")
            except Exception as exc:  # noqa: BLE001
                if sessao_expirada(exc, navegar):
                    return
                feedback_codigo.color = ft.Colors.RED_300
                feedback_codigo.value = mensagem_erro(exc)
                page.update()
                return
            state.session.selected_group = grupo_id
            navegar("grupo")

        return lambda e: page.run_task(_entrar)

    def card_grupo(g: dict):
        info = f"Código: {_codigo(g['id'])} • {g['members']} membro(s)"
        textos = [
            ft.Text(g["name"], weight=ft.FontWeight.BOLD, size=16),
            ft.Text(info, color=ft.Colors.GREY_400, size=12),
        ]
        if g.get("description"):
            textos.append(ft.Text(g["description"], color=ft.Colors.GREY_400, size=12))
        acao = (
            botao("ABRIR", abrir_grupo(g["id"]))
            if g["member"]
            else botao("ENTRAR", entrar_no_grupo(g["id"]), ft.Colors.GREEN_700)
        )
        return cartao(ft.Row([ft.Column(textos, spacing=2, expand=True), acao], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    async def carregar():
        try:
            dados = await api.get("/groups")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            lista_grupos.controls = [ft.Text(mensagem_erro(exc), color=ft.Colors.RED_300)]
            page.update()
            return
        lista_grupos.controls = [card_grupo(g) for g in dados["groups"]] or [
            ft.Text("Nenhum grupo ainda. Crie o primeiro!", color=ft.Colors.GREY_400)
        ]
        page.update()

    def fechar_modal(e):
        modal_criar_grupo.open = False
        page.update()

    async def confirmar_criacao():
        nome = (nome_grupo_input.value or "").strip()
        nome_grupo_input.error_text = None
        erro_modal.value = ""
        if len(nome) < 3:
            nome_grupo_input.error_text = "O nome deve ter pelo menos 3 caracteres."
            page.update()
            return
        try:
            r = await api.post("/groups", {"name": nome, "description": (desc_grupo_input.value or "").strip()})
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            erro_modal.value = mensagem_erro(exc)
            page.update()
            return
        nome_grupo_input.value = ""
        desc_grupo_input.value = ""
        modal_criar_grupo.open = False
        state.session.selected_group = r["group"]["id"]
        navegar("grupo")

    modal_criar_grupo = ft.AlertDialog(
        title=ft.Text("Criar novo grupo", weight=ft.FontWeight.BOLD),
        content=ft.Column([nome_grupo_input, desc_grupo_input, erro_modal], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.Button("Criar grupo", on_click=lambda e: page.run_task(confirmar_criacao)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )

    def abrir_modal_criar(e):
        if modal_criar_grupo not in page.overlay:
            page.overlay.append(modal_criar_grupo)
        modal_criar_grupo.open = True
        page.update()

    campo_codigo = ft.TextField(
        label="Código do grupo",
        width=200,
        height=45,
        bgcolor=ft.Colors.GREY_900,
        content_padding=10,
        max_length=5,
    )

    def entrar_por_codigo(e):
        codigo = (campo_codigo.value or "").strip()
        feedback_codigo.color = ft.Colors.RED_300
        if not re.fullmatch(r"\d{1,5}", codigo):
            feedback_codigo.value = "Informe o código numérico do grupo."
            page.update()
            return
        feedback_codigo.value = ""
        entrar_no_grupo(int(codigo))(e)

    secao_acoes = ft.Row([
        botao("Criar grupo", abrir_modal_criar, ft.Colors.BLUE_700, ft.Icons.ADD),
        ft.Column([
            ft.Row([campo_codigo, botao("Entrar", entrar_por_codigo, ft.Colors.GREEN_700)], spacing=5),
            feedback_codigo,
        ], spacing=2),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column([
            ft.Text("Grupos", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            secao_acoes,
            ft.Divider(height=20, color=ft.Colors.OUTLINE),
            lista_grupos,
        ], expand=True),
        padding=20,
        expand=True,
    )
