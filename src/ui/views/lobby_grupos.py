import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_grupos(page: ft.Page, navegar):
    state = get_state(page)
    campo_nome = ft.TextField(
        label="Nome do novo grupo", width=230, bgcolor=ft.Colors.GREY_900
    )
    campo_codigo = ft.TextField(
        label="Codigo de convite", width=200, bgcolor=ft.Colors.GREY_900
    )
    feedback = ft.Text("", color=ft.Colors.RED_300)
    lista_grupos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def abrir_grupo(group_id: str):
        state.selected_group_id = group_id
        navegar("grupo")

    def criar_card_grupo(group):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(group["name"], weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(
                                f"Codigo: {group['invite_code']}",
                                color=ft.Colors.WHITE_70,
                                size=12,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "ABRIR", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=ft.Colors.BLUE_700,
                        padding=10,
                        border_radius=5,
                        ink=True,
                        on_click=lambda e, group_id=group["id"]: abrir_grupo(group_id),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10),
        )

    def carregar_grupos():
        lista_grupos.controls.clear()
        try:
            grupos = state.backend.list_groups()
            if not grupos:
                lista_grupos.controls.append(
                    ft.Text("Voce ainda nao participa de nenhum grupo.", color=ft.Colors.GREY_400)
                )
            else:
                lista_grupos.controls.extend(criar_card_grupo(group) for group in grupos)
        except BackendError as exc:
            feedback.value = str(exc)

    def criar_grupo(e):
        try:
            group = state.backend.create_group(campo_nome.value or "")
            state.selected_group_id = group["id"]
            campo_nome.value = ""
            feedback.color = ft.Colors.GREEN_300
            feedback.value = f"Grupo criado. Codigo: {group['invite_code']}"
            carregar_grupos()
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
        page.update()

    def entrar_por_codigo(e):
        try:
            group = state.backend.join_group(campo_codigo.value or "")
            state.selected_group_id = group["id"]
            campo_codigo.value = ""
            feedback.color = ft.Colors.GREEN_300
            feedback.value = f"Voce entrou no grupo {group['name']}."
            carregar_grupos()
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
        page.update()

    botao_criar = ft.Container(
        content=ft.Text("Criar grupo", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        on_click=criar_grupo,
        bgcolor=ft.Colors.BLUE_700,
        padding=12,
        border_radius=5,
        ink=True,
    )
    botao_entrar = ft.Container(
        content=ft.Text("Entrar", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        on_click=entrar_por_codigo,
        bgcolor=ft.Colors.GREEN_700,
        padding=12,
        border_radius=5,
        ink=True,
    )

    carregar_grupos()
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Meus grupos", size=28, weight=ft.FontWeight.BOLD),
                ft.Row([campo_nome, botao_criar], wrap=True),
                ft.Row([campo_codigo, botao_entrar], wrap=True),
                feedback,
                ft.Divider(height=15, color=ft.Colors.OUTLINE),
                lista_grupos,
            ]
        ),
        padding=20,
        expand=True,
    )
