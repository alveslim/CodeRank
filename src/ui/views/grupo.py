import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_grupo(page: ft.Page, navegar):
    state = get_state(page)
    feedback = ft.Text("", color=ft.Colors.RED_300)
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
        ft.Text(f"#{row['position']}  {row['name']} — {row['points']} pts", size=16)
        for row in ranking[:5]
    ] or [ft.Text("Nenhuma pontuacao ainda.", color=ft.Colors.GREY_400)]
    members_column = ft.Column(spacing=8)

    def remover_membro(user_id: str):
        try:
            state.backend.remove_group_member(group["id"], user_id)
            feedback.color = ft.Colors.GREEN_300
            feedback.value = "Membro removido."
            carregar_membros()
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
        page.update()

    def carregar_membros():
        members_column.controls.clear()
        try:
            members = state.backend.list_group_members(group["id"])
            can_manage = group.get("role") in {"owner", "admin"}
            for member in members:
                controls = [
                    ft.Column(
                        [
                            ft.Text(member["name"], weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"{member['role']} • {member['points']} pontos",
                                color=ft.Colors.GREY_400,
                                size=12,
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    )
                ]
                if (
                    can_manage
                    and member["role"] != "owner"
                    and state.session
                    and member["user_id"] != state.session.user_id
                ):
                    controls.append(
                        ft.TextButton(
                            "Remover",
                            icon=ft.Icons.PERSON_REMOVE,
                            on_click=lambda e, user_id=member["user_id"]: remover_membro(user_id),
                        )
                    )
                members_column.controls.append(
                    ft.Container(
                        content=ft.Row(controls),
                        padding=10,
                        bgcolor=ft.Colors.GREY_900,
                        border_radius=6,
                    )
                )
        except BackendError as exc:
            feedback.value = str(exc)

    carregar_membros()
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(group["name"], size=28, weight=ft.FontWeight.BOLD),
                ft.Text(f"Codigo de convite: {group['invite_code']}", color=ft.Colors.BLUE_300),
                ft.Text(f"Sua funcao: {group.get('role', 'member')}", color=ft.Colors.GREY_400),
                feedback,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Ranking do grupo", size=20, weight=ft.FontWeight.BOLD),
                *ranking_controls,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Membros", size=20, weight=ft.FontWeight.BOLD),
                members_column,
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
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
