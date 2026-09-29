import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_grupo(page: ft.Page, navegar):
    state = get_state(page)
    try:
        groups = state.backend.list_groups()
        group = next(
            (item for item in groups if item["id"] == state.selected_group_id),
            groups[0] if groups else None,
        )
        if group is None:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Nenhum grupo selecionado.", size=22),
                        ft.TextButton(
                            "Voltar aos grupos", on_click=lambda e: navegar("lobby_grupos")
                        ),
                    ]
                ),
                padding=20,
            )
        state.selected_group_id = group["id"]
        ranking = state.backend.get_ranking(group["id"])
    except BackendError as exc:
        return ft.Container(content=ft.Text(str(exc), color=ft.Colors.RED_300), padding=20)

    ranking_controls = [
        ft.Text(
            f"#{row['position']}  {row['name']} — {row['points']} pts",
            size=16,
        )
        for row in ranking[:5]
    ] or [ft.Text("Nenhuma pontuacao ainda.", color=ft.Colors.GREY_400)]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(group["name"], size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Codigo de convite: {group['invite_code']}", color=ft.Colors.BLUE_300),
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Ranking do grupo", size=20, weight=ft.FontWeight.BOLD),
                *ranking_controls,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Row(
                    [
                        ft.TextButton(
                            "Resolver desafios",
                            icon=ft.Icons.CODE,
                            on_click=lambda e: navegar("desafios"),
                        ),
                        ft.TextButton(
                            "Ver ranking completo",
                            icon=ft.Icons.LEADERBOARD,
                            on_click=lambda e: navegar("ranking"),
                        ),
                    ],
                    wrap=True,
                ),
            ]
        ),
        padding=20,
        expand=True,
    )
