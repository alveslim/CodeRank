import flet as ft

def tela_perfil(page: ft.Page, navegar):
    # Estatísticas principais
    linha_estatisticas = ft.Row([
        ft.Column([ft.Text("1100", size=24, weight=ft.FontWeight.BOLD), ft.Text("Pontos", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("15", size=24, weight=ft.FontWeight.BOLD), ft.Text("Desafios", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("Python", size=24, weight=ft.FontWeight.BOLD), ft.Text("Linguagem", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    ], alignment=ft.MainAxisAlignment.CENTER)

    # Botão para terminar sessão
    botao_sair = ft.Container(
        content=ft.Text("Terminar Sessão", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.RED_700,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=lambda e: print("Ação: Sair da conta")
    )

    return ft.Container(
        content=ft.Column([
            ft.Text("O Meu Perfil", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            
            # Cabeçalho do Perfil
            ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, size=40),
                    radius=40,
                    bgcolor=ft.Colors.BLUE_700
                ),
                ft.Column([
                    ft.Text("Flávio Alves", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Engenharia de Software | FAMETRO", color=ft.Colors.GREY_400, size=16),
                ], spacing=2)
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(height=40, color=ft.Colors.OUTLINE),
            linha_estatisticas,
            ft.Divider(height=40, color=ft.Colors.OUTLINE),
            
            ft.Row([botao_sair], alignment=ft.MainAxisAlignment.START)
        ]),
        padding=20,
        expand=True
    )