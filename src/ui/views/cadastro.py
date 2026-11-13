import flet as ft

from src.services.viacep import consultar_cep


def tela_cadastro(page: ft.Page, navegar):
    campo_email = ft.TextField(
        label="E-mail",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    campo_senha = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        width=350,
        bgcolor=ft.Colors.GREEN_900,
    )
    cep = ft.TextField(
        label="Digite seu CEP",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        max_length=9,
    )
    cidade = ft.TextField(
        label="Cidade",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        read_only=True,
    )
    feedback_cep = ft.Text(value="", color=ft.Colors.RED)
    feedback_cadastro = ft.Text(
        value="",
        color=ft.Colors.RED_300,
        width=350,
        text_align=ft.TextAlign.CENTER,
    )

    def informar_indisponibilidade(e):
        feedback_cadastro.value = (
            "O cadastro ainda não está conectado a um backend nesta branch. "
            "Nenhuma conta foi criada."
        )
        page.update()

    def validar_cep(e):
        feedback_cep.value = "Consultando CEP..."
        feedback_cep.color = ft.Colors.BLUE_400
        page.update()

        dados_endereco = consultar_cep(cep.value or "")
        if dados_endereco:
            cidade.value = f"{dados_endereco.get('localidade', '')} - {dados_endereco.get('uf', '')}"
            feedback_cep.value = ""
        else:
            cidade.value = ""
            feedback_cep.value = "CEP inválido, não encontrado ou serviço indisponível."
            feedback_cep.color = ft.Colors.RED

        page.update()

    cep.on_blur = validar_cep

    botao_criar_conta = ft.Button(
        content=ft.Text("Criar conta"),
        width=350,
        on_click=informar_indisponibilidade,
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Crie seu cadastro", color=ft.Colors.GREY_400),
            ft.Text("Protótipo local — cadastro não integrado", color=ft.Colors.AMBER_300),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            cep,
            feedback_cep,
            cidade,
            botao_criar_conta,
            feedback_cadastro,
            ft.TextButton(
                "Já possui uma conta? Entrar",
                on_click=lambda e: navegar("login"),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
        expand=True,
        alignment=ft.Alignment.CENTER,
    )
