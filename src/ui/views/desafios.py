import flet as ft

from src import state
from src.services import api
from src.ui.helpers import botao, cartao, carregando, mensagem_erro, rotulo_dificuldade, sessao_expirada


def tela_desafios(page: ft.Page, navegar):
    lista = ft.Column([carregando()], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    def abrir(slug: str):
        def _abrir(e):
            state.session.selected_problem = slug
            navegar("editor")

        return _abrir

    def card(posicao: int, p: dict):
        rotulo, cor = rotulo_dificuldade(p["difficulty"])
        resolvido = p.get("solved")
        return cartao(
            ft.Row([
                ft.Row([
                    ft.Text(f"{posicao}. {p['title']}", weight=ft.FontWeight.BOLD, size=16),
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=18, visible=bool(resolvido)),
                ], spacing=8),
                ft.Row([
                    ft.Text(rotulo, color=cor),
                    ft.Text(f"{p['points']} pts", color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD),
                    botao("Revisar" if resolvido else "Resolver", abrir(p["slug"]),
                          ft.Colors.GREY_700 if resolvido else ft.Colors.BLUE_700),
                ], spacing=15),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        )

    async def carregar():
        try:
            dados = await api.get("/problems")
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            lista.controls = [ft.Text(mensagem_erro(exc), color=ft.Colors.RED_300)]
            page.update()
            return
        lista.controls = [card(i + 1, p) for i, p in enumerate(dados["problems"])] or [
            ft.Text("Nenhum desafio disponível ainda.", color=ft.Colors.GREY_400)
        ]
        page.update()

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column([
            ft.Text("Desafios Disponíveis", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            lista,
        ], expand=True),
        padding=20,
        expand=True,
    )
