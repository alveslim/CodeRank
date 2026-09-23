import flet as ft
from src.ui.views.editor import tela_editor
from src.ui.views.desafios import tela_desafios
from src.ui.components.navbar import criar_navbar

def main_ui(page: ft.Page):
    page.title = "CodeRank"
    page.theme_mode = ft.ThemeMode.DARK

    conteudo_principal = ft.Container(expand=True)

    def navegar(rota):
        if rota == 'desafios':
            conteudo_principal.content = tela_desafios(page, navegar)
        elif rota == 'editor':
                    conteudo_principal.content = tela_editor(page)
        page.update()

    page.appbar = criar_navbar(page, navegar)
    page.clean()
    page.add(conteudo_principal)
    navegar("desafios")
