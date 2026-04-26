import flet as ft
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def main(page: ft.Page):
    page.title = "FESConnect - Punto de Venta"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 850
    
    # --- 1. VARIABLES DE ESTADO ---
    carrito = []
    lista_productos_db = []

    # --- 2. INSTANCIACIÓN PREVIA DE COMPONENTES (Para evitar errores de referencia) ---
    # Campos de Login
    txt_user = ft.TextField(label="Usuario", width=300, prefix_icon=ft.Icons.PERSON)
    txt_pass = ft.TextField(label="Contraseña", password=True, width=300, can_reveal_password=True)
    es_admin=False
    # Componentes de Ventas
    input_cantidad = ft.TextField(label="Cant.", value="1", width=80, text_align="center")
    input_recibido = ft.TextField(label="Recibido", width=120)
    txt_total_v = ft.Text("Total: $0.00", size=24, weight="bold")
    txt_cambio_display = ft.Text("Cambio: $0.00", size=18)
    btn_finalizar = ft.FilledButton("Cobrar", disabled=True, bgcolor=ft.Colors.GREY_400)
    
    # Tablas y Buscador
    tabla_ventas = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Producto")), ft.DataColumn(ft.Text("Precio")),
            ft.DataColumn(ft.Text("Cant.")), ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Acción"))
        ]
    )
    
    tabla_stock = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Código")), ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Precio")), ft.DataColumn(ft.Text("Existencia")),
            ft.DataColumn(ft.Text("Acciones"))
        ]
    )
    # Campos para crear nuevo usuario
    new_user_name = ft.TextField(label="Nombre de Usuario", width=300)
    new_user_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)
    new_user_role = ft.Dropdown(
        label="Rol",
        width=300,
        options=[
            ft.dropdown.Option("admin", "Administrador"),
            ft.dropdown.Option("staff", "Vendedor"),
        ],
        value="staff"
    )
    
    tabla_usuarios = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Rol")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )
    # --- 3. FUNCIONES DE APOYO ---
    def mostrar_snack(texto, color=ft.Colors.RED):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- 4. LÓGICA DE NEGOCIO ---
    def cargar_productos_busqueda():
        try:
            res = requests.get(f"{BASE_URL}/productos/", timeout=5)
            if res.status_code == 200:
                nonlocal lista_productos_db
                lista_productos_db = res.json()
                input_busqueda.suggestions = [
                    ft.AutoCompleteSuggestion(key=p['nombre'], value=p['nombre']) 
                    for p in lista_productos_db
                ]
                page.update()
        except: pass

    def cargar_tabla_stock():
        tabla_stock.rows.clear()
        try:
            res = requests.get(f"{BASE_URL}/productos/", timeout=5)
            if res.status_code == 200:
                for p in res.json():
                    stock_actual = int(p.get('stock', 0))
                    color_alerta = ft.Colors.RED_600 if stock_actual < 5 else ft.Colors.BLACK
                    tabla_stock.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(p.get('codigo_barras', 'S/C'))),
                        ft.DataCell(ft.Text(p['nombre'])),
                        ft.DataCell(ft.Text(f"${float(p['precio']):.2f}")),
                        ft.DataCell(ft.Text(str(stock_actual), color=color_alerta, weight="bold")),
                        ft.DataCell(ft.IconButton(ft.Icons.EDIT, icon_color="blue700"))
                    ]))
                page.update()
        except Exception as e:
            mostrar_snack(f"Error al cargar stock: {e}")

    def calcular_cambio_real(e=None):
        try:
            total = sum(item['precio'] * item['cantidad'] for item in carrito)
            recibido = float(input_recibido.value) if input_recibido.value else 0
            cambio = recibido - total
            esta_bloqueado = (cambio < 0 or total == 0)
            btn_finalizar.disabled = esta_bloqueado
            btn_finalizar.bgcolor = ft.Colors.GREY_400 if esta_bloqueado else ft.Colors.GREEN
            if cambio >= 0:
                txt_cambio_display.value = f"Cambio: ${cambio:.2f}"; txt_cambio_display.color = "green"
            else:
                txt_cambio_display.value = f"Faltan: ${abs(cambio):.2f}"; txt_cambio_display.color = "red"
        except:
            btn_finalizar.disabled = True; btn_finalizar.bgcolor = ft.Colors.GREY_400
        page.update()

    def eliminar_item(item_id):
        nonlocal carrito
        carrito = [i for i in carrito if i['id'] != item_id]
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
                    if (sum(i['cantidad'] for i in carrito if i['id'] == prod['id']) + cant_v) > int(prod['stock']):
                        mostrar_snack("⚠️ Stock insuficiente"); return
                    
                    en_carrito = next((i for i in carrito if i['id'] == prod['id']), None)
                    if en_carrito: 
                        en_carrito['cantidad'] += cant_v
                    else: 
                        carrito.append({"id": prod['id'], "nombre": prod['nombre'], "precio": float(prod['precio']), "cantidad": cant_v})
                    
                    input_busqueda.value = ""; input_cantidad.value = "1"
                    actualizar_interfaz_ventas()
                else: mostrar_snack("❌ Producto no encontrado")
        except: mostrar_snack("🌐 Error de red")

    def finalizar_venta_event(e):
        # Simulación de POST a la API
        carrito.clear()
        input_recibido.value = ""
        mostrar_snack("✅ Venta exitosa", ft.Colors.GREEN)
        actualizar_interfaz_ventas()
        cargar_productos_busqueda()
    
    def cargar_tabla_usuarios():
        if not es_admin: return
        tabla_usuarios.rows.clear()
        try:
            res = requests.get(f"{BASE_URL}/usuarios/", timeout=5)
            if res.status_code == 200:
                for u in res.json():
                    tabla_usuarios.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(u['id']))),
                        ft.DataCell(ft.Text(u['username'])),
                        ft.DataCell(ft.Text("Admin" if u.get('is_staff') else "Vendedor")),
                        ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda _, id=u['id']: eliminar_usuario(id))),
                    ]))
                page.update()
        except: mostrar_snack("Error al conectar con usuarios")

    def guardar_usuario(e):
        if not new_user_name.value or not new_user_pass.value:
            mostrar_snack("Llena todos los campos")
            return
            
        datos = {
            "username": new_user_name.value,
            "password": new_user_pass.value,
            "is_staff": True if new_user_role.value == "admin" else False
        }
        
        try:
            res = requests.post(f"{BASE_URL}/usuarios/", json=datos, timeout=5)
            if res.status_code in [200, 201]:
                mostrar_snack("✅ Usuario creado con éxito", ft.Colors.GREEN)
                new_user_name.value = ""; new_user_pass.value = ""
                cargar_tabla_usuarios()
            else:
                mostrar_snack(f"Error: {res.text}")
        except:
            mostrar_snack("🌐 Error de red al crear usuario")

    def eliminar_usuario(id_user):
        mostrar_snack(f"Eliminando usuario {id_user}...")
        pass
    # --- 5. COMPONENTES CON LÓGICA ASIGNADA ---
    input_busqueda = ft.AutoComplete(suggestions=[], on_select=lambda e: agregar_producto_event(None))
    input_recibido.on_change = calcular_cambio_real
    btn_finalizar.on_click = finalizar_venta_event

    # --- 6. VISTAS DE LA APLICACIÓN ---
    view_ventas = ft.Container(
        content=ft.Column([
            ft.Text("🛒 Ventas", size=30, weight="bold"),
            ft.Row([
                ft.Container(input_busqueda, expand=True),
                input_cantidad,
                ft.IconButton(ft.Icons.CAMERA_ALT, tooltip="Escanear con celular", on_click=lambda _: mostrar_snack("Activando cámara...", "blue")),
                ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=agregar_producto_event)
            ]),
            ft.Container(content=ft.ListView([tabla_ventas], expand=True), expand=True, border=ft.Border.all(1, "bluegrey100"), border_radius=10, padding=10),
            ft.Row([
                ft.Column([
                    ft.RadioGroup(content=ft.Row([ft.Radio(value="e", label="Efectivo"), ft.Radio(value="t", label="Tarjeta")]), value="e"), 
                    ft.Row([input_recibido, txt_cambio_display])
                ]),
                ft.Column([txt_total_v, btn_finalizar])
            ], alignment="spaceBetween")
        ]), expand=True
    )
    view_usuarios = ft.Container(
        content=ft.Column([
            ft.Text("👥 Gestión de Usuarios", size=30, weight="bold"),
            ft.Row([
                ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Text("Agregar Nuevo", weight="bold"),
                            new_user_name,
                            new_user_pass,
                            new_user_role,
                            ft.ElevatedButton("Guardar Usuario", icon=ft.Icons.SAVE, on_click=guardar_usuario)
                        ])
                    )
                ),
                ft.VerticalDivider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Usuarios Registrados", weight="bold"),
                        ft.ListView([tabla_usuarios], expand=True)
                    ]), expand=True
                )
            ], expand=True)
        ]), expand=True, visible=False
    )
    view_stock = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("📦 Inventario", size=30, weight="bold"), ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: cargar_tabla_stock())]),
            ft.Container(content=ft.ListView([tabla_stock], expand=True), expand=True, border=ft.Border.all(1, "bluegrey100"), border_radius=10)
        ]), expand=True, visible=False
    )

    # --- 7. NAVEGACIÓN Y LOGIN ---
    def cambiar_tab(e):
        idx = e.control.selected_index
        view_ventas.visible = (idx == 0)
        view_stock.visible = (idx == 1)
        view_usuarios.visible = (idx == 3) 
        
        if idx == 1: cargar_tabla_stock()
        if idx == 3: cargar_tabla_usuarios()
        if idx == 4: reiniciar() # Salir
        page.update()

    rail = ft.NavigationRail(
        selected_index=0, label_type="all",
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART, label="Ventas"),
            ft.NavigationRailDestination(icon=ft.Icons.INVENTORY, label="Stock"),
            ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial"),
            ft.NavigationRailDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS, label="Admin"),
            ft.NavigationRailDestination(icon=ft.Icons.LOGOUT, label="Salir"),
        ], on_change=cambiar_tab
    )

    def login(e):
        user = txt_user.value.strip()
        passw = txt_pass.value.strip()
        if not user or not passw:
            mostrar_snack("Llenar campos")
            return
        
        try:
            res = requests.post(f"{BASE_URL}/login/", json={"username": user, "password": passw}, timeout=5)
            if res.status_code in [200, 201]:
                page.clean()
                page.add(ft.Row([rail, ft.VerticalDivider(width=1), view_ventas, view_stock], expand=True))
                cargar_productos_busqueda()
            else:
                mostrar_snack("Usuario o contraseña incorrectos")
        except:
            mostrar_snack("Error de conexión con el servidor")

    login_card = ft.Card(
        content=ft.Container(
            padding=40, width=400,
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_PERSON, size=80, color="blue"),
                ft.Text("FESConnect Admin", size=24, weight="bold"),
                txt_user, txt_pass,
                ft.FilledButton("Entrar", on_click=login, width=250)
            ], horizontal_alignment="center")
        ), elevation=10
    )

    def reiniciar():
        page.clean()
        page.vertical_alignment = "center"
        page.horizontal_alignment = "center"
        page.add(login_card)

    reiniciar()

ft.run(main)