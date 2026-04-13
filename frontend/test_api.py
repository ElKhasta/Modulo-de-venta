import flet as ft
import requests

def main(page: ft.Page):
    page.title = "FES Connect - Punto de Venta"
    page.adaptive = True  # Look & Feel según el SO
    page.theme_mode = ft.ThemeMode.LIGHT
    
    carrito = []

    # --- COMPONENTES ---
    
    # Nuevo: Selector de Clientes
    dropdown_cliente = ft.Dropdown(
        label="Seleccionar Cliente",
        hint_text="¿A quién le vendemos?",
        expand=True,
        options=[ft.dropdown.Option("0", "Público General")],
        value="0"
    )

    input_busqueda = ft.TextField(
        label="Producto o Código", 
        expand=True, 
        on_submit=lambda e: agregar_producto(e)
    )
    input_cantidad = ft.TextField(
        label="Cant.", 
        value="1", 
        width=80, 
        text_align=ft.TextAlign.CENTER
    )
    
    tabla_ventas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Precio")),
            ft.DataColumn(ft.Text("Cant.")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[]
    )

    txt_total = ft.Text("Total: $0.00", size=25, weight="bold")

    btn_finalizar = ft.Button(
        "Finalizar Venta", 
        icon=ft.Icons.CHECK_CIRCLE, 
        on_click=lambda e: mostrar_confirmacion(e),
        disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.WHITE)
    )

    # --- LÓGICA DE INTERFAZ ---

    # Nuevo: Cargar clientes desde la API
    def cargar_clientes():
        try:
            res = requests.get("http://127.0.0.1:8000/api/clientes/", timeout=5)
            if res.status_code == 200:
                clientes = res.json()
                # Reiniciamos opciones con la opción por defecto
                dropdown_cliente.options = [ft.dropdown.Option("0", "Público General")]
                for c in clientes:
                    dropdown_cliente.options.append(
                        ft.dropdown.Option(str(c['id']), f"{c['nombre']} ({c['rfc'] or 'Sin RFC'})")
                    )
                page.update()
        except Exception as ex:
            print(f"Error al cargar clientes: {ex}")

    def actualizar_interfaz():
        tabla_ventas.rows.clear()
        total_acumulado = 0
        for item in carrito:
            subtotal = item['precio'] * item['cantidad']
            total_acumulado += subtotal
            tabla_ventas.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['nombre'])),
                    ft.DataCell(ft.Text(f"${item['precio']:.2f}")),
                    ft.DataCell(ft.Text(str(item['cantidad']))),
                    ft.DataCell(ft.Text(f"${subtotal:.2f}")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda _, i=item['id']: eliminar(i)))
                ])
            )
        
        txt_total.value = f"Total: ${total_acumulado:.2f}"
        if len(carrito) > 0:
            btn_finalizar.disabled = False
            btn_finalizar.style.bgcolor = ft.Colors.GREEN_700
        else:
            btn_finalizar.disabled = True
            btn_finalizar.style.bgcolor = ft.Colors.GREY_400
        
        page.update()

    def eliminar(item_id):
        nonlocal carrito
        carrito = [i for i in carrito if i['id'] != item_id]
        actualizar_interfaz()

    def agregar_producto(e):
        busqueda = input_busqueda.value.strip()
        if not busqueda: return
        
        try:
            res = requests.get("http://127.0.0.1:8000/api/productos/", timeout=5)
            productos = res.json()
            encontrado = next((p for p in productos if p['nombre'].lower() == busqueda.lower() or p['codigo_barras'] == busqueda), None)
            
            if encontrado:
                try:
                    cant = int(input_cantidad.value)
                except: cant = 1

                actual_en_carro = sum(i['cantidad'] for i in carrito if i['id'] == encontrado['id'])
                
                if encontrado['stock'] >= (actual_en_carro + cant):
                    for item in carrito:
                        if item['id'] == encontrado['id']:
                            item['cantidad'] += cant
                            break
                    else:
                        carrito.append({"id": encontrado['id'], "nombre": encontrado['nombre'], "precio": float(encontrado['precio']), "cantidad": cant})
                    
                    input_busqueda.value = ""; input_cantidad.value = "1"
                    actualizar_interfaz()
                else:
                    mostrar_snack(f"⚠️ Stock insuficiente: {encontrado['stock']} disp.", ft.Colors.ORANGE_700)
            else:
                mostrar_snack("❌ Producto no encontrado", ft.Colors.RED)
        except Exception as ex:
            print(f"Error: {ex}")
        
        input_busqueda.focus()
        page.update()

    def mostrar_snack(texto, color):
        snack = ft.SnackBar(ft.Text(texto), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def mostrar_confirmacion(e):
        def cerrar(res):
            dlg.open = False
            page.update()
            if res: enviar_a_django()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Venta"),
            content=ft.Text(f"¿Deseas cobrar {txt_total.value}?"),
            actions=[
                ft.TextButton("No", on_click=lambda _: cerrar(False)),
                ft.Button("Sí, cobrar", on_click=lambda _: cerrar(True), bgcolor="green", color="white")
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def enviar_a_django():
        # Ajuste: Capturar el cliente seleccionado
        # Si es "0", mandamos None para que Django lo guarde como "Sin cliente"
        id_cliente = dropdown_cliente.value if dropdown_cliente.value != "0" else None

        datos = {
            "cliente_id": id_cliente,
            "total": sum(i['precio'] * i['cantidad'] for i in carrito), 
            "productos": carrito
        }
        try:
            r = requests.post("http://127.0.0.1:8000/api/ventas/", json=datos, timeout=5)
            if r.status_code == 201:
                mostrar_snack("✅ Venta exitosa", ft.Colors.GREEN)
                carrito.clear()
                actualizar_interfaz()
                # Opcional: resetear cliente a Público General tras venta
                dropdown_cliente.value = "0"
            else:
                msg = r.json().get('error', 'Error en servidor')
                mostrar_snack(f"❌ {msg}", ft.Colors.RED)
        except:
            mostrar_snack("🌐 Sin conexión al servidor", ft.Colors.RED)

    # --- UI LAYOUT ---
    page.add(
        ft.Container(
            expand=True, padding=20,
            content=ft.Column([
                ft.Text("🛒 FES Connect POS", size=30, weight="bold"),
                
                # Fila de Cliente
                ft.Row([
                    dropdown_cliente, 
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: cargar_clientes(), tooltip="Actualizar Clientes")
                ]),
                
                # Fila de Producto
                ft.Row([
                    input_busqueda, 
                    input_cantidad, 
                    ft.IconButton(ft.Icons.ADD, on_click=agregar_producto)
                ]),
                
                ft.Container(
                    content=ft.ListView([tabla_ventas], expand=True), 
                    expand=True, 
                    border=ft.Border.all(1, "grey300"), 
                    border_radius=10
                ),
                
                ft.Row([txt_total, btn_finalizar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], expand=True)
        )
    )

    # Carga inicial de clientes al abrir la app
    cargar_clientes()

ft.run(main)