import flet as ft

from src import state
from src.services import api
from src.ui.helpers import botao, cartao, carregando, mensagem_erro, rotulo_dificuldade, sessao_expirada


def tela_grupo(page: ft.Page, navegar):
    titulo = ft.Text("Carregando grupo...", size=28, weight=ft.FontWeight.BOLD)
    subtitulo = ft.Text("", color=ft.Colors.GREY_400, size=14)
    acao_grupo = ft.Row([])
    lista_desafios = ft.Column([carregando()], scroll=ft.ScrollMode.AUTO)
    lista_membros = ft.Column([], scroll=ft.ScrollMode.AUTO)
    area_conteudo = ft.Container(content=lista_desafios, padding=20, expand=True)

    def voltar(e):
        navegar("lobby_grupos")

    def abrir_desafio(slug: str):
        def _abrir(e):
            state.session.selected_problem = slug
            navegar("editor")

        return _abrir

    def card_desafio(p: dict):
        rotulo, cor = rotulo_dificuldade(p["difficulty"])
        resolvido = p.get("solved")
        return cartao(ft.Row([
            ft.Column([
                ft.Text(p["title"], weight=ft.FontWeight.BOLD, size=18),
                ft.Text(f"{rotulo} • {p['points']} pts", color=cor, size=14),
            ], spacing=2),
            botao("Resolvido" if resolvido else "Resolver", abrir_desafio(p["slug"]),
                  ft.Colors.GREY_700 if resolvido else ft.Colors.GREEN_700),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    def card_membro(posicao: int, m: dict, eu: bool):
        marca = (
            ft.Icon(ft.Icons.STAR, color=ft.Colors.YELLOW_600, tooltip="Administrador")
            if m.get("owner")
            else ft.Container(width=24)
        )
        return cartao(ft.Row([
            ft.Row([
                ft.Text(f"#{posicao}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON), bgcolor=ft.Colors.BLUE_700),
                ft.Text(m.get("display_name") or m.get("username") or "?", size=16, weight=ft.FontWeight.W_500),
            ], spacing=15),
            ft.Row([ft.Text(f"{m['points']} pts", size=16, color=ft.Colors.YELLOW_400, weight=ft.FontWeight.BOLD), marca], spacing=10),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), destaque=ft.Colors.BLUE_900 if eu else None)

    async def sair():
        try:
            await api.post(f"/groups/{state.session.selected_group}/leave")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            subtitulo.value = mensagem_erro(exc)
            page.update()
            return
        navegar("lobby_grupos")

    async def entrar():
        try:
            await api.post(f"/groups/{state.session.selected_group}/join")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            subtitulo.value = mensagem_erro(exc)
            page.update()
            return
        await carregar()

    async def carregar():
        gid = state.session.selected_group
        if not gid:
            navegar("lobby_grupos")
            return
        try:
            g, probs = await api.get(f"/groups/{gid}"), await api.get("/problems")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            titulo.value = "Não foi possível abrir o grupo"
            subtitulo.value = mensagem_erro(exc)
            lista_desafios.controls = []
            page.update()
            return

        grupo, membros = g["group"], g["members"]
        meu_id = (state.session.user or {}).get("id")
        titulo.value = grupo["name"]
        subtitulo.value = f"Código de convite: {gid:05d}" + (f" • {grupo['description']}" if grupo.get("description") else "")
        acao_grupo.controls = [
            botao("Sair do grupo", lambda e: page.run_task(sair), ft.Colors.RED_700, ft.Icons.LOGOUT)
            if grupo["member"]
            else botao("Entrar no grupo", lambda e: page.run_task(entrar), ft.Colors.GREEN_700, ft.Icons.LOGIN)
        ]
        lista_desafios.controls = [card_desafio(p) for p in probs["problems"]]
        lista_membros.controls = [card_membro(i + 1, m, m["user_id"] == meu_id) for i, m in enumerate(membros)]
        page.update()

    def mudar_aba(aba: str):
        def _mudar(e):
            if aba == "desafios":
                area_conteudo.content = lista_desafios
                btn_desafios.bgcolor = ft.Colors.BLUE_700
                btn_membros.bgcolor = ft.Colors.GREY_800
            else:
                area_conteudo.content = lista_membros
                btn_desafios.bgcolor = ft.Colors.GREY_800
                btn_membros.bgcolor = ft.Colors.BLUE_700
            page.update()

        return _mudar

    btn_desafios = botao("Desafios", mudar_aba("desafios"), ft.Colors.BLUE_700, ft.Icons.CODE)
    btn_membros = botao("Membros & ranking", mudar_aba("membros"), ft.Colors.GREY_800, ft.Icons.PEOPLE)

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=voltar, tooltip="Voltar aos grupos"),
                ft.Column([titulo, subtitulo], spacing=0, expand=True),
                acao_grupo,
            ]),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Column([
                ft.Row([btn_desafios, btn_membros], spacing=10),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                area_conteudo,
            ], expand=True),
        ], expand=True),
        padding=20,
        expand=True,
    )
