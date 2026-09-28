import flet as ft

def tela_perfil(page: ft.Page, navegar):
    # Simulando variáveis que viriam do seu banco de dados (Supabase)
    cidade_usuario = "Manaus"
    uf_usuario = "AM"
    nome_usuario = "Flávio Alves"
    curso_usuario = "Engenharia de Software"
    faculdade = "FAMETRO"

    # Estatísticas principais
    linha_estatisticas = ft.Row([
        ft.Column([ft.Text("1100", size=24, weight=ft.FontWeight.BOLD), ft.Text("Pontos", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("15", size=24, weight=ft.FontWeight.BOLD), ft.Text("Desafios", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("Python", size=24, weight=ft.FontWeight.BOLD), ft.Text("Linguagem", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    def deslogar(e):
        navegar("login")

    # Botão para terminar sessão
    botao_sair = ft.Container(
        content=ft.Text("Terminar Sessão", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.RED_700,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=deslogar
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
                    ft.Text(f"{nome_usuario}", size=24, weight=ft.FontWeight.BOLD),
                    # Usando f-strings para interpolar as variáveis
                    ft.Text(f"{curso_usuario} | {faculdade}", color=ft.Colors.GREY_400, size=16),
                    ft.Text(f"{cidade_usuario} - {uf_usuario}", color=ft.Colors.GREY_400, size=16),
                ], spacing=2)
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(height=40, color=ft.Colors.OUTLINE),
            linha_estatisticas,
            ft.Divider(height=40, color=ft.Colors.OUTLINE),
            
            # Removido o on_click inválido da Row
            ft.Row([botao_sair], alignment=ft.MainAxisAlignment.START)
        ]),
        padding=20,
        expand=True
    )