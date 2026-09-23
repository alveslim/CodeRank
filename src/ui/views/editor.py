import flet as ft 

def tela_editor(page: ft.Page):
    entrada_codigo = ft.TextField(
        multiline=True,
        min_lines=20,
        text_style=ft.TextStyle(font_family="monospace", size=14),
        hint_text="#include <stdio.h> \n       int main(void) {\n              printf('Hello World!');\n       return 0;\n       }\n       # Escreva seu código aqui...",
        expand=True,
        bgcolor=ft.Colors.GREY_900,
        border_color=ft.Colors.OUTLINE
    )

    def simular_execucao(e):
        print("Codigo capturado pela interface: ")
        print(entrada_codigo.value)
        # conectar a funcao ao motor docker

    botao_executar = ft.Container(
        content=ft.Text("Executar Código", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.GREEN_700,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=simular_execucao
    )

    return ft.Container(
            content=ft.Column([
                ft.Text("Problema: Two Sum", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Retorne os índices de dois números que somam ao alvo."),
                entrada_codigo,
                ft.Row([botao_executar], alignment=ft.MainAxisAlignment.END)
            ]),
            padding=20,
            expand=True
        )