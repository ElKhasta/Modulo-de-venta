import flet as ft
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def main(page: ft.Page):
    page.title = "FESConnect - Punto de Venta"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 850
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- 1. VARIABLES DE ESTADO ---
    carrito = []
    ventas_totales_dia = {"efectivo": 0.0, "tarjeta": 0.0}

    # --- 2. CAMPOS DE SESIÓN (Definidos primero para evitar NameError) ---
    txt_user = ft.TextField(label="Usuario", width=300, prefix_icon=ft.Icons.PERSON)
    txt_pass = ft.TextField(label="Contraseña", password=True, width=300, can_reveal_password=True)

    def mostrar_snack(texto, color=ft.Colors.RED):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ==========================================
    # LÓGICA DE NEGOCIO (INYECCIÓN DEL CÓDIGO 1)
    # ==========================================
    
    def calcular_cambio_real(e=None):
        try:
            total = sum(item['precio'] * item['cantidad'] for item in carrito)
            recibido = float(input_recibido.value) if input_recibido.value else 0
            cambio = recibido - total
            
            # Bloqueo dinámico del botón de cobro
            esta_bloqueado = (cambio < 0 or total == 0)
            btn_finalizar.disabled = esta_bloqueado
            btn_finalizar.bgcolor = ft.Colors.GREY_400 if esta_bloqueado else ft.Colors.GREEN
            
            if cambio >= 0:
                txt_cambio_display.value = f"Cambio: ${cambio:.2f}"
                txt_cambio_display.color = "green"
            else:
                txt_cambio_display.value = f"Faltan: ${abs(cambio):.2f}"
                txt_cambio_display.color = "red"
        except:
            btn_finalizar.disabled = True
        page.update()

    def agregar_producto_event(e):
        busqueda = input_busqueda.value.strip()
        if not busqueda: return
        try:
            res = requests.get(f"{BASE_URL}/productos/", timeout=5)
            if res.status_code == 200:
                prod = next((p for p in res.json() if p['nombre'].lower() == busqueda.lower() or p.get('codigo_barras') == busqueda), None)
                if prod:
                    cant_v = int(input_cantidad.value)
                    stock_real = int(prod['stock'])
                    en_carrito = sum(i['cantidad'] for i in carrito if i['id'] == prod['id'])
                    
                    # Validación de Stock
                    if (en_carrito + cant_v) > stock_real:
                        mostrar_snack(f"⚠️ Stock insuficiente: {stock_real} disponibles")
                        return

                    if en_carrito > 0:
                        for i in carrito:
                            if i['id'] == prod['id']: i['cantidad'] += cant_v
                    else:
                        carrito.append({"id": prod['id'], "nombre": prod['nombre'], "precio": float(prod['precio']), "cantidad": cant_v})
                    
                    input_busqueda.value = ""; input_cantidad.value = "1"
                    actualizar_interfaz_ventas()
                else: mostrar_snack("❌ Producto no encontrado")
        except: mostrar_snack("🌐 Error de red")

    def finalizar_venta_event(e):
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        ventas_totales_dia[radio_pago.value] += total
        carrito.clear()
        input_recibido.value = ""
        mostrar_snack("✅ Venta procesada", "green")
        actualizar_interfaz_ventas()

    def actualizar_interfaz_ventas():
        tabla_ventas.rows.clear()
        total = 0
        for item in carrito:
            sub = item['precio'] * item['cantidad']
            total += sub
            tabla_ventas.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item['nombre'])),
                ft.DataCell(ft.Text(f"${item['precio']:.2f}")),
                ft.DataCell(ft.Text(str(item['cantidad']))),
                ft.DataCell(ft.Text(f"${sub:.2f}")),
                ft.DataCell(ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color="red", on_click=lambda _, i=item['id']: eliminar_item(i)))
            ]))
        txt_total_v.value = f"Total: ${total:.2f}"
        calcular_cambio_real()

    def eliminar_item(item_id):
        nonlocal carrito
        carrito = [i for i in carrito if i['id'] != item_id]
        actualizar_interfaz_ventas()

    # ==========================================
    # DEFINICIÓN DE VISTAS (DISEÑO DEL CÓDIGO 2)
    # ==========================================
    
    # --- VENTAS ---
    dropdown_cliente = ft.Dropdown(label="Cliente", expand=True, options=[ft.dropdown.Option("0", "Público General")], value="0")
    input_busqueda = ft.TextField(label="Producto o Código", expand=True, on_submit=agregar_producto_event)
    input_cantidad = ft.TextField(label="Cant.", value="1", width=80, text_align="center")
    tabla_ventas = ft.DataTable(expand=True, columns=[
        ft.DataColumn(ft.Text("Producto")), ft.DataColumn(ft.Text("Precio")),
        ft.DataColumn(ft.Text("Cant.")), ft.DataColumn(ft.Text("Subtotal")), ft.DataColumn(ft.Text("Acción"))
    ])
    
    radio_pago = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="efectivo", label="Efectivo 💵"),
        ft.Radio(value="tarjeta", label="Tarjeta/Transf. 💳"),
    ]), value="efectivo")
    
    input_recibido = ft.TextField(label="Recibido $", width=150, on_change=calcular_cambio_real)
    txt_cambio_display = ft.Text("Cambio: $0.00", size=20, weight="bold", color="green")
    txt_total_v = ft.Text("Total: $0.00", size=28, weight="bold", color="blue900")
    btn_finalizar = ft.FilledButton(
        "Finalizar", 
        icon=ft.Icons.CHECK, 
        color="white", 
        bgcolor=ft.Colors.GREY_400, 
        disabled=True, 
        on_click=finalizar_venta_event
    )
    view_ventas = ft.Container(
        content=ft.Column([
            ft.Text("🛒 Módulo de Ventas", size=30, weight="bold"),
            ft.Row([dropdown_cliente, ft.IconButton(ft.Icons.REFRESH)]),
            ft.Row([input_busqueda, input_cantidad, ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=agregar_producto_event)]),
            ft.Container(content=ft.ListView([tabla_ventas], expand=True), expand=True, border=ft.Border.all(1, "bluegrey100"), border_radius=10, padding=10),
            ft.Row([
                ft.Column([radio_pago, ft.Row([input_recibido, txt_cambio_display])]),
                ft.Column([txt_total_v, btn_finalizar], horizontal_alignment="end")
            ], alignment="spaceBetween")
        ]), expand=True, visible=True
    )

    # --- STOCK ---
    view_stock = ft.Container(
        content=ft.Column([
            ft.Text("📦 Inventario", size=30, weight="bold"),
            ft.Row([ft.TextField(label="Filtrar...", expand=True), ft.IconButton(ft.Icons.SEARCH)]),
            ft.ListView(expand=True)
        ]), expand=True, visible=False
    )

    # --- CLIENTES ---
    view_clientes = ft.Container(
        content=ft.Column([
            ft.Text("👥 Registro de Clientes", size=30, weight="bold"),
            ft.TextField(label="Nombre / Razón Social", icon=ft.Icons.PERSON),
            ft.TextField(label="RFC", icon=ft.Icons.BADGE),
            ft.TextField(label="Email", icon=ft.Icons.EMAIL),
            ft.FilledButton("Guardar", icon=ft.Icons.SAVE, color="white", bgcolor="blue")
        ]), expand=True, visible=False
    )

    # --- CORTE ---
    txt_c_efectivo = ft.Text("$0.00", size=45, weight="bold", color="green")
    txt_c_tarjeta = ft.Text("$0.00", size=45, weight="bold", color="blue")
    
    view_corte = ft.Container(
        content=ft.Column([
            ft.Text("📊 Resumen del Día", size=35, weight="bold"),
            ft.Row([
                ft.Card(content=ft.Container(padding=40, width=400, content=ft.Column([ft.Icon(ft.Icons.ATTACH_MONEY, size=50, color="green"), ft.Text("EFECTIVO", size=20), txt_c_efectivo], horizontal_alignment="center"))),
                ft.Card(content=ft.Container(padding=40, width=400, content=ft.Column([ft.Icon(ft.Icons.CREDIT_CARD, size=50, color="blue"), ft.Text("TAR_TRANS", size=20), txt_c_tarjeta], horizontal_alignment="center"))),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
            ft.FilledButton("Cerrar Caja", icon=ft.Icons.LOCK_OUTLINE, scale=1.2)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=40),
        expand=True, visible=False
    )

    # ==========================================
    # NAVEGACIÓN
    # ==========================================
    def cambiar_tab(e):
        idx = e.control.selected_index
        view_ventas.visible = (idx == 0)
        view_stock.visible = (idx == 1)
        view_clientes.visible = (idx == 2)
        view_corte.visible = (idx == 3)
        if idx == 3:
            txt_c_efectivo.value = f"${ventas_totales_dia['efectivo']:.2f}"
            txt_c_tarjeta.value = f"${ventas_totales_dia['tarjeta']:.2f}"
        if idx == 4: reiniciar()
        page.update()

    rail = ft.NavigationRail(
        selected_index=0, label_type="all", min_width=100,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART, label="Ventas"),
            ft.NavigationRailDestination(icon=ft.Icons.INVENTORY, label="Stock"),
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_ADD, label="Clientes"),
            ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART, label="Corte"),
            ft.NavigationRailDestination(icon=ft.Icons.LOGOUT, label="Salir"),
        ], on_change=cambiar_tab
    )

    def cargar_principal():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.add(ft.Row([rail, ft.VerticalDivider(width=1), view_ventas, view_stock, view_clientes, view_corte], expand=True))

    def login(e):
        cargar_principal()

    login_card = ft.Card(
        content=ft.Container(
            padding=40, width=400,
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=80, color="blue"),
                ft.Text("FESConnect POS", size=28, weight="bold"),
                ft.Divider(height=20, color="transparent"),
                txt_user,
                txt_pass,
                ft.Divider(height=10, color="transparent"),
                ft.FilledButton("Entrar", on_click=login, width=250)
            ], horizontal_alignment="center", spacing=15)
        ),
        elevation=10
    )

    def reiniciar():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.add(login_card)

    page.add(login_card)

ft.run(main)