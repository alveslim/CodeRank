import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_desafios(page: ft.Page, navegar):
    state = get_state(page)
    lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    feedback = ft.Text("", color=ft.Colors.RED_300)
    filtro = ft.Dropdown(
        label="Linguagem",
        value="todos",
        width=190,
        options=[
            ft.DropdownOption(key="todos", text="Todas"),
            ft.DropdownOption(key="python", text="Python"),
            ft.DropdownOption(key="java", text="Java"),
        ],
    )

    def abrir_desafio(challenge_id: str):
        state.selected_challenge_id = challenge_id
        navegar("editor")

    def card(challenge):
        color = {
            "Facil": ft.Colors.GREEN_400,
            "Medio": ft.Colors.AMBER_400,
            "Dificil": ft.Colors.RED_400,
        }.get(challenge["difficulty"], ft.Colors.GREY_400)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(challenge["title"], weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(challenge["description"], color=ft.Colors.GREY_400),
                            ft.Text(
                                f"{challenge['language'].upper()} • {challenge['points']} pontos",
                                size=12,
                                color=ft.Colors.BLUE_300,
                            ),
                        ],
                        expand=True,
                    ),
                    ft.Text(challenge["difficulty"], color=color),
                    ft.Container(
                        content=ft.Text("Resolver", weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.BLUE_700,
                        padding=10,
                        border_radius=5,
                        ink=True,
                        on_click=lambda e, challenge_id=challenge["id"]: abrir_desafio(challenge_id),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )

    def carregar(e=None):
        lista.controls.clear()
        feedback.value = ""
        try:
            challenges = state.backend.list_challenges(filtro.value)
            lista.controls.extend(card(item) for item in challenges)
            if not challenges:
                lista.controls.append(ft.Text("Nenhum desafio encontrado."))
        except BackendError as exc:
            feedback.value = str(exc)
        if e is not None:
            page.update()

    filtro.on_select = carregar
    carregar()
    aviso = (
        "Modo demonstracao: os dados serao apagados ao fechar o aplicativo."
        if state.backend.mode == "demo"
        else "Dados carregados do Supabase."
    )
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Desafios disponiveis", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(aviso, color=ft.Colors.AMBER_300, size=12),
                filtro,
                feedback,
                lista,
            ]
        ),
        padding=20,
        expand=True,
    )
