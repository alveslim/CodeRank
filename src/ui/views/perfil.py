import flet as ft

from src import state
from src.services import api
from src.ui.helpers import botao, cartao, carregando, mensagem_erro, sessao_expirada

STATUS = {
    "accepted": ("Aceito", ft.Colors.GREEN_400, ft.Icons.CHECK_CIRCLE),
    "wrong_answer": ("Resposta incorreta", ft.Colors.RED_400, ft.Icons.CANCEL),
    "runtime_error": ("Erro de execução", ft.Colors.RED_400, ft.Icons.CANCEL),
    "timeout": ("Tempo excedido", ft.Colors.ORANGE_400, ft.Icons.TIMER_OFF),
    "error": ("Erro", ft.Colors.RED_400, ft.Icons.CANCEL),
}


def tela_perfil(page: ft.Page, navegar):
    texto_nome = ft.Text("", size=24, weight=ft.FontWeight.BOLD)
    texto_usuario = ft.Text("", color=ft.Colors.GREY_400, size=16)
    texto_local = ft.Text("", color=ft.Colors.GREY_400, size=16)
    texto_bio = ft.Text("", color=ft.Colors.GREY_300, size=14)
    estatisticas = ft.Row([carregando()], alignment=ft.MainAxisAlignment.CENTER)
    historico = ft.Column([], scroll=ft.ScrollMode.AUTO, height=240)

    input_nome = ft.TextField(label="Nome de exibição", width=320, max_length=40)
    input_cidade = ft.TextField(label="Cidade", width=320, max_length=60)
    input_bio = ft.TextField(label="Bio", width=320, multiline=True, max_length=200)
    erro_modal = ft.Text("", color=ft.Colors.RED_300)

    def estat(valor, rotulo):
        return ft.Column(
            [ft.Text(str(valor), size=24, weight=ft.FontWeight.BOLD), ft.Text(rotulo, color=ft.Colors.GREY_400)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def preencher(perfil: dict):
        texto_nome.value = perfil.get("display_name") or perfil["username"]
        texto_usuario.value = f"@{perfil['username']}"
        texto_local.value = perfil.get("cidade") or "Cidade não informada"
        texto_bio.value = perfil.get("bio") or ""
        input_nome.value = perfil.get("display_name") or perfil["username"]
        input_cidade.value = perfil.get("cidade") or ""
        input_bio.value = perfil.get("bio") or ""

    def card_historico(s: dict):
        rotulo, cor, icone = STATUS.get(s["status"], (s["status"], ft.Colors.GREY_400, ft.Icons.HELP))
        titulo = (s.get("problems") or {}).get("title", "Desafio")
        data = str(s.get("created_at", ""))[:16].replace("T", " ")
        return cartao(
            ft.Row([
                ft.Column([
                    ft.Text(titulo, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"{data} • Python • {s['passed']}/{s['total']} testes", color=ft.Colors.GREY_400, size=12),
                ], spacing=2),
                ft.Row([ft.Text(rotulo, color=cor, weight=ft.FontWeight.BOLD), ft.Icon(icone, color=cor, size=20)], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

    async def carregar():
        try:
            dados = await api.get("/me")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            estatisticas.controls = [ft.Text(mensagem_erro(exc), color=ft.Colors.RED_300)]
            page.update()
            return
        state.session.profile = dados["profile"]
        state.save_session()
        preencher(dados["profile"])
        st = dados.get("stats", {})
        estatisticas.controls = [
            estat(dados["profile"]["points"], "Pontos"),
            ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
            estat(st.get("solved", 0), "Resolvidos"),
            ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
            estat(f"#{st.get('rank', '-')}", "Ranking"),
        ]
        historico.controls = [card_historico(s) for s in dados.get("submissions", [])] or [
            ft.Text("Nenhuma submissão ainda. Resolva seu primeiro desafio!", color=ft.Colors.GREY_400)
        ]
        page.update()

    def fechar_modal(e):
        modal.open = False
        page.update()

    async def salvar():
        erro_modal.value = ""
        try:
            r = await api.patch("/me", {
                "display_name": input_nome.value or "",
                "cidade": input_cidade.value or "",
                "bio": input_bio.value or "",
            })
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            erro_modal.value = mensagem_erro(exc)
            page.update()
            return
        state.session.profile = r["profile"]
        state.save_session()
        preencher(r["profile"])
        modal.open = False
        page.update()

    modal = ft.AlertDialog(
        title=ft.Text("Editar perfil", weight=ft.FontWeight.BOLD),
        content=ft.Column([input_nome, input_cidade, input_bio, erro_modal], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            botao("Salvar alterações", lambda e: page.run_task(salvar)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )

    def abrir_modal(e):
        if modal not in page.overlay:
            page.overlay.append(modal)
        modal.open = True
        page.update()

    async def sair():
        await api.logout()
        navegar("login")

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column([
            ft.Text("Meu perfil", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Row([
                ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON, size=40), radius=40, bgcolor=ft.Colors.BLUE_700),
                ft.Column([
                    ft.Row([
                        texto_nome,
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE_400, tooltip="Editar perfil", on_click=abrir_modal),
                    ], spacing=5),
                    texto_usuario,
                    texto_local,
                    texto_bio,
                ], spacing=2),
            ], spacing=20),
            ft.Divider(height=30, color=ft.Colors.OUTLINE),
            estatisticas,
            ft.Divider(height=30, color=ft.Colors.OUTLINE),
            ft.Text("Histórico de submissões", size=20, weight=ft.FontWeight.BOLD),
            historico,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Row([botao("Terminar sessão", lambda e: page.run_task(sair), ft.Colors.RED_700, ft.Icons.LOGOUT)]),
        ], scroll=ft.ScrollMode.AUTO),
        padding=20,
        expand=True,
    )
