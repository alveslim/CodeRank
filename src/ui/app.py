import flet as ft

from src.ui.components.navbar import criar_navbar
from src.ui.views.cadastro import tela_cadastro
from src.ui.views.desafios import tela_desafios
from src.ui.views.editor import tela_editor
from src.ui.views.grupo import tela_grupo
from src.ui.views.lobby_grupos import tela_grupos
from src.ui.views.login import tela_login
from src.ui.views.perfil import tela_perfil
from src.ui.views.ranking import tela_ranking


ROTAS_VALIDAS = {
    "login",
    "cadastro",
    "desafios",
    "editor",
    "lobby_grupos",
    "grupo",
    "ranking",
    "perfil",
}


def main_ui(page: ft.Page):
    page.title = "CodeRank"
    page.theme_mode = ft.ThemeMode.DARK

    conteudo_principal = ft.Container(expand=True)

    def navegar(rota: str) -> None:
        # Compatibilidade com o nome antigo usado por versões anteriores da tela.
        if rota == "grupos":
            rota = "lobby_grupos"
        if rota not in ROTAS_VALIDAS:
            rota = "login"

        if rota == "login":
            page.appbar = None
            conteudo_principal.content = tela_login(page, navegar)
        elif rota == "cadastro":
            page.appbar = None
            conteudo_principal.content = tela_cadastro(page, navegar)
        else:
            page.appbar = barra_navegacao
            telas = {
                "desafios": lambda: tela_desafios(page, navegar),
                "editor": lambda: tela_editor(page),
                "lobby_grupos": lambda: tela_grupos(page, navegar),
                "grupo": lambda: tela_grupo(page, navegar),
                "ranking": lambda: tela_ranking(page, navegar),
                "perfil": lambda: tela_perfil(page, navegar),
            }
            conteudo_principal.content = telas[rota]()

        page.update()

    barra_navegacao = criar_navbar(page, navegar)

    page.clean()
    page.add(conteudo_principal)
    navegar("login")
