import flet as ft

from src.services import api
from src.services.viacep import consultar_cep_async
from src.ui.helpers import mensagem_erro


def tela_cadastro(page: ft.Page, navegar):
    campo_usuario = ft.TextField(
        label="Nome de usuário",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        max_length=20,
    )
    campo_email = ft.TextField(
        label="E-mail",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    campo_senha = ft.TextField(
        label="Senha (mínimo 8 caracteres)",
        password=True,
        can_reveal_password=True,
        width=350,
        bgcolor=ft.Colors.GREEN_900,
    )
    cep = ft.TextField(
        label="CEP (opcional)",
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

    async def validar_cep():
        if not (cep.value or "").strip():
            cidade.value = ""
            feedback_cep.value = ""
            page.update()
            return
        feedback_cep.value = "Consultando CEP..."
        feedback_cep.color = ft.Colors.BLUE_400
        page.update()

        dados_endereco = await consultar_cep_async(cep.value or "")
        if dados_endereco:
            cidade.value = f"{dados_endereco.get('localidade', '')} - {dados_endereco.get('uf', '')}"
            feedback_cep.value = ""
        else:
            cidade.value = ""
            feedback_cep.value = "CEP inválido, não encontrado ou serviço indisponível."
            feedback_cep.color = ft.Colors.RED
        page.update()

    cep.on_blur = lambda e: page.run_task(validar_cep)

    async def criar_conta():
        feedback_cadastro.color = ft.Colors.RED_300
        botao_criar_conta.disabled = True
        feedback_cadastro.value = "Criando conta..."
        page.update()
        try:
            resultado = await api.signup(
                (campo_email.value or "").strip(),
                campo_senha.value or "",
                (campo_usuario.value or "").strip(),
                cidade.value or "",
            )
        except Exception as exc:  # noqa: BLE001
            feedback_cadastro.value = mensagem_erro(exc)
            botao_criar_conta.disabled = False
            page.update()
            return

        if resultado.get("needs_confirmation"):
            feedback_cadastro.color = ft.Colors.GREEN_300
            feedback_cadastro.value = (
                "Conta criada! Enviamos um e-mail de confirmação. "
                "Confirme-o e depois faça login."
            )
            botao_criar_conta.disabled = False
            page.update()
            return
        feedback_cadastro.value = ""
        navegar("login")

    botao_criar_conta = ft.Button(
        content=ft.Text("Criar conta"),
        width=350,
        on_click=lambda e: page.run_task(criar_conta),
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Crie seu cadastro", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_usuario,
            ft.Text("3 a 20 caracteres: letras, números e _", size=12, color=ft.Colors.GREY_400),
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
