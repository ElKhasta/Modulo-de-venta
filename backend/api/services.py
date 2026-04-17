from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import DetalleVenta, Producto, Venta


def _lock_product(product_id: int) -> Producto:
    return Producto.objects.select_for_update().get(pk=product_id)


def _resolve_price(detail_data: dict, producto: Producto) -> Decimal:
    return Decimal(detail_data.get("precio_historico") or producto.precio)


def _apply_sale_details(venta: Venta, detalles: list[dict]) -> Decimal:
    total = Decimal("0.00")

    for detail_data in detalles:
        producto = _lock_product(detail_data["producto"].pk)
        cantidad = detail_data["cantidad"]

        if producto.stock < cantidad:
            raise ValidationError(
                {
                    "detalles": [
                        f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}."
                    ]
                }
            )

        precio_historico = _resolve_price(detail_data, producto)
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_historico=precio_historico,
        )

        producto.stock -= cantidad
        producto.save(update_fields=["stock"])
        total += precio_historico * cantidad

    return total


@transaction.atomic
def create_sale(*, cliente, detalles: list[dict]) -> Venta:
    venta = Venta.objects.create(cliente=cliente)
    venta.total = _apply_sale_details(venta, detalles)
    venta.save(update_fields=["total"])
    return venta


@transaction.atomic
def update_sale(venta: Venta, *, cliente, detalles: list[dict]) -> Venta:
    current_details = list(venta.detalles.select_related("producto"))

    for detail in current_details:
        producto = _lock_product(detail.producto_id)
        producto.stock += detail.cantidad
        producto.save(update_fields=["stock"])

    venta.detalles.all().delete()
    venta.cliente = cliente
    venta.total = _apply_sale_details(venta, detalles)
    venta.save(update_fields=["cliente", "total"])
    return venta


@transaction.atomic
def delete_sale(venta: Venta) -> None:
    current_details = list(venta.detalles.select_related("producto"))

    for detail in current_details:
        producto = _lock_product(detail.producto_id)
        producto.stock += detail.cantidad
        producto.save(update_fields=["stock"])

    venta.delete()
