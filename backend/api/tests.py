from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cliente, MovimientoInventario, Producto, Venta


User = get_user_model()


class ApiInventoryFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="admin1234")
        self.cliente = Cliente.objects.create(
            nombre="Cliente Demo",
            email="cliente@example.com",
            telefono="5512345678",
            rfc="XAXX010101000",
        )

    def authenticate(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "admin", "password": "admin1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_login_returns_tokens_and_user(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "admin", "password": "admin1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "admin")

    def test_create_producto_from_api(self):
        self.authenticate()
        response = self.client.post(
            "/api/productos/",
            {
                "nombre": "Cafe americano",
                "codigo_barras": "750100000001",
                "precio": "25.00",
                "stock": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["codigo_barras"], "750100000001")
        self.assertEqual(response.data["stock"], 10)

    def test_resolve_scan_by_barcode(self):
        Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )
        response = self.client.post(
            "/api/inventario/resolve-scan/",
            {"codigo_barras": "750100000001"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["existe"])
        self.assertEqual(response.data["producto"]["codigo_barras"], "750100000001")
        self.assertEqual(response.data["stock_actual"], 10)

    def test_increment_stock_with_inventory_movement(self):
        self.authenticate()
        producto = Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )
        response = self.client.post(
            "/api/inventario/movimientos/",
            {
                "codigo_barras": "750100000001",
                "tipo": "incrementar",
                "cantidad": 2,
                "nota": "ajuste manual",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["stock_anterior"], 10)
        self.assertEqual(response.data["stock_nuevo"], 12)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 12)

    def test_decrement_stock_with_inventory_movement(self):
        self.authenticate()
        producto = Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )
        response = self.client.post(
            "/api/inventario/movimientos/",
            {
                "codigo_barras": "750100000001",
                "tipo": "disminuir",
                "cantidad": 3,
                "nota": "ajuste manual",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["stock_anterior"], 10)
        self.assertEqual(response.data["stock_nuevo"], 7)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 7)

    def test_reject_negative_stock_movement(self):
        producto = Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=1,
        )
        response = self.client.post(
            "/api/inventario/movimientos/",
            {
                "codigo_barras": "750100000001",
                "tipo": "disminuir",
                "cantidad": 2,
                "nota": "ajuste invalido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 1)

    def test_inventory_movement_is_created_and_tracks_user(self):
        self.authenticate()
        Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )
        response = self.client.post(
            "/api/inventario/movimientos/",
            {
                "codigo_barras": "750100000001",
                "tipo": "incrementar",
                "cantidad": 2,
                "nota": "ajuste manual",
                "origen": "app_movil",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        movimiento = MovimientoInventario.objects.get(id=response.data["movimiento"]["id"])
        self.assertEqual(movimiento.usuario_id, self.user.id)
        self.assertEqual(movimiento.origen, "app_movil")
        self.assertEqual(movimiento.codigo_barras_leido, "750100000001")

    def test_sale_flow_keeps_stock_compatible(self):
        self.authenticate()
        producto = Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )
        response = self.client.post(
            "/api/ventas/",
            {
                "cliente": self.cliente.id,
                "detalles": [
                    {
                        "producto": producto.id,
                        "cantidad": 2,
                        "precio_historico": "25.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 8)
        self.assertEqual(str(response.data["total"]), "50.00")

        venta = Venta.objects.get(id=response.data["id"])
        delete_response = self.client.delete(f"/api/ventas/{venta.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        producto.refresh_from_db()
        self.assertEqual(producto.stock, 10)
