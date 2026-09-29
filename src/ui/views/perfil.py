import flet as ft

def tela_perfil(page: ft.Page, navegar):
    # Simulando variáveis iniciais
    cidade_usuario = "Manaus"
    uf_usuario = "AM"
    nome_usuario = "Flávio Alves"
    curso_usuario = "Engenharia de Software"
    faculdade = "FAMETRO"

    # --- 1. Elementos de Texto Dinâmicos ---
    # Precisamos separá-los em variáveis para poder alterar o .value depois
    texto_nome = ft.Text(nome_usuario, size=24, weight=ft.FontWeight.BOLD)
    texto_curso = ft.Text(f"{curso_usuario} | {faculdade}", color=ft.Colors.GREY_400, size=16)
    texto_localizacao = ft.Text(f"{cidade_usuario} - {uf_usuario}", color=ft.Colors.GREY_400, size=16)

    # --- 2. Lógica do Modal de Edição ---
    input_nome = ft.TextField(label="Nome Completo", value=nome_usuario, width=320)
    input_cidade = ft.TextField(label="Cidade", value=cidade_usuario, width=155)
    input_uf = ft.TextField(label="UF", value=uf_usuario, width=155)
    
    def fechar_modal_edicao(e):
        modal_editar_perfil.open = False
        page.update()

    def salvar_perfil(e):
        # Atualiza os textos na interface com os novos valores digitados
        texto_nome.value = input_nome.value
        texto_localizacao.value = f"{input_cidade.value} - {input_uf.value}"
        
        # Aqui você faria o UPDATE no Supabase
        
        modal_editar_perfil.open = False
        page.update()

    modal_editar_perfil = ft.AlertDialog(
        title=ft.Text("Editar Perfil", weight=ft.FontWeight.BOLD),
        content=ft.Column([
            input_nome,
            ft.Row([input_cidade, input_uf], spacing=10)
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal_edicao),
            ft.Container(
                content=ft.Text("Salvar Alterações", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                on_click=salvar_perfil, 
                bgcolor=ft.Colors.BLUE_700,
                padding=10,
                border_radius=5,
                ink=True
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8)
    )

    def abrir_modal_edicao(e):
        if modal_editar_perfil not in page.overlay:
            page.overlay.append(modal_editar_perfil)
        modal_editar_perfil.open = True
        page.update()

    # Botão de editar que ficará ao lado do nome
    botao_editar = ft.IconButton(
        icon=ft.Icons.EDIT, 
        icon_color=ft.Colors.BLUE_400, 
        tooltip="Editar Perfil",
        on_click=abrir_modal_edicao
    )

    # --- 3. Histórico de Desafios ---
    def criar_card_historico(nome_desafio, data, status, linguagem="Python"):
        cor_status = ft.Colors.GREEN_400 if status == "Aceito" else ft.Colors.RED_400
        icone_status = ft.Icons.CHECK_CIRCLE if status == "Aceito" else ft.Icons.CANCEL
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(nome_desafio, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"{data} • {linguagem}", color=ft.Colors.GREY_400, size=12),
                ], spacing=2),
                ft.Row([
                    ft.Text(status, color=cor_status, weight=ft.FontWeight.BOLD),
                    ft.Icon(icone_status, color=cor_status, size=20)
                ], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10)
        )

    # Lista rolável do histórico
    lista_historico = ft.Column([
        criar_card_historico("1. Two Sum", "28 Set 2026", "Aceito"),
        criar_card_historico("2. Validador de Senhas", "27 Set 2026", "Erro (Tempo)"),
        criar_card_historico("1. Two Sum", "27 Set 2026", "Erro (Sintaxe)", "Java"),
    ], scroll=ft.ScrollMode.AUTO, height=220) # A altura fixa garante que o perfil não "estoure" a tela

    # --- 4. Estatísticas e Botão Sair ---
    linha_estatisticas = ft.Row([
        ft.Column([ft.Text("1100", size=24, weight=ft.FontWeight.BOLD), ft.Text("Pontos", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("15", size=24, weight=ft.FontWeight.BOLD), ft.Text("Desafios", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.VerticalDivider(width=40, color=ft.Colors.OUTLINE),
        ft.Column([ft.Text("Python", size=24, weight=ft.FontWeight.BOLD), ft.Text("Linguagem", color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    def deslogar(e):
        navegar("login")

    botao_sair = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE, size=18), ft.Text("Terminar Sessão", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)], spacing=5),
        bgcolor=ft.Colors.RED_700,
        padding=10,
        border_radius=5,
        ink=True,
        on_click=deslogar
    )

    # --- 5. Montagem Final da Tela ---
    return ft.Container(
        content=ft.Column([
            ft.Text("O Meu Perfil", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            
            # Cabeçalho do Perfil (agora com o botão de editar ao lado do nome)
            ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, size=40),
                    radius=40,
                    bgcolor=ft.Colors.BLUE_700
                ),
                ft.Column([
                    ft.Row([texto_nome, botao_editar], spacing=5, alignment=ft.MainAxisAlignment.START),
                    texto_curso,
                    texto_localizacao,
                ], spacing=2)
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(height=30, color=ft.Colors.OUTLINE),
            linha_estatisticas,
            ft.Divider(height=30, color=ft.Colors.OUTLINE),
            
            # Nova seção de histórico
            ft.Text("Histórico de Submissões", size=20, weight=ft.FontWeight.BOLD),
            lista_historico,
            
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Row([botao_sair], alignment=ft.MainAxisAlignment.START)
        ]),
        padding=20,
        expand=True
    )