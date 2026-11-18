import flet as ft

from src import state
from src.services import api
from src.ui.helpers import carregando, mensagem_erro, rotulo_dificuldade, sessao_expirada

STARTER = '# Leia a entrada com input() e imprima a resposta com print()\n'

STATUS_TEXTO = {
    "ok": "Executado com sucesso",
    "accepted": "Aceito",
    "wrong_answer": "Resposta incorreta",
    "runtime_error": "Erro de execução",
    "compile_error": "Erro de sintaxe",
    "timeout": "Tempo limite excedido",
    "output_limit": "Saída grande demais",
}


def tela_editor(page: ft.Page, navegar):
    estado = {"slug": None}

    titulo = ft.Text("Carregando desafio...", size=24, weight=ft.FontWeight.BOLD)
    meta = ft.Text("", color=ft.Colors.GREY_400)
    enunciado = ft.Text("", selectable=True)
    exemplo = ft.Text("", selectable=True, font_family="monospace", color=ft.Colors.GREY_300)

    entrada_codigo = ft.TextField(
        value=STARTER,
        multiline=True,
        min_lines=14,
        text_style=ft.TextStyle(font_family="monospace", size=14),
        expand=True,
        bgcolor=ft.Colors.GREY_900,
        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE)),
    )
    entrada_stdin = ft.TextField(
        label="Entrada (stdin) para o botão Executar",
        multiline=True,
        min_lines=1,
        max_lines=4,
        text_style=ft.TextStyle(font_family="monospace", size=13),
    )
    saida = ft.Text(
        "A saída aparecerá aqui.",
        selectable=True,
        font_family="monospace",
        color=ft.Colors.GREY_300,
    )
    painel_saida = ft.Container(
        content=ft.Column([saida], scroll=ft.ScrollMode.AUTO),
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=5,
        padding=12,
        width=float("inf"),
        height=130,
    )
    resultados = ft.Column([], spacing=2)
    progresso = ft.ProgressRing(width=22, height=22, visible=False)

    def ocupado(valor: bool):
        botao_executar.disabled = valor
        botao_enviar.disabled = valor
        progresso.visible = valor
        page.update()

    async def carregar():
        slug = state.session.selected_problem
        try:
            if not slug:
                lista = (await api.get("/problems"))["problems"]
                pendentes = [p for p in lista if not p.get("solved")]
                if not lista:
                    titulo.value = "Nenhum desafio disponível."
                    page.update()
                    return
                slug = (pendentes or lista)[0]["slug"]
                state.session.selected_problem = slug
            p = (await api.get(f"/problems/{slug}"))["problem"]
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            titulo.value = "Não foi possível carregar o desafio"
            saida.value = mensagem_erro(exc)
            saida.color = ft.Colors.RED_300
            page.update()
            return

        estado["slug"] = slug
        rotulo, cor = rotulo_dificuldade(p["difficulty"])
        titulo.value = p["title"]
        meta.value = f"{rotulo} • {p['points']} pontos" + (" • já resolvido" if p.get("solved") else "")
        meta.color = cor
        enunciado.value = p["description"]
        exemplo.value = f"Exemplo de entrada:\n{p['example_input']}\n\nSaída esperada:\n{p['example_output']}"
        entrada_stdin.value = p["example_input"]
        page.update()

    async def executar():
        if not estado["slug"]:
            return
        ocupado(True)
        resultados.controls = []
        saida.value = "Executando..."
        saida.color = ft.Colors.BLUE_200
        page.update()
        try:
            r = await api.post(
                f"/problems/{estado['slug']}/run",
                {"source": entrada_codigo.value or "", "stdin": entrada_stdin.value or ""},
            )
            blocos = []
            if r.get("stdout"):
                blocos.append(r["stdout"].rstrip())
            if r.get("stderr"):
                blocos.append(r["stderr"].rstrip())
            saida.value = "\n".join(blocos) or "Programa finalizado sem saída."
            saida.color = ft.Colors.GREEN_300 if r.get("status") == "ok" else ft.Colors.RED_300
            if r.get("status") not in ("ok",):
                saida.value = f"[{STATUS_TEXTO.get(r.get('status'), r.get('status'))}]\n{saida.value}"
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            saida.value = mensagem_erro(exc)
            saida.color = ft.Colors.RED_300
        ocupado(False)

    async def enviar():
        if not estado["slug"]:
            return
        ocupado(True)
        resultados.controls = []
        saida.value = "Avaliando sua solução..."
        saida.color = ft.Colors.BLUE_200
        page.update()
        try:
            r = await api.post(
                f"/problems/{estado['slug']}/submit",
                {"source": entrada_codigo.value or ""},
            )
        except Exception as exc:  # noqa: BLE001
            if sessao_expirada(exc, navegar):
                return
            saida.value = mensagem_erro(exc)
            saida.color = ft.Colors.RED_300
            ocupado(False)
            return

        aceito = r["status"] == "accepted"
        resumo = f"{STATUS_TEXTO.get(r['status'], r['status'])} — {r['passed']}/{r['total']} testes"
        if r.get("points_awarded"):
            resumo += f"  (+{r['points_awarded']} pontos!)"
        saida.value = resumo
        saida.color = ft.Colors.GREEN_300 if aceito else ft.Colors.RED_300

        linhas = []
        for t in r.get("results", []):
            ok = t.get("ok")
            texto = f"Teste {t['index']}: " + ("passou" if ok else STATUS_TEXTO.get(t["status"], t["status"]))
            linhas.append(ft.Text(texto, color=ft.Colors.GREEN_300 if ok else ft.Colors.RED_300, size=13))
            if not ok and t.get("stderr"):
                linhas.append(ft.Text(t["stderr"], font_family="monospace", size=12, color=ft.Colors.GREY_400, selectable=True))
            if not ok and t.get("expected") is not None:
                linhas.append(ft.Text(
                    f"  entrada: {t.get('input')!r}  esperado: {t.get('expected')!r}  obtido: {t.get('got')!r}",
                    font_family="monospace", size=12, color=ft.Colors.GREY_400, selectable=True,
                ))
        resultados.controls = linhas
        if aceito:
            await carregar()
        ocupado(False)

    botao_executar = ft.Button(
        content=ft.Text("Executar", weight=ft.FontWeight.BOLD),
        icon=ft.Icons.PLAY_ARROW,
        on_click=lambda e: page.run_task(executar),
    )
    botao_enviar = ft.Button(
        content=ft.Text("Enviar solução", weight=ft.FontWeight.BOLD),
        icon=ft.Icons.SEND,
        bgcolor=ft.Colors.GREEN_700,
        color=ft.Colors.WHITE,
        on_click=lambda e: page.run_task(enviar),
    )

    page.run_task(carregar)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Voltar aos desafios", on_click=lambda e: navegar("desafios")),
                    titulo,
                ]),
                meta,
                enunciado,
                exemplo,
                ft.Text("Linguagem: Python 3", color=ft.Colors.GREY_400, size=12),
                entrada_codigo,
                entrada_stdin,
                ft.Row(
                    [progresso, botao_executar, botao_enviar],
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text("Saída", size=16, weight=ft.FontWeight.BOLD),
                painel_saida,
                resultados,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
