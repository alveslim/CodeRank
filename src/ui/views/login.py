import flet as ft 

def tela_login(page: ft.Page, navegar):
    campo_email = ft.TextField(label="E-mail", width=350, bgcolor=ft.Colors.GREEN_900)
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=350, bgcolor=ft.Colors.GREEN_900)

    def simular_login(e):
        print(f'Autenticando Usuario: {campo_email.value}')
        # feat: A chamada para a supabase auth aqui
        # Apos o sucesso, redirecionar para a tela princiapl
        navegar("desafios")

    botao_entrar = ft.Container(
        content=ft.Text("Entrar na Conta", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREEN_700,
        padding=12,
        alignment=ft.Alignment.CENTER,
        width=350,
        border_radius=5,
        ink=True,
        on_click=simular_login
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Faça login para competir", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            botao_entrar,
            ft.TextButton("Ainda não tem conta? Registre-se", on_click=lambda e: print("Ir para registro"))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        expand=True,
        alignment=ft.Alignment.CENTER
    )