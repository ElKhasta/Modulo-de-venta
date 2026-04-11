import flet as ft
import requests

def main(page: ft.Page):
    page.title = "Prueba de Conexión POS"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Texto donde mostraremos los datos
    lista_productos = ft.Column()

    def obtener_datos(e):
        try:
            # La URL que acabamos de probar en el navegador
            response = requests.get("http://127.0.0.1:8000/api/productos/")
            data = response.json()
            
            lista_productos.controls.clear()
            for prod in data:
                lista_productos.controls.append(
                    ft.Text(f"📦 {prod['nombre']} - ${prod['precio']} (Stock: {prod['stock']})")
                )
            page.update()
        except Exception as ex:
            lista_productos.controls.append(ft.Text(f"Error: {ex}", color="red"))
            page.update()

    # Botón para activar la magia
    btn = ft.ElevatedButton("Consultar Inventario Real", on_click=obtener_datos)

    page.add(
        ft.Text("Bienvenido al Punto de Venta", size=30, weight="bold"),
        btn,
        lista_productos
    )

ft.app(target=main)