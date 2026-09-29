import flet as ft

from src.services.backend import BackendError
from src.services.viacep import CepError, consultar_cep, formatar_cep, limpar_cep
from src.ui.state import get_state


def tela_perfil(page: ft.Page, navegar):
    state = get_state(page)
    try:
        profile = state.backend.get_profile()
        history = state.backend.list_submission_history(5)
        notifications = state.backend.list_notifications(5)
    except BackendError as exc:
        return ft.Container(
            content=ft.Text(str(exc), color=ft.Colors.RED_300), padding=20
        )

    campo_nome = ft.TextField(label="Nome", value=profile.get("name", ""), width=350)
    campo_curso = ft.TextField(
        label="Curso", value=profile.get("course", ""), width=350
    )
    campo_instituicao = ft.TextField(
        label="Instituicao", value=profile.get("institution", ""), width=350
    )
    campo_cep = ft.TextField(
        label="CEP (8 numeros)",
        hint_text="00000-000",
        value=formatar_cep(profile.get("cep", "")),
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=9,
        width=350,
    )
    localizacao_inicial = " - ".join(
        filter(None, [profile.get("city"), profile.get("state")])
    )
    campo_cidade = ft.TextField(
        label="Cidade",
        value=localizacao_inicial,
        read_only=True,
        width=350,
    )
    texto_localizacao = ft.Text(localizacao_inicial, color=ft.Colors.GREY_400)
    feedback_cep = ft.Text("", color=ft.Colors.RED_300, width=350)
    feedback = ft.Text("", color=ft.Colors.RED_300)
    endereco = {
        "cep": limpar_cep(profile.get("cep", "")),
        "city": str(profile.get("city") or ""),
        "state": str(profile.get("state") or ""),
    }

    def limpar_endereco():
        endereco.update({"cep": "", "city": "", "state": ""})
        campo_cidade.value = ""

    def formatar_campo_cep(e):
        valor_formatado = formatar_cep(campo_cep.value)
        if campo_cep.value != valor_formatado:
            campo_cep.value = valor_formatado
        if endereco["cep"] != limpar_cep(campo_cep.value):
            limpar_endereco()
            feedback_cep.value = ""
        page.update()

    def carregar_endereco(*, mostrar_busca: bool = True) -> bool:
        cep_atual = limpar_cep(campo_cep.value)
        if endereco["cep"] == cep_atual and endereco["city"] and endereco["state"]:
            return True

        if mostrar_busca:
            feedback_cep.value = "Consultando CEP..."
            feedback_cep.color = ft.Colors.BLUE_400
            page.update()
        try:
            dados = consultar_cep(campo_cep.value)
        except CepError as exc:
            limpar_endereco()
            feedback_cep.value = str(exc)
            feedback_cep.color = ft.Colors.RED_300
            page.update()
            return False

        endereco["cep"] = limpar_cep(dados.get("cep", cep_atual))
        endereco["city"] = str(dados.get("localidade") or "")
        endereco["state"] = str(dados.get("uf") or "")
        campo_cep.value = formatar_cep(endereco["cep"])
        campo_cidade.value = f"{endereco['city']} - {endereco['state']}"
        feedback_cep.value = "CEP encontrado."
        feedback_cep.color = ft.Colors.GREEN_300
        page.update()
        return True

    def validar_cep(e):
        carregar_endereco()

    def salvar(e):
        feedback.value = ""
        nome = (campo_nome.value or "").strip()
        if len(nome) < 2:
            feedback.color = ft.Colors.RED_300
            feedback.value = "Informe um nome com pelo menos 2 caracteres."
            page.update()
            return
        if not carregar_endereco(mostrar_busca=False):
            feedback.color = ft.Colors.RED_300
            feedback.value = "Corrija o CEP antes de salvar o perfil."
            page.update()
            return

        try:
            state.backend.update_profile(
                {
                    "name": nome,
                    "course": campo_curso.value or "",
                    "institution": campo_instituicao.value or "",
                    "cep": endereco["cep"],
                    "city": endereco["city"],
                    "state": endereco["state"],
                }
            )
            texto_localizacao.value = (
                f"{endereco['city']} - {endereco['state']}"
            )
            feedback.color = ft.Colors.GREEN_300
            feedback.value = "Perfil e endereco atualizados."
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

    campo_cep.on_change = formatar_campo_cep
    campo_cep.on_blur = validar_cep

    stats = ft.Row(
        [
            ft.Column(
                [
                    ft.Text(
                        str(profile.get("points", 0)),
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text("Pontos"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
            ft.Column(
                [
                    ft.Text(
                        str(profile.get("solved_count", 0)),
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text("Desafios"),
                ],
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
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.PERSON, size=40), radius=40
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    profile.get("email", ""),
                                    color=ft.Colors.GREY_400,
                                ),
                                texto_localizacao,
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
                campo_cep,
                feedback_cep,
                campo_cidade,
                ft.TextButton(
                    "Salvar alteracoes", icon=ft.Icons.SAVE, on_click=salvar
                ),
                feedback,
                ft.Divider(height=20, color=ft.Colors.OUTLINE),
                ft.Text("Historico recente", size=20, weight=ft.FontWeight.BOLD),
                *history_controls,
                ft.Text("Notificacoes", size=20, weight=ft.FontWeight.BOLD),
                *notification_controls,
                ft.Text(
                    "Modo demonstracao local"
                    if state.backend.mode == "demo"
                    else "Conectado ao Supabase",
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
