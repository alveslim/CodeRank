import re
import secrets

import flet as ft


def tela_grupos(page: ft.Page, navegar):
    # Estado apenas local para permitir demonstrar o fluxo sem backend.
    grupos_disponiveis = {
        "21910": "Grupo 1",
        "84729": "Equipe Python",
    }

    nome_grupo_input = ft.TextField(label="Nome do Grupo", width=300, autofocus=True)
    desc_grupo_input = ft.TextField(
        label="Descrição (Opcional)",
        width=300,
        multiline=True,
    )
    feedback_codigo = ft.Text("", color=ft.Colors.RED_300)

    def abrir_grupo(e):
        navegar("grupo")

    def fechar_modal(e):
        modal_criar_grupo.open = False
        page.update()

    def gerar_codigo_unico() -> str:
        while True:
            codigo = f"{secrets.randbelow(100000):05d}"
            if codigo not in grupos_disponiveis:
                return codigo

    def confirmar_criacao(e):
        nome = (nome_grupo_input.value or "").strip()
        if not nome:
            nome_grupo_input.error_text = "O nome do grupo é obrigatório."
            page.update()
            return

        if len(nome) > 50:
            nome_grupo_input.error_text = "O nome deve ter no máximo 50 caracteres."
            page.update()
            return

        codigo_gerado = gerar_codigo_unico()
        descricao = (desc_grupo_input.value or "").strip()
        grupos_disponiveis[codigo_gerado] = nome

        lista_grupos.controls.insert(
            0,
            criar_card_grupo(nome, codigo_gerado, descricao),
        )
        nome_grupo_input.value = ""
        nome_grupo_input.error_text = None
        desc_grupo_input.value = ""
        modal_criar_grupo.open = False
        page.update()

    modal_criar_grupo = ft.AlertDialog(
        title=ft.Text("Criar Novo Grupo", weight=ft.FontWeight.BOLD),
        content=ft.Column([
            ft.Text("Os dados serão mantidos somente nesta demonstração local."),
            nome_grupo_input,
            desc_grupo_input,
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.Button("Criar Grupo", on_click=confirmar_criacao),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )

    def abrir_modal_criar(e):
        if modal_criar_grupo not in page.overlay:
            page.overlay.append(modal_criar_grupo)
        modal_criar_grupo.open = True
        page.update()

    def entrar_por_codigo(e):
        codigo = (campo_codigo.value or "").strip()
        feedback_codigo.color = ft.Colors.RED_300

        if not re.fullmatch(r"\d{5}", codigo):
            feedback_codigo.value = "Informe um código de convite com 5 dígitos."
        elif codigo not in grupos_disponiveis:
            feedback_codigo.value = "Código não encontrado nesta demonstração local."
        else:
            feedback_codigo.value = f"Grupo encontrado: {grupos_disponiveis[codigo]}"
            feedback_codigo.color = ft.Colors.GREEN_300
            navegar("grupo")

        page.update()

    campo_codigo = ft.TextField(
        label="Código de Convite",
        width=200,
        height=45,
        bgcolor=ft.Colors.GREY_900,
        content_padding=10,
        max_length=5,
    )
    botao_entrar_codigo = ft.Container(
        content=ft.Text("Entrar", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        on_click=entrar_por_codigo,
        bgcolor=ft.Colors.GREEN_700,
        height=45,
        padding=ft.Padding.symmetric(horizontal=20),
        alignment=ft.Alignment.CENTER,
        border_radius=5,
        ink=True,
    )
    botao_criar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE, size=20),
            ft.Text("Criar Grupo", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
        on_click=abrir_modal_criar,
        bgcolor=ft.Colors.BLUE_700,
        height=45,
        padding=ft.Padding.symmetric(horizontal=15),
        alignment=ft.Alignment.CENTER,
        border_radius=5,
        ink=True,
    )

    secao_acoes = ft.Row([
        botao_criar,
        ft.Column([
            ft.Row([campo_codigo, botao_entrar_codigo], spacing=5),
            feedback_codigo,
        ], spacing=2),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def criar_card_grupo(nome, codigo, descricao=""):
        textos = [
            ft.Text(nome, weight=ft.FontWeight.BOLD, size=16),
            ft.Text(f"Código: {codigo}", color=ft.Colors.WHITE_70, size=12),
        ]
        if descricao:
            textos.append(ft.Text(descricao, color=ft.Colors.GREY_400, size=12))

        return ft.Container(
            content=ft.Row([
                ft.Column(textos, spacing=2, expand=True),
                ft.Container(
                    content=ft.Text("ABRIR", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE_700,
                    padding=10,
                    border_radius=5,
                    ink=True,
                    on_click=abrir_grupo,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10),
        )

    lista_grupos = ft.Column([
        criar_card_grupo("Grupo 1", "21910"),
        criar_card_grupo("Equipe Python", "84729"),
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    return ft.Container(
        content=ft.Column([
            ft.Text("Meus Grupos — demonstração local", size=28, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Criação e convites ainda não são persistidos em um backend.",
                color=ft.Colors.AMBER_300,
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            secao_acoes,
            ft.Divider(height=20, color=ft.Colors.OUTLINE),
            lista_grupos,
        ]),
        padding=20,
        expand=True,
    )
