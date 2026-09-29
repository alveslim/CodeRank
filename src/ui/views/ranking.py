import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_ranking(page: ft.Page, navegar):
    state = get_state(page)
    lista = ft.Column(spacing=10)
    feedback = ft.Text("", color=ft.Colors.RED_300)

    try:
        groups = state.backend.list_groups()
    except BackendError as exc:
        groups = []
        feedback.value = str(exc)

    if groups and not state.selected_group_id:
        state.selected_group_id = groups[0]["id"]
    seletor = ft.Dropdown(
        label="Grupo",
        value=state.selected_group_id,
        width=260,
        options=[ft.DropdownOption(key=group["id"], text=group["name"]) for group in groups],
    )

    def criar_linha(row):
        destaque = (
            ft.Colors.BLUE_900
            if state.session and row["user_id"] == state.session.user_id
            else ft.Colors.GREY_900
        )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"#{row['position']}", weight=ft.FontWeight.BOLD, width=45),
                    ft.Text(row["name"], expand=True),
                    ft.Text(
                        f"{row['points']} pts",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.AMBER_400,
                    ),
                ]
            ),
            padding=15,
            bgcolor=destaque,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )

    def carregar(e=None):
        state.selected_group_id = seletor.value
        lista.controls.clear()
        try:
            rows = state.backend.get_ranking(seletor.value)
            lista.controls.extend(criar_linha(row) for row in rows)
            if not rows:
                lista.controls.append(
                    ft.Text("Nenhuma pontuacao ainda.", color=ft.Colors.GREY_400)
                )
        except BackendError as exc:
            feedback.value = str(exc)
        if e is not None:
            page.update()

    seletor.on_select = carregar
    carregar()
    content = [
        ft.Text("Ranking do grupo", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("Resolva desafios para conquistar pontos.", color=ft.Colors.GREY_400),
    ]
    if groups:
        content.extend([seletor, feedback, lista])
    else:
        content.extend(
            [
                feedback,
                ft.Text("Crie ou entre em um grupo para visualizar o ranking."),
                ft.TextButton(
                    "Ir para grupos", on_click=lambda e: navegar("lobby_grupos")
                ),
            ]
        )
    return ft.Container(content=ft.Column(content), padding=20, expand=True)
