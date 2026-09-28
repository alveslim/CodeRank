import flet as ft

def tela_grupos(page: ft.Page, navegar):
    
    def abrir_grupo(e):
        navegar("grupo")
        
    def criar_grupo(e):
        print("Abrir modal ou tela para criação de novo grupo")
        
    def entrar_por_codigo(e):
        codigo = campo_codigo.value
        if codigo:
            print(f"Tentando ingressar no grupo com código: {codigo}")
        else:
            print("Digite um código válido.")

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
        on_click=criar_grupo,
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