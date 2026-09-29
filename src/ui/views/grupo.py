import flet as ft

def tela_grupo(page: ft.Page, navegar):
    # Simulando dados que viriam do backend ao clicar em um grupo específico
    nome_do_grupo = "Equipe Python"
    codigo_do_grupo = "84729"

    def voltar(e):
        # A rota "grupos" deve ser a que renderiza o lobby (tela_grupos)
        navegar("grupos") 

    def abrir_desafio(e):
        # Vai para a tela do editor resolver o problema (ex: Two Sum)
        navegar("editor") 

    def remover_membro(e, nome):
        print(f"Lógica do backend para remover {nome} do grupo acionada.")
        # Após remover do banco de dados, você atualizaria a lista_membros aqui
        page.update()

    # --- Header da Tela ---
    botao_voltar = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=ft.Colors.WHITE,
        on_click=voltar,
        tooltip="Voltar aos meus grupos"
    )

    header = ft.Row([
        botao_voltar,
        ft.Column([
            ft.Text(nome_do_grupo, size=28, weight=ft.FontWeight.BOLD),
            ft.Text(f"Código de Convite: {codigo_do_grupo}", color=ft.Colors.GREY_400, size=14),
        ], spacing=0)
    ], alignment=ft.MainAxisAlignment.START)

    # --- Aba 1: Desafios do Grupo ---
    def criar_card_desafio(titulo, dificuldade, resolvido=False):
        cor_dificuldade = ft.Colors.GREEN_400 if dificuldade == "Fácil" else ft.Colors.ORANGE_400
        
        texto_botao = "Resolvido" if resolvido else "Resolver"
        cor_botao = ft.Colors.GREY_700 if resolvido else ft.Colors.GREEN_700
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(titulo, weight=ft.FontWeight.BOLD, size=18),
                    ft.Text(dificuldade, color=cor_dificuldade, size=14),
                ], spacing=2),
                ft.Container(
                    content=ft.Text(texto_botao, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=cor_botao,
                    padding=10,
                    border_radius=5,
                    ink=not resolvido,
                    on_click=abrir_desafio if not resolvido else None
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10)
        )

    lista_desafios = ft.Column([
        criar_card_desafio("1. Two Sum", "Fácil", resolvido=True),
        criar_card_desafio("2. Validador de Senhas", "Médio"),
        criar_card_desafio("3. Robô Coletor (Lógica)", "Difícil"),
    ], scroll=ft.ScrollMode.AUTO)

    # --- Aba 2: Membros e Ranking Interno ---
    def criar_card_membro(posicao, nome, pontos, is_admin=False):
        # Se for admin, mostra uma estrela. Se for membro comum, mostra a lixeira para remoção (US08)
        icone_acao = ft.Icon(ft.Icons.STAR, color=ft.Colors.YELLOW_600, tooltip="Administrador") if is_admin else ft.IconButton(
            icon=ft.Icons.DELETE, 
            icon_color=ft.Colors.RED_400, 
            tooltip="Remover Membro",
            on_click=lambda e: remover_membro(e, nome)
        )

        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Text(f"#{posicao}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                    ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON), bgcolor=ft.Colors.BLUE_700),
                    ft.Text(nome, size=16, weight=ft.FontWeight.W_500),
                ], spacing=15),
                ft.Row([
                    ft.Text(f"{pontos} pts", size=16, color=ft.Colors.YELLOW_400, weight=ft.FontWeight.BOLD),
                    icone_acao
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10)
        )

    lista_membros = ft.Column([
        criar_card_membro(1, "Flávio Alves", 1100, is_admin=True),
        criar_card_membro(2, "Lourenço Braga", 850),
        criar_card_membro(3, "Maria Cecilia", 300),
    ], scroll=ft.ScrollMode.AUTO)

# --- Estrutura das Abas ---
    area_conteudo = ft.Container(
            content=lista_desafios, 
            padding=20, 
            expand=True
        )

    def mudar_aba(e, aba_selecionada):
        if aba_selecionada == "desafios":
            area_conteudo.content = lista_desafios
            btn_desafios.bgcolor = ft.Colors.BLUE_700
            btn_membros.bgcolor = ft.Colors.GREY_800
        else:
            area_conteudo.content = lista_membros
            btn_desafios.bgcolor = ft.Colors.GREY_800
            btn_membros.bgcolor = ft.Colors.BLUE_700
        page.update()

    btn_desafios = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CODE, size=18, color=ft.Colors.WHITE), 
            ft.Text("Desafios", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        ]),
        bgcolor=ft.Colors.BLUE_700, # Começa selecionado
        padding=10,
        border_radius=5,
        ink=True,
        on_click=lambda e: mudar_aba(e, "desafios")
    )

    btn_membros = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.PEOPLE, size=18, color=ft.Colors.WHITE), 
            ft.Text("Membros & Ranking", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        ]),
        bgcolor=ft.Colors.GREY_800, # Começa inativo
        padding=10,
        border_radius=5,
        ink=True,
        on_click=lambda e: mudar_aba(e, "membros")
    )

    abas = ft.Column([
        ft.Row([btn_desafios, btn_membros], spacing=10),
        ft.Divider(height=1, color=ft.Colors.OUTLINE),
        area_conteudo
    ], expand=True)

    return ft.Container(
        content=ft.Column([
            header,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            abas
        ]),
        padding=20,
        expand=True
    )