import flet as ft
from src.services.viacep import consultar_cep
import requests

def tela_cadastro(page: ft.Page, navegar):
    campo_email = ft.TextField(label="E-mail", width=350, bgcolor=ft.Colors.GREEN_900)
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=350, bgcolor=ft.Colors.GREEN_900)
    cep = ft.TextField(label="Digite seu Cep", width=350, bgcolor=ft.Colors.GREEN_900, max_length=9)
    cidade = ft.TextField(label="Cidade", width=350, bgcolor=ft.Colors.GREEN_900, read_only=True)
    feedback_cep = ft.Text(value="", color=ft.Colors.RED)
    
    def simular_login(e):
        print(f'Conta criada com: {campo_email.value}')
        # feat: A chamada para a supabase auth aqui
        # Apos o sucesso, redirecionar para a tela princiapl
        navegar("desafios")
        
    def validar_cep(e):
        # Mostra indicador de que está a buscar
        feedback_cep.value = "A procurar código postal..."
        feedback_cep.color = ft.Colors.BLUE_400
        page.update()

        # Chama a função limpa que está no outro ficheiro
        dados_endereco = consultar_cep(cep.value)

        if dados_endereco:
            # Preenche os campos se encontrar
            cidade.value = f"{dados_endereco.get('localidade', '')} - {dados_endereco.get('uf', '')}"
            feedback_cep.value = "" # Limpa a mensagem de busca
        else:
            cidade.value = ""
            feedback_cep.value = "Código postal inválido ou não encontrado."
            feedback_cep.color = ft.Colors.RED

        page.update() # Atualiza o ecrã com os novos valores
    cep.on_blur = validar_cep

    botao_criarConta = ft.Container(
        content=ft.Text("Criar conta", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
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
            ft.Text("Faça Casdastro para competir", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            cep,
            feedback_cep,     
            cidade,
            botao_criarConta,
            ft.TextButton("Já possui uma conta?", on_click=lambda e: navegar("login"))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO),
        expand=True,
        alignment=ft.Alignment.CENTER
    )