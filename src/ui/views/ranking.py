import flet as ft

from src import state
from src.services import api
from src.ui.helpers import carregando, mensagem_erro, sessao_expirada


def tela_ranking(page: ft.Page, navegar):
    lista = ft.Column([carregando()], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def linha(posicao: int, r: dict, eu: bool):
        return ft.Container(
            content=ft.Row([
                ft.Text(f"#{posicao}", weight=ft.FontWeight.BOLD, size=18, width=50),
                ft.Column([
                    ft.Text(r.get("display_name") or r["username"], size=16),
                    ft.Text(f"@{r['username']} • {r.get('solved', 0)} resolvidos", size=12, color=ft.Colors.GREY_400),
                ], spacing=0, expand=True),
                ft.Text(f"{r['points']} pts", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.AMBER_400),
            ]),
            padding=15,
            bgcolor=ft.Colors.BLUE_900 if eu else ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )

    async def carregar():
        try:
            dados = await api.get("/ranking", auth=False)
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            lista.controls = [ft.Text(mensagem_erro(exc), color=ft.Colors.RED_300)]
            page.update()
            return
        meu = (state.session.profile or {}).get("username")
        lista.controls = [linha(i + 1, r, r["username"] == meu) for i, r in enumerate(dados["ranking"])] or [
            ft.Text("Ninguém pontuou ainda. Seja o primeiro!", color=ft.Colors.GREY_400)
        ]
        page.update()

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column([
            ft.Text("Ranking Global", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Pontos ganhos na primeira solução aceita de cada desafio.", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            lista,
        ], expand=True),
        padding=20,
        expand=True,
    )
