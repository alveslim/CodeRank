import asyncio
import time

import flet as ft

from src.services.backend import BackendError
from src.services.code_runner import run_code
from src.ui.state import get_state


EXAMPLES = {
    "python": 'print(2 + 3)',
    "java": """public class Main {
    public static void main(String[] args) {
        System.out.println(2 + 3);
    }
}""",
}


def tela_editor(page: ft.Page, navegar):
    state = get_state(page)
    try:
        challenges = state.backend.list_challenges()
        challenge = next(
            (item for item in challenges if item["id"] == state.selected_challenge_id),
            challenges[0] if challenges else None,
        )
    except BackendError as exc:
        return ft.Container(content=ft.Text(str(exc), color=ft.Colors.RED_300), padding=20)

    if challenge is None:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Nenhum desafio disponivel."),
                    ft.TextButton("Voltar", on_click=lambda e: navegar("desafios")),
                ]
            ),
            padding=20,
        )
    state.selected_challenge_id = challenge["id"]
    initial_language = challenge["language"] if challenge["language"] != "any" else "python"

    linguagem = ft.Dropdown(
        label="Linguagem",
        value=initial_language,
        width=180,
        disabled=challenge["language"] != "any",
        options=[
            ft.DropdownOption(key="python", text="Python 3"),
            ft.DropdownOption(key="java", text="Java 21"),
        ],
    )
    entrada_codigo = ft.TextField(
        value=EXAMPLES[initial_language],
        multiline=True,
        min_lines=16,
        text_style=ft.TextStyle(font_family="monospace", size=14),
        expand=True,
        bgcolor=ft.Colors.GREY_900,
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE)),
    )
    saida = ft.Text(
        "A saida da execucao aparecera aqui.",
        selectable=True,
        font_family="monospace",
        color=ft.Colors.GREY_300,
    )
    resultado_desafio = ft.Text("", weight=ft.FontWeight.BOLD)
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
        resultado_desafio.value = ""
        saida.value = "Executando em conteiner isolado..."
        saida.color = ft.Colors.BLUE_200
        page.update()

        started = time.perf_counter()
        try:
            resultado = await asyncio.to_thread(
                run_code,
                linguagem.value,
                entrada_codigo.value or "",
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            blocos = []
            if resultado.stdout:
                blocos.append(resultado.stdout.rstrip())
            if resultado.stderr:
                blocos.append(resultado.stderr.rstrip())
            saida.value = "\n".join(blocos) or "Programa finalizado sem saida."
            saida.color = ft.Colors.GREEN_300 if resultado.succeeded else ft.Colors.RED_300

            correct = (
                resultado.succeeded
                and resultado.stdout.strip().replace("\r\n", "\n")
                == str(challenge["expected_output"]).strip().replace("\r\n", "\n")
            )
            submission = state.backend.record_submission(
                challenge_id=challenge["id"],
                group_id=state.selected_group_id,
                language=linguagem.value,
                source_code=entrada_codigo.value or "",
                stdout=resultado.stdout,
                stderr=resultado.stderr,
                exit_code=resultado.exit_code,
                correct=correct,
                execution_ms=elapsed_ms,
            )
            if correct:
                awarded = submission.get("points_awarded", 0)
                resultado_desafio.value = (
                    f"Resposta aceita! +{awarded} pontos."
                    if awarded
                    else "Resposta aceita. Este desafio ja havia sido pontuado."
                )
                resultado_desafio.color = ft.Colors.GREEN_300
            else:
                resultado_desafio.value = (
                    f"Resposta incorreta. Saida esperada: {challenge['expected_output']}"
                )
                resultado_desafio.color = ft.Colors.RED_300
        except (RuntimeError, ValueError, BackendError) as exc:
            saida.value = str(exc)
            saida.color = ft.Colors.RED_300
        finally:
            botao_executar.disabled = False
            progresso.visible = False
            page.update()

    def iniciar_execucao(e):
        page.run_task(executar_codigo)

    botao_executar = ft.Button(
        content=ft.Text("Executar codigo", weight=ft.FontWeight.BOLD),
        icon=ft.Icons.PLAY_ARROW,
        bgcolor=ft.Colors.GREEN_700,
        color=ft.Colors.WHITE,
        on_click=iniciar_execucao,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(f"Desafio: {challenge['title']}", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(challenge["description"]),
                ft.Text(
                    f"Saida esperada: {challenge['expected_output']} • Vale {challenge['points']} pontos",
                    color=ft.Colors.GREY_400,
                ),
                linguagem,
                entrada_codigo,
                ft.Row(
                    [progresso, botao_executar],
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                resultado_desafio,
                ft.Text("Saida", size=16, weight=ft.FontWeight.BOLD),
                painel_saida,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
