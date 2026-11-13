import flet as ft


def tela_login(page: ft.Page, navegar):
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
    feedback = ft.Text("", color=ft.Colors.RED_300, width=350, text_align=ft.TextAlign.CENTER)

    def informar_indisponibilidade(e):
        feedback.value = (
            "A autenticação ainda não está conectada a um backend nesta branch. "
            "Nenhuma conta ou sessão foi criada."
        )
        page.update()

    botao_entrar = ft.Button(
        content=ft.Text("Entrar na conta"),
        width=350,
        on_click=informar_indisponibilidade,
    )

    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CODE, size=80, color=ft.Colors.BLUE_400),
            ft.Text("CodeRank", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Entre para competir", color=ft.Colors.GREY_400),
            ft.Text("Protótipo local — autenticação não integrada", color=ft.Colors.AMBER_300),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            campo_email,
            campo_senha,
            botao_entrar,
            feedback,
            ft.TextButton(
                "Ainda não tem conta? Ver cadastro",
                on_click=lambda e: navegar("cadastro"),
            ),
            ft.TextButton(
                "Explorar o protótipo sem login",
                on_click=lambda e: navegar("desafios"),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        expand=True,
        alignment=ft.Alignment.CENTER,
    )
