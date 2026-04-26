import flet as ft
import requests
import threading
import time

try:
    import cv2
    from pyzbar.pyzbar import decode
except ImportError:
    cv2 = None

BASE_URL = "http://127.0.0.1:8000/api"

# --- COLORES INSTITUCIONALES UNAM ---
AZUL_UNAM = "#002B7A"
ORO_UNAM = "#B38E5D"

def main(page: ft.Page):
    page.title = "FESConnect - Punto de Venta"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 850
    
    # --- 1. VARIABLES DE ESTADO ---
    carrito = []
    lista_productos_db = []
    global_es_admin = False # Para controlar permisos
    escaneo_destino = "venta" # "venta" o "stock"

    # --- 2. COMPONENTES DE INTERFAZ ---
    # Campos para Diálogo de Edición de Producto
    edit_nombre = ft.TextField(label="Nombre del Producto")
    edit_precio = ft.TextField(label="Precio", prefix=ft.Text("$"))
    edit_stock = ft.TextField(label="Existencia Actual")
    edit_codigo = ft.TextField(label="Código de Barras")

    txt_user = ft.TextField(label="Usuario", width=300, prefix_icon=ft.Icons.PERSON, border_color=AZUL_UNAM)
    txt_pass = ft.TextField(label="Contraseña", password=True, width=300, can_reveal_password=True, border_color=AZUL_UNAM)
    
    input_cantidad = ft.TextField(label="Cant.", value="1", width=80, text_align="center")
    input_recibido = ft.TextField(label="Recibido", width=120, border_color=AZUL_UNAM)
    txt_total_v = ft.Text("Total: $0.00", size=24, weight="bold", color=AZUL_UNAM)
    txt_cambio_display = ft.Text("Cambio: $0.00", size=18)
    
    btn_finalizar = ft.FilledButton(
        "Cobrar", 
        disabled=True, 
        bgcolor=ft.Colors.GREY_400,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    # Componentes para Edición de Productos (Popup)
    btn_guardar_edit = ft.FilledButton("Guardar Cambios", bgcolor=AZUL_UNAM, color="white")
    
    edit_dialog = ft.AlertDialog(
        title=ft.Text("Editar Producto"),
        content=ft.Column([
            edit_nombre, 
            edit_precio, 
            edit_stock, 
            edit_codigo
        ], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: (setattr(edit_dialog, "open", False), page.update())),
            btn_guardar_edit
        ]
    )

    def handle_barcode_result(e):
        if e.data:
            procesar_codigo_escaneado(e.data)

    # --- Lógica de Escáner para PC (OpenCV) ---
    def escanear_en_pc():
        if cv2 is None:
            mostrar_snack("Librerías OpenCV/PyZbar no encontradas. Instálalas con pip.")
            return

        cap = cv2.VideoCapture(0)
        window_name = 'Escaneando Producto - FESConnect'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        # Forzamos la ventana para que aparezca al frente (TopMost)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # Corregir efecto espejo (Voltear imagen para que sea intuitivo)
            frame = cv2.flip(frame, 1)

            for barcode in decode(frame):
                codigo = barcode.data.decode('utf-8')
                cap.release()
                cv2.destroyAllWindows()
                # Pequeña pausa para permitir que el SO procese el cierre de la ventana
                time.sleep(0.4)
                procesar_codigo_escaneado(codigo)
                return
            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
        cap.release()
        cv2.destroyAllWindows()

    def procesar_codigo_escaneado(codigo):
        nonlocal escaneo_destino
        if escaneo_destino == "venta":
            input_busqueda.value = codigo
            agregar_producto_event(None)
        elif escaneo_destino == "stock":
            # Buscar el producto en la lista local para editarlo
            prod = next((p for p in lista_productos_db if p.get('codigo_barras') == codigo), None)
            if prod:
                abrir_editar_producto(prod)
            else:
                mostrar_snack(f"Código {codigo} no registrado. Iniciando alta...")
                abrir_crear_producto(codigo)
        
        # TRUCO DE FOCO: Forzamos a que la ventana de Flet pase al frente
        # Esto soluciona que el diálogo no aparezca hasta hacer clic.
        page.window.always_on_top = True
        page.update()
        time.sleep(0.1)
        page.window.always_on_top = False
        page.update()

    def abrir_camara(e, destino="venta"):
        nonlocal escaneo_destino
        escaneo_destino = destino
        if page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
            if barcode_scanner: barcode_scanner.scan()
            else: mostrar_snack("Escáner móvil no disponible")
        else:
            # Ejecutamos en un hilo separado para no congelar la interfaz de Flet
            threading.Thread(target=escanear_en_pc, daemon=True).start()

    barcode_scanner = None
    if hasattr(ft, "BarcodeScanner"):
        barcode_scanner = ft.BarcodeScanner(on_result=handle_barcode_result)

    # Tablas
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

    tabla_usuarios = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Rol")), ft.DataColumn(ft.Text("Acciones")),
        ]
    )

    # Campos Usuario
    new_user_name = ft.TextField(label="Nombre de Usuario", width=300)
    new_user_pass = ft.TextField(label="Contraseña", password=True, width=300)
    new_user_role = ft.Dropdown(label="Rol", width=300, value="staff", options=[
        ft.dropdown.Option("admin", "Administrador"),
        ft.dropdown.Option("staff", "Vendedor"),
    ])

    # --- 3. FUNCIONES ---
    def mostrar_snack(texto, color=AZUL_UNAM):
        # Asegurar que el color sea válido para el fondo
        if color == ft.Colors.GREEN:
            snack = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=ft.Colors.GREEN_700)
        else:
            snack = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

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
        nonlocal lista_productos_db
        busqueda = input_busqueda.value.strip()
        if not busqueda: return
        
        # MEJORA: Buscar en la lista local cargada previamente en lugar de hacer request
        prod = next((p for p in lista_productos_db if p['nombre'].lower() == busqueda.lower() or p.get('codigo_barras') == busqueda), None)
        
        if prod:
            try:
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
            except ValueError:
                mostrar_snack("❌ Cantidad inválida")
        else:
            mostrar_snack("❌ Producto no encontrado")

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
        except Exception as ex:
            print(f"Error al sincronizar productos: {ex}")

    def cargar_tabla_usuarios():
        if not global_es_admin: return
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
        datos = {
            "username": new_user_name.value,
            "password": new_user_pass.value,
            "is_staff": True if new_user_role.value == "admin" else False
        }
        res = requests.post(f"{BASE_URL}/usuarios/", json=datos)
        if res.status_code in [200, 201]:
            mostrar_snack("✅ Usuario Creado", ft.Colors.GREEN)
            cargar_tabla_usuarios()
        else: mostrar_snack("Error al crear")

    def abrir_editar_producto(p):
        edit_dialog.title.value = "Editar Producto"
        btn_guardar_edit.text = "Guardar Cambios"
        edit_nombre.value = p['nombre']
        edit_precio.value = str(p['precio'])
        edit_stock.value = str(p['stock'])
        edit_codigo.value = p['codigo_barras']
        
        # Configurar el botón de guardar del diálogo para este producto específico
        btn_guardar_edit.on_click = lambda _: guardar_cambios_producto(p['id'])
        edit_dialog.open = True
        page.update()

    def abrir_crear_producto(codigo=""):
        edit_dialog.title.value = "Registrar Nuevo Producto"
        btn_guardar_edit.text = "Crear Producto"
        edit_nombre.value = ""
        edit_precio.value = ""
        edit_stock.value = ""
        edit_codigo.value = codigo
        btn_guardar_edit.on_click = lambda _: guardar_nuevo_producto()
        edit_dialog.open = True
        page.update()

    def guardar_cambios_producto(id_prod):
        try:
            datos = {
                "nombre": edit_nombre.value,
                "precio": float(edit_precio.value),
                "stock": int(edit_stock.value),
                "codigo_barras": edit_codigo.value
            }
            res = requests.put(f"{BASE_URL}/productos/{id_prod}/", json=datos, timeout=5)
            if res.status_code == 200:
                edit_dialog.open = False
                mostrar_snack("✅ Producto actualizado", ft.Colors.GREEN)
                cargar_tabla_stock()
                cargar_productos_busqueda()
            else:
                mostrar_snack("❌ Error al actualizar")
        except ValueError:
            mostrar_snack("❌ Datos numéricos inválidos")
        except Exception as e:
            mostrar_snack(f"Error: {e}")

    def guardar_nuevo_producto():
        try:
            if not edit_nombre.value or not edit_precio.value:
                mostrar_snack("❌ Nombre y Precio son obligatorios"); return
                
            datos = {
                "nombre": edit_nombre.value,
                "precio": float(edit_precio.value),
                "stock": int(edit_stock.value or 0),
                "codigo_barras": edit_codigo.value
            }
            res = requests.post(f"{BASE_URL}/productos/", json=datos, timeout=5)
            if res.status_code in [200, 201]:
                edit_dialog.open = False
                mostrar_snack("✅ Producto creado exitosamente", ft.Colors.GREEN)
                cargar_tabla_stock()
                cargar_productos_busqueda()
            else:
                mostrar_snack(f"❌ Error al crear: {res.text}")
        except ValueError:
            mostrar_snack("❌ Formato de precio o stock incorrecto")
        except Exception as e:
            mostrar_snack(f"Error de red: {e}")

    def eliminar_usuario(id_user):
        mostrar_snack(f"Eliminando usuario {id_user}...")
        pass

    def cargar_tabla_stock():
        tabla_stock.rows.clear()
        try:
            res = requests.get(f"{BASE_URL}/productos/", timeout=5)
            if res.status_code == 200:
                for p in res.json():
                    stock_actual = int(p.get('stock', 0))
                    tabla_stock.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(p.get('codigo_barras', 'S/C'))),
                        ft.DataCell(ft.Text(p['nombre'])),
                        ft.DataCell(ft.Text(f"${float(p['precio']):.2f}")),
                        ft.DataCell(ft.Text(str(stock_actual), weight="bold")),
                        # SOLO EL ADMIN PUEDE EDITAR
                        ft.DataCell(ft.IconButton(
                            ft.Icons.EDIT, 
                            icon_color=AZUL_UNAM, 
                            visible=global_es_admin,
                            on_click=lambda _, prod=p: abrir_editar_producto(prod)
                        ))
                    ]))
                page.update()
        except: pass

    # --- 4. VISTAS ---
    input_busqueda = ft.AutoComplete(
        suggestions=[], 
        on_select=lambda e: (setattr(input_busqueda, "value", e.selection), agregar_producto_event(None))
    )

    view_ventas = ft.Container(
        content=ft.Column([
            ft.Text("🛒 Módulo de Ventas", size=30, weight="bold", color=AZUL_UNAM),
            ft.Row([
                ft.Container(input_busqueda, expand=True), 
                input_cantidad, 
                ft.IconButton(
                    ft.Icons.CAMERA_ALT, 
                    icon_color=AZUL_UNAM, 
                    tooltip="Escanear Código", 
                    on_click=lambda e: abrir_camara(e, "venta")
                ),
                ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=ORO_UNAM, on_click=agregar_producto_event)
            ]),
            ft.Container(content=ft.ListView([tabla_ventas], expand=True), expand=True, border=ft.Border.all(1, "#DDDDDD"), border_radius=10, padding=10),
            ft.Row([ft.Column([input_recibido, txt_cambio_display]), ft.Column([txt_total_v, btn_finalizar])], alignment="spaceBetween")
        ]), expand=True
    )

    view_stock = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("📦 Control de Inventario", size=30, weight="bold", color=AZUL_UNAM),
                ft.Row([
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE, 
                        icon_color=AZUL_UNAM,
                        tooltip="Agregar manualmente",
                        on_click=lambda _: abrir_crear_producto("")
                    ),
                    ft.IconButton(
                        ft.Icons.QR_CODE_SCANNER, 
                        icon_color=AZUL_UNAM, 
                        tooltip="Escanear para buscar/crear", 
                        on_click=lambda e: abrir_camara(e, "stock")
                    ),
                ])
            ], alignment="spaceBetween"),
            ft.Container(content=ft.ListView([tabla_stock], expand=True), expand=True, border=ft.Border.all(1, "#DDDDDD"), border_radius=10)
        ]), expand=True, visible=False
    )

    view_usuarios = ft.Container(
        content=ft.Column([
            ft.Text("👥 Administración de Personal", size=30, weight="bold", color=AZUL_UNAM),
            ft.Row([
                ft.Card(content=ft.Container(padding=20, content=ft.Column([
                    ft.Text("Nuevo Usuario", weight="bold"), 
                    new_user_name, 
                    new_user_pass, 
                    new_user_role, 
                    ft.FilledButton("Guardar", bgcolor=AZUL_UNAM, color="white", on_click=guardar_usuario)
                ]))),
                ft.Container(content=ft.ListView([tabla_usuarios], expand=True), expand=True)
            ], expand=True)
        ]), expand=True, visible=False
    )

    view_corte = ft.Container(
        content=ft.Column([
            ft.Text("📊 Corte de Caja", size=30, weight="bold", color=AZUL_UNAM),
            ft.Text("Resumen de operaciones del día...")
        ]), expand=True, visible=False
    )

    # --- 5. NAVEGACIÓN ---
    def cambiar_tab(e):
        idx = e.control.selected_index
        view_ventas.visible = (idx == 0)
        view_stock.visible = (idx == 1)
        view_corte.visible = (idx == 2)
        view_usuarios.visible = (idx == 3)
        
        if idx == 1: cargar_tabla_stock()
        if idx == 3: cargar_tabla_usuarios()
        if idx == 4: reiniciar()
        page.update()

    rail = ft.NavigationRail(
        selected_index=0, label_type="all",
        unselected_label_text_style=ft.TextStyle(color=AZUL_UNAM),
        selected_label_text_style=ft.TextStyle(color=ORO_UNAM, weight="bold"),
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART, label="Ventas"),
            ft.NavigationRailDestination(icon=ft.Icons.INVENTORY, label="Stock"),
            ft.NavigationRailDestination(icon=ft.Icons.MONETIZATION_ON, label="Corte"),
            ft.NavigationRailDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS, label="Admin"),
            ft.NavigationRailDestination(icon=ft.Icons.LOGOUT, label="Salir"),
        ], on_change=cambiar_tab
    )

    def login(e):
        nonlocal global_es_admin, carrito
        try:
            res = requests.post(f"{BASE_URL}/login/", json={"username": txt_user.value, "password": txt_pass.value})
            if res.status_code == 200:
                data = res.json()
                global_es_admin = data.get("is_staff", False) # Capturamos el rol
                
                # RESETEAR ESTADOS DE LA UI
                carrito = []
                actualizar_interfaz_ventas()
                
                # RESTRICCIÓN DE ROLES EN EL MENÚ
                rail.destinations[3].visible = global_es_admin # Ocultar Admin
                rail.destinations[2].visible = global_es_admin # Ocultar Corte
                rail.selected_index = 0
                
                # FORZAR VISIBILIDAD DE VISTAS (Evita que se queden pegadas vistas de sesiones anteriores)
                view_ventas.visible = True
                view_stock.visible = False
                view_corte.visible = False
                view_usuarios.visible = False
                
                # Cargar datos iniciales
                cargar_productos_busqueda()

                page.clean()
                # IMPORTANTE: Agregar todas las vistas aquí para que existan en el DOM
                page.add(ft.Row([rail, ft.VerticalDivider(width=1), view_ventas, view_stock, view_corte, view_usuarios], expand=True))
            else: mostrar_snack("Credenciales inválidas")
        except: mostrar_snack("Error de conexión")

    login_card = ft.Card(
        content=ft.Container(padding=40, content=ft.Column([
            ft.Text("FESConnect", size=28, weight="bold", color=AZUL_UNAM),
            txt_user, txt_pass,
            ft.FilledButton("Iniciar Sesión", bgcolor=AZUL_UNAM, color="white", width=300, on_click=login)
        ], horizontal_alignment="center"))
    )

    def reiniciar():
        page.clean()
        page.vertical_alignment = "center"
        page.horizontal_alignment = "center"
        page.add(login_card)
        
        if edit_dialog in page.overlay: page.overlay.remove(edit_dialog)
        # Agregar componentes invisibles al DOM global
        page.overlay.append(edit_dialog)
        if barcode_scanner:
            page.overlay.append(barcode_scanner)

    reiniciar()

ft.run(main)