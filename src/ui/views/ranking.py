import flet as ft


def tela_ranking(page: ft.Page, navegar):
    def criar_linha_ranking(posicao, nome, pontuacao, cor_destaque=ft.Colors.TRANSPARENT):
        return ft.Container(
            content=ft.Row([
                ft.Text(f"#{posicao}", weight=ft.FontWeight.BOLD, size=18, width=40),
                ft.Text(nome, size=16, expand=True),
                ft.Text(f"{pontuacao} pts", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.AMBER_400),
            ]),
            padding=15,
            bgcolor=cor_destaque if cor_destaque != ft.Colors.TRANSPARENT else ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )

    # Dados ilustrativos até a integração com o backend ser disponibilizada na main.
    lista_ranking = ft.Column([
        criar_linha_ranking(1, "Ana Exemplo", 1200, ft.Colors.BLUE_900),
        criar_linha_ranking(2, "Bruno Exemplo", 1160),
        criar_linha_ranking(3, "Carla Exemplo", 300),
    ], spacing=10)

    return ft.Container(
        content=ft.Column([
            ft.Text("Ranking Global — demonstração", size=28, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Classificação ilustrativa. A pontuação ainda não vem de submissões persistidas.",
                color=ft.Colors.GREY_400,
            ),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            lista_ranking,
        ]),
        padding=20,
        expand=True,
    )
