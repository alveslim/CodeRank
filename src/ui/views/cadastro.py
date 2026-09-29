import flet as ft

from src.services.backend import BackendError
from src.services.viacep import CepError, consultar_cep, formatar_cep, limpar_cep
from src.ui.state import get_state


def tela_cadastro(page: ft.Page, navegar):
    campo_nome = ft.TextField(label="Nome", width=350, bgcolor=ft.Colors.GREEN_900)
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
        label="CEP (8 numeros)",
        hint_text="00000-000",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=9,
    )
    cidade = ft.TextField(
        label="Cidade",
        width=350,
        bgcolor=ft.Colors.GREEN_900,
        read_only=True,
    )
    feedback_cep = ft.Text(value="", color=ft.Colors.RED_300, width=350)
    feedback = ft.Text(value="", color=ft.Colors.RED_300, width=350)
    endereco = {"cep": "", "city": "", "state": ""}
    processando = {"value": False}
    state = get_state(page)

    def limpar_endereco():
        endereco.update({"cep": "", "city": "", "state": ""})
        cidade.value = ""

    def formatar_campo_cep(e):
        valor_formatado = formatar_cep(cep.value)
        if cep.value != valor_formatado:
            cep.value = valor_formatado
        if endereco["cep"] != limpar_cep(cep.value):
            limpar_endereco()
            feedback_cep.value = ""
        page.update()

    def carregar_endereco(*, mostrar_busca: bool = True) -> bool:
        cep_atual = limpar_cep(cep.value)
        if endereco["cep"] == cep_atual and endereco["city"] and endereco["state"]:
            return True

        if mostrar_busca:
            feedback_cep.value = "Consultando CEP..."
            feedback_cep.color = ft.Colors.BLUE_400
            page.update()

        try:
            dados_endereco = consultar_cep(cep.value)
        except CepError as exc:
            limpar_endereco()
            feedback_cep.value = str(exc)
            feedback_cep.color = ft.Colors.RED_300
            page.update()
            return False

        endereco["cep"] = limpar_cep(dados_endereco.get("cep", cep_atual))
        endereco["city"] = str(dados_endereco.get("localidade") or "")
        endereco["state"] = str(dados_endereco.get("uf") or "")
        cep.value = formatar_cep(endereco["cep"])
        cidade.value = f"{endereco['city']} - {endereco['state']}"
        feedback_cep.value = "CEP encontrado."
        feedback_cep.color = ft.Colors.GREEN_300
        page.update()
        return True

    def validar_cep(e):
        carregar_endereco()

    def criar_conta(e):
        if processando["value"]:
            return

        feedback.color = ft.Colors.RED_300
        feedback.value = ""
        nome = (campo_nome.value or "").strip()
        email = (campo_email.value or "").strip()
        senha = campo_senha.value or ""
        if len(nome) < 2:
            feedback.value = "Informe um nome com pelo menos 2 caracteres."
            page.update()
            return
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            feedback.value = "Informe um e-mail valido."
            page.update()
            return
        if len(senha) < 6:
            feedback.value = "A senha deve ter pelo menos 6 caracteres."
            page.update()
            return
        if not carregar_endereco(mostrar_busca=False):
            feedback.value = "Corrija o CEP antes de criar a conta."
            page.update()
            return

        processando["value"] = True
        botao_criar_conta.disabled = True
        botao_criar_conta.opacity = 0.6
        feedback.value = "Criando conta..."
        feedback.color = ft.Colors.BLUE_300
        page.update()
        try:
            session = state.backend.sign_up(
                email,
                senha,
                {
                    "name": nome,
                    "cep": endereco["cep"],
                    "city": endereco["city"],
                    "state": endereco["state"],
                    "course": "Engenharia de Software",
                    "institution": "FAMETRO",
                },
            )
            if session is None:
                feedback.color = ft.Colors.GREEN_300
                feedback.value = (
                    "Cadastro recebido. Confirme seu e-mail e depois entre pela tela de login."
                )
                return
            state.session = session
            navegar("desafios")
        except BackendError as exc:
            feedback.color = ft.Colors.RED_300
            feedback.value = str(exc)
        finally:
            processando["value"] = False
            botao_criar_conta.disabled = False
            botao_criar_conta.opacity = 1
            page.update()

    cep.on_change = formatar_campo_cep
    cep.on_blur = validar_cep

    botao_criar_conta = ft.Container(
        content=ft.Text(
            "Criar conta", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
        ),
        bgcolor=ft.Colors.GREEN_700,
        padding=12,
        alignment=ft.Alignment.CENTER,
        width=350,
        border_radius=5,
        ink=True,
        on_click=criar_conta,
    )

    return ft.Container(
        content=ft.Column(
            [
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
                botao_criar_conta,
                ft.TextButton(
                    "Já possui uma conta?", on_click=lambda e: navegar("login")
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        alignment=ft.Alignment.CENTER,
    )
