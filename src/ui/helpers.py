"""Componentes e utilitários compartilhados pelas telas."""

import flet as ft

from src import state
from src.services.api import ApiError

DIFICULDADES = {
    "facil": ("Fácil", ft.Colors.GREEN_400),
    "medio": ("Médio", ft.Colors.ORANGE_400),
    "dificil": ("Difícil", ft.Colors.RED_400),
}


def rotulo_dificuldade(chave: str) -> tuple[str, str]:
    return DIFICULDADES.get(chave, (chave, ft.Colors.GREY_400))


def sessao_expirada(exc: Exception, navegar) -> bool:
    """Se a API respondeu 401, limpa a sessão e volta ao login. Retorna True se tratou."""
    if isinstance(exc, ApiError) and exc.status == 401:
        state.clear_session()
        navegar("login")
        return True
    return False


def mensagem_erro(exc: Exception) -> str:
    return exc.message if isinstance(exc, ApiError) else "Algo deu errado. Tente novamente."


def botao(texto: str, on_click, cor=ft.Colors.BLUE_700, icone=None, largura=None):
    conteudo = [ft.Text(texto, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)]
    if icone:
        conteudo.insert(0, ft.Icon(icone, color=ft.Colors.WHITE, size=18))
    return ft.Container(
        content=ft.Row(conteudo, spacing=6, alignment=ft.MainAxisAlignment.CENTER, tight=True),
        bgcolor=cor,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=on_click,
        width=largura,
    )


def cartao(conteudo, destaque=None):
    return ft.Container(
        content=conteudo,
        padding=15,
        bgcolor=destaque or ft.Colors.GREY_900,
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        margin=ft.Margin.only(bottom=10),
    )


def carregando():
    return ft.Row([ft.ProgressRing(width=24, height=24)], alignment=ft.MainAxisAlignment.CENTER)
