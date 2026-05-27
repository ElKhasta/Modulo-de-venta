from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cliente, Producto, Venta


User = get_user_model()


class AuthAndSalesFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="admin1234")
        self.cliente = Cliente.objects.create(
            nombre="Cliente Demo",
            email="cliente@example.com",
            telefono="5512345678",
            rfc="XAXX010101000",
        )
        self.producto = Producto.objects.create(
            nombre="Cafe americano",
            codigo_barras="750100000001",
            precio="25.00",
            stock=10,
        )

    def authenticate(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "admin", "password": "admin1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_login_returns_tokens_and_user(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "admin", "password": "admin1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "admin")

    def test_create_sale_updates_inventory(self):
        self.authenticate()
        response = self.client.post(
            reverse("venta-list"),
            {
                "cliente": self.cliente.id,
                "detalles": [
                    {
                        "producto": self.producto.id,
                        "cantidad": 2,
                        "precio_historico": "25.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)
        self.assertEqual(str(response.data["total"]), "50.00")

    def test_delete_sale_restores_inventory(self):
        self.authenticate()
        venta = Venta.objects.create(cliente=self.cliente, total="50.00")
        venta.detalles.create(producto=self.producto, cantidad=2, precio_historico="25.00")
        self.producto.stock = 8
        self.producto.save(update_fields=["stock"])

        response = self.client.delete(reverse("venta-detail", args=[venta.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)


class HardwareIngestionAndTransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="admin1234")
        self.cliente = Cliente.objects.create(
            nombre="Juan Perez",
            email="juan@perez.com",
            telefono="5512345679",
            rfc="PERJ800101XYZ",
        )
        self.producto_estandar = Producto.objects.create(
            nombre="Refresco de Cola",
            codigo_barras="750101112223",
            precio="18.50",
            stock=15,
        )
        self.producto_variable = Producto.objects.create(
            nombre="Queso Manchego Peso Variable",
            codigo_barras="200123",  # SKU base para prueba
            precio="120.00",
            stock=50,
        )

    def authenticate(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "admin", "password": "admin1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_semantic_resolution_by_barcode(self):
        self.authenticate()
        url = reverse("producto-detail", args=[self.producto_estandar.codigo_barras])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], self.producto_estandar.nombre)

    def test_procesar_escaneo_standard_barcode(self):
        self.authenticate()
        url = reverse("producto-procesar-escaneo")
        response = self.client.post(url, {"codigo": "750101112223"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tipo"], "producto")
        self.assertEqual(response.data["datos"]["nombre"], self.producto_estandar.nombre)
        self.assertFalse(response.data["datos"].get("es_peso_variable", False))

    def test_procesar_escaneo_loyalty_qr(self):
        self.authenticate()
        url = reverse("producto-procesar-escaneo")
        qr_payload = '{"email": "juan@perez.com", "telefono": "5512345679"}'
        response = self.client.post(url, {"codigo": qr_payload}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tipo"], "cliente")
        self.assertEqual(response.data["datos"]["nombre"], self.cliente.nombre)

    def test_procesar_escaneo_gs1_variable_weight(self):
        self.authenticate()
        url = reverse("producto-procesar-escaneo")
        # Barcode de peso variable: 2 (prefijo) + 00123 (SKU) + 00450 (monto: $4.50) + 1 (digito control)
        # Longitud 13: "2001230004501"
        # Nuestro SKU base del producto es "200123" que coincide con el inicio del barcode.
        codigo_peso_variable = "2001230004501"
        response = self.client.post(url, {"codigo": codigo_peso_variable}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tipo"], "producto")
        self.assertEqual(response.data["datos"]["nombre"], self.producto_variable.nombre)
        self.assertEqual(response.data["datos"]["precio"], "4.50")
        self.assertTrue(response.data["datos"]["es_peso_variable"])

    def test_descontar_stock_transactional(self):
        self.authenticate()
        url = reverse("producto-descontar-stock", args=[self.producto_estandar.codigo_barras])
        response = self.client.post(url, {"cantidad": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock"], 10)
        self.producto_estandar.refresh_from_db()
        self.assertEqual(self.producto_estandar.stock, 10)

    def test_descontar_stock_insufficient(self):
        self.authenticate()
        url = reverse("producto-descontar-stock", args=[self.producto_estandar.codigo_barras])
        response = self.client.post(url, {"cantidad": 20}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Stock insuficiente", response.data["detail"])
        self.producto_estandar.refresh_from_db()
        self.assertEqual(self.producto_estandar.stock, 15)

    def test_remote_scanning_flow(self):
        self.authenticate()
        
        # 1. Enviar escaneo remoto desde móvil
        url_scan = reverse("producto-escanear-remoto")
        response_scan = self.client.post(url_scan, {"codigo": "750101112223"}, format="json")
        self.assertEqual(response_scan.status_code, status.HTTP_200_OK)
        self.assertEqual(response_scan.data["status"], "success")

        # 2. Recuperar escaneos remotos en el cliente de escritorio
        url_get = reverse("producto-obtener-escaneos-remotos")
        response_get = self.client.get(url_get)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertIn("750101112223", response_get.data["escaneos"])

        # 3. Verificar que se limpie la cola después de leerla
        response_get_again = self.client.get(url_get)
        self.assertEqual(response_get_again.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_get_again.data["escaneos"]), 0)


