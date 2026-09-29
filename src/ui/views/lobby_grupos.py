import flet as ft
import random # simular a geracao de um código aleatório :)

def tela_grupos(page: ft.Page, navegar):
    
    def abrir_grupo(e):
        navegar("grupo")
        
    def criar_grupo(e):
        print("Abrir modal ou tela para criação de novo grupo")
        
    def entrar_por_codigo(e):
        codigo = campo_codigo.value
        if codigo:
            print(f"Tentando ingressar no grupo com código: {codigo}")
            navegar("grupo")
        else:
            print("Digite um código válido.")
            
    nome_grupo_input =  ft.TextField(label='Nome do Grupo', width=300, autofocus=True)
    desc_grupo_input = ft.TextField(label="Descrição (Opcional)", width=300, multiline=True)
    
    def fechar_modal(e):
        modal_criar_grupo.open = False
        page.update()
    
    def confirmar_criacao(e):
        nome = nome_grupo_input.value
        if nome:
            codigo_gerado = str(random.randint(10000, 99999)) # chamada back
            
            novo_card = criar_card_grupo(nome, codigo_gerado)
            lista_grupos.controls.insert(0, novo_card)
            
            nome_grupo_input.value = ""
            nome_grupo_input.error_text = None
            desc_grupo_input.value = ""
            
            modal_criar_grupo.open = False
            page.update()
        else:
            # Exibe erro se tentar criar sem nome
            nome_grupo_input.error_text = "O nome do grupo é obrigatório"
            page.update()
            
    modal_criar_grupo = ft.AlertDialog(
            title=ft.Text("Criar Novo Grupo", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("Preencha os dados abaixo para gerar um novo código de convite:"),
                nome_grupo_input,
                desc_grupo_input
            ], tight=True), # tight=True evita que a coluna ocupe a tela toda
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.Container(
                    content=ft.Text("Criar Grupo", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    on_click=confirmar_criacao, 
                    bgcolor=ft.Colors.BLUE_700,
                    padding=10,
                    border_radius=5,
                    ink=True
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    
    def abrir_modal_criar(e):
        # Abre o modal na tela
        if modal_criar_grupo not in page.overlay:
            page.overlay.append(modal_criar_grupo)
            
        modal_criar_grupo.open = True
        page.update()
    
    # Elementos para a US03 - Entrar via código
    campo_codigo = ft.TextField(
        label="Código de Convite", 
        width=200, 
        height=45, 
        bgcolor=ft.Colors.GREY_900,
        content_padding=10
    )
    
    # Botão "Entrar" corrigido usando Container
    botao_entrar_codigo = ft.Container(
        content=ft.Text("Entrar", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        on_click=entrar_por_codigo,
        bgcolor=ft.Colors.GREEN_700,
        height=45,
        padding=ft.Padding.symmetric(horizontal=20),
        alignment=ft.Alignment.CENTER,
        border_radius=5,
        ink=True
    )

    # Botão "Criar Grupo" corrigido usando Container e Row (para ícone + texto)
    botao_criar = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE, size=20),
            ft.Text("Criar Grupo", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
        on_click=abrir_modal_criar,
        bgcolor=ft.Colors.BLUE_700,
        height=45,
        padding=ft.Padding.symmetric(horizontal=15),
        alignment=ft.Alignment.CENTER,
        border_radius=5,
        ink=True
    )

    # Header unindo as ações de Criar e Entrar
    secao_acoes = ft.Row([
        botao_criar,
        ft.Row([campo_codigo, botao_entrar_codigo], spacing=5)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Modelo de card de grupo existente
    def criar_card_grupo(nome, codigo):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(nome, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"Código: {codigo}", color=ft.Colors.WHITE_70, size=12),
                ], spacing=2),
                ft.Container(
                    content=ft.Text("ABRIR", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE_700,
                    padding=10,
                    border_radius=5,
                    ink=True,
                    on_click=abrir_grupo
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            margin=ft.Margin.only(bottom=10)
        )

    # Lista estática para exemplo
    lista_grupos = ft.Column([
        criar_card_grupo("Grupo 1", "21910"),
        criar_card_grupo("Equipe Python", "84729"),
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    return ft.Container(
        content=ft.Column([
            ft.Text("Meus Grupos", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            secao_acoes,
            ft.Divider(height=20, color=ft.Colors.OUTLINE),
            lista_grupos
        ]),
        padding=20,
        expand=True
    )