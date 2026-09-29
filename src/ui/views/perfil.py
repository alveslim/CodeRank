import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_perfil(page: ft.Page, navegar):
    state = get_state(page)
    try:
        profile = state.backend.get_profile()
    except BackendError as exc:
        return ft.Container(content=ft.Text(str(exc), color=ft.Colors.RED_300), padding=20)

    def deslogar(e):
        try:
            state.backend.sign_out()
        except BackendError:
            pass
        state.session = None
        state.selected_group_id = None
        state.selected_challenge_id = None
        navegar("login")

    location = " - ".join(filter(None, [profile.get("city"), profile.get("state")]))
    stats = ft.Row(
        [
            ft.Column(
                [ft.Text(str(profile.get("points", 0)), size=24, weight=ft.FontWeight.BOLD), ft.Text("Pontos")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
            ft.Column(
                [ft.Text(str(profile.get("solved_count", 0)), size=24, weight=ft.FontWeight.BOLD), ft.Text("Desafios")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("O meu perfil", size=28, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, size=40), radius=40),
                        ft.Column(
                            [
                                ft.Text(profile.get("name", "Usuario"), size=24, weight=ft.FontWeight.BOLD),
                                ft.Text(profile.get("email", ""), color=ft.Colors.GREY_400),
                                ft.Text(
                                    f"{profile.get('course', '')} | {profile.get('institution', '')}",
                                    color=ft.Colors.GREY_400,
                                ),
                                ft.Text(location, color=ft.Colors.GREY_400),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=20,
                ),
                ft.Divider(height=30, color=ft.Colors.OUTLINE),
                stats,
                ft.Divider(height=30, color=ft.Colors.OUTLINE),
                ft.Text(
                    "Modo demonstracao local" if state.backend.mode == "demo" else "Conectado ao Supabase",
                    color=ft.Colors.AMBER_300,
                ),
                ft.Container(
                    content=ft.Text("Terminar sessao", weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.RED_700,
                    padding=10,
                    border_radius=5,
                    ink=True,
                    on_click=deslogar,
                ),
            ]
        ),
        padding=20,
        expand=True,
    )
