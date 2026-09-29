import flet as ft

from src.services.backend import BackendError
from src.ui.state import get_state


def tela_perfil(page: ft.Page, navegar):
    state = get_state(page)
    try:
        profile = state.backend.get_profile()
        history = state.backend.list_submission_history(5)
        notifications = state.backend.list_notifications(5)
    except BackendError as exc:
        return ft.Container(content=ft.Text(str(exc), color=ft.Colors.RED_300), padding=20)

    campo_nome = ft.TextField(label="Nome", value=profile.get("name", ""), width=350)
    campo_curso = ft.TextField(label="Curso", value=profile.get("course", ""), width=350)
    campo_instituicao = ft.TextField(
        label="Instituicao", value=profile.get("institution", ""), width=350
    )
    feedback = ft.Text("", color=ft.Colors.RED_300)

    def salvar(e):
        try:
            state.backend.update_profile(
                {
                    "name": campo_nome.value or "",
                    "course": campo_curso.value or "",
                    "institution": campo_instituicao.value or "",
                }
            )
            feedback.color = ft.Colors.GREEN_300
            feedback.value = "Perfil atualizado."
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
        page.update()

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
    history_controls = [
        ft.Text(
            f"{'Aceito' if item['correct'] else 'Incorreto'} — {item['challenge_title']} ({item['language']})",
            color=ft.Colors.GREEN_300 if item["correct"] else ft.Colors.RED_300,
        )
        for item in history
    ] or [ft.Text("Nenhuma submissao registrada.", color=ft.Colors.GREY_400)]
    notification_controls = [
        ft.Text(item["message"], color=ft.Colors.BLUE_200) for item in notifications
    ] or [ft.Text("Nenhuma notificacao.", color=ft.Colors.GREY_400)]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("O meu perfil", size=28, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, size=40), radius=40),
                        ft.Column(
                            [
                                ft.Text(profile.get("email", ""), color=ft.Colors.GREY_400),
                                ft.Text(location, color=ft.Colors.GREY_400),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=20,
                ),
                stats,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Editar perfil", size=20, weight=ft.FontWeight.BOLD),
                campo_nome,
                campo_curso,
                campo_instituicao,
                ft.TextButton("Salvar alteracoes", icon=ft.Icons.SAVE, on_click=salvar),
                feedback,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Historico recente", size=20, weight=ft.FontWeight.BOLD),
                *history_controls,
                ft.Text("Notificacoes", size=20, weight=ft.FontWeight.BOLD),
                *notification_controls,
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
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
