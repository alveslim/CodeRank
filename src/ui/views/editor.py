import asyncio

import flet as ft

from src.services.code_runner import run_code


EXAMPLES = {
    "python": 'print("Olá do sandbox Python!")',
    "java": """public class Main {
    public static void main(String[] args) {
        System.out.println("Olá do sandbox Java!");
    }
}""",
}


def tela_editor(page: ft.Page):
    linguagem = ft.Dropdown(
        label="Linguagem",
        value="python",
        width=180,
        options=[
            ft.DropdownOption(key="python", text="Python 3"),
            ft.DropdownOption(key="java", text="Java 21"),
        ],
    )
    entrada_codigo = ft.TextField(
        value=EXAMPLES["python"],
        multiline=True,
        min_lines=18,
        text_style=ft.TextStyle(font_family="monospace", size=14),
        expand=True,
        bgcolor=ft.Colors.GREY_900,
        border=ft.OutlineInputBorder(
            side=ft.BorderSide(color=ft.Colors.OUTLINE),
        ),
    )
    saida = ft.Text(
        "A saída da execução aparecerá aqui.",
        selectable=True,
        font_family="monospace",
        color=ft.Colors.GREY_300,
    )
    painel_saida = ft.Container(
        content=saida,
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=5,
        padding=12,
        width=float("inf"),
        height=110,
    )
    progresso = ft.ProgressRing(width=22, height=22, visible=False)

    def trocar_linguagem(e):
        selecionada = e.data if e.data in EXAMPLES else linguagem.value
        entrada_codigo.value = EXAMPLES[selecionada]
        entrada_codigo.update()

    linguagem.on_select = trocar_linguagem

    async def executar_codigo():
        botao_executar.disabled = True
        progresso.visible = True
        saida.value = "Executando em contêiner isolado..."
        saida.color = ft.Colors.BLUE_200
        page.update()

        try:
            resultado = await asyncio.to_thread(
                run_code,
                linguagem.value,
                entrada_codigo.value or "",
            )
            blocos = []
            if resultado.stdout:
                blocos.append(resultado.stdout.rstrip())
            if resultado.stderr:
                blocos.append(resultado.stderr.rstrip())
            saida.value = "\n".join(blocos) or "Programa finalizado sem saída."
            saida.color = (
                ft.Colors.GREEN_300 if resultado.succeeded else ft.Colors.RED_300
            )
        except (RuntimeError, ValueError) as exc:
            saida.value = str(exc)
            saida.color = ft.Colors.RED_300
        finally:
            botao_executar.disabled = False
            progresso.visible = False
            page.update()

    def iniciar_execucao(e):
        page.run_task(executar_codigo)

    botao_executar = ft.Button(
        content=ft.Text("Executar Código", weight=ft.FontWeight.BOLD),
        icon=ft.Icons.PLAY_ARROW,
        bgcolor=ft.Colors.GREEN_700,
        color=ft.Colors.WHITE,
        on_click=iniciar_execucao,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Problema: Two Sum", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Retorne os índices de dois números que somam ao alvo."),
                linguagem,
                entrada_codigo,
                ft.Row(
                    [progresso, botao_executar],
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text("Saída", size=16, weight=ft.FontWeight.BOLD),
                painel_saida,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
