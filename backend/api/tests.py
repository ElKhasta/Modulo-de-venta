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
