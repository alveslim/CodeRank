import flet as ft
from src.services.viacep import consultar_cep
from src.services.backend import BackendError
from src.ui.state import get_state

def tela_cadastro(page: ft.Page, navegar):
    campo_nome = ft.TextField(label="Nome", width=350, bgcolor=ft.Colors.GREEN_900)
    campo_email = ft.TextField(label="E-mail", width=350, bgcolor=ft.Colors.GREEN_900)
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=350, bgcolor=ft.Colors.GREEN_900)
    cep = ft.TextField(label="Digite seu CEP", width=350, bgcolor=ft.Colors.GREEN_900, max_length=9)
    cidade = ft.TextField(label="Cidade", width=350, bgcolor=ft.Colors.GREEN_900, read_only=True)
    feedback_cep = ft.Text(value="", color=ft.Colors.RED)
    feedback = ft.Text(value="", color=ft.Colors.RED_300, width=350)
    endereco = {"city": "", "state": ""}
    state = get_state(page)
    
    def criar_conta(e):
        feedback.value = ""
        if not (campo_nome.value or "").strip():
            feedback.value = "Informe seu nome."
            page.update()
            return
        try:
            session = state.backend.sign_up(
                campo_email.value or "",
                campo_senha.value or "",
                {
                    "name": campo_nome.value.strip(),
                    "cep": "".join(filter(str.isdigit, cep.value or "")),
                    "city": endereco["city"],
                    "state": endereco["state"],
                    "course": "Engenharia de Software",
                    "institution": "FAMETRO",
                },
            )
            if session is None:
                feedback.color = ft.Colors.GREEN_300
                feedback.value = "Cadastro recebido. Confirme seu e-mail antes de entrar."
                page.update()
                return
            state.session = session
            navegar("desafios")
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
            page.update()
        
    def validar_cep(e):
        # Mostra indicador de que está a buscar
        feedback_cep.value = "A procurar código postal..."
        feedback_cep.color = ft.Colors.BLUE_400
        page.update()

        # Chama a função limpa que está no outro ficheiro
        dados_endereco = consultar_cep(cep.value)

        if dados_endereco:
            # Preenche os campos se encontrar
            endereco["city"] = dados_endereco.get("localidade", "")
            endereco["state"] = dados_endereco.get("uf", "")
            cidade.value = f"{endereco['city']} - {endereco['state']}"
            feedback_cep.value = ""
        else:
            endereco["city"] = ""
            endereco["state"] = ""
            cidade.value = ""
            feedback_cep.value = "CEP inválido ou não encontrado."
            feedback_cep.color = ft.Colors.RED

        page.update()
    cep.on_blur = validar_cep

    botao_criarConta = ft.Container(
        content=ft.Text("Criar conta", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREEN_700,
        padding=12,
        alignment=ft.Alignment.CENTER,
        width=350,
        border_radius=5,
        ink=True,
        on_click=criar_conta
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Faça cadastro para competir", color=ft.Colors.GREY_400),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_nome,
            campo_email,
            campo_senha,
            cep,
            feedback_cep,     
            cidade,
            feedback,
            botao_criarConta,
            ft.TextButton("Já possui uma conta?", on_click=lambda e: navegar("login"))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO),
        expand=True,
        alignment=ft.Alignment.CENTER
    )
