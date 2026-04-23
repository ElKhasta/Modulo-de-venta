from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import DetalleVenta, MovimientoInventario, Producto, Venta
from .realtime import publish_inventory_movement


def _optional_user(user):
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def _lock_product(product_id: int) -> Producto:
    return Producto.objects.select_for_update().get(pk=product_id)


def _resolve_price(detail_data: dict, producto: Producto) -> Decimal:
    return Decimal(detail_data.get("precio_historico") or producto.precio)


def _create_inventory_movement(
    *,
    producto: Producto,
    tipo_movimiento: str,
    cantidad: int,
    stock_anterior: int,
    stock_nuevo: int,
    usuario=None,
    origen: str = "",
    codigo_barras_leido: str = "",
    nota: str = "",
) -> MovimientoInventario:
    movimiento = MovimientoInventario.objects.create(
        producto=producto,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        usuario=_optional_user(usuario),
        origen=origen,
        codigo_barras_leido=codigo_barras_leido,
        nota=nota,
    )
    transaction.on_commit(lambda: publish_inventory_movement(movimiento))
    return movimiento


def _apply_inventory_change(
    *,
    producto: Producto,
    tipo_movimiento: str,
    cantidad: int,
    usuario=None,
    origen: str = "",
    codigo_barras_leido: str = "",
    nota: str = "",
) -> MovimientoInventario:
    stock_anterior = producto.stock
    cantidad = int(cantidad)

    if tipo_movimiento in {
        MovimientoInventario.TIPO_INCREMENTAR,
        MovimientoInventario.TIPO_DISMINUIR,
        MovimientoInventario.TIPO_ALTA_PRODUCTO,
    } and cantidad <= 0:
        raise ValidationError({"cantidad": "La cantidad debe ser mayor a cero."})

    if tipo_movimiento == MovimientoInventario.TIPO_INCREMENTAR:
        stock_nuevo = stock_anterior + cantidad
    elif tipo_movimiento == MovimientoInventario.TIPO_DISMINUIR:
        stock_nuevo = stock_anterior - cantidad
        if stock_nuevo < 0:
            raise ValidationError(
                {
                    "cantidad": (
                        f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}."
                    )
                }
            )
    elif tipo_movimiento == MovimientoInventario.TIPO_ALTA_PRODUCTO:
        stock_nuevo = stock_anterior + cantidad
    elif tipo_movimiento == MovimientoInventario.TIPO_BAJA_LOGICA:
        if cantidad < 0:
            raise ValidationError({"cantidad": "La cantidad no puede ser negativa."})
        stock_nuevo = stock_anterior
    else:
        raise ValidationError({"tipo_movimiento": "Tipo de movimiento no soportado."})

    if stock_nuevo != stock_anterior:
        producto.stock = stock_nuevo
        producto.save(update_fields=["stock"])

    return _create_inventory_movement(
        producto=producto,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        usuario=usuario,
        origen=origen,
        codigo_barras_leido=codigo_barras_leido,
        nota=nota,
    )


@transaction.atomic
def apply_inventory_movement(
    *,
    product_id: int,
    tipo_movimiento: str,
    cantidad: int,
    usuario=None,
    origen: str = "",
    codigo_barras_leido: str = "",
    nota: str = "",
) -> tuple[Producto, MovimientoInventario]:
    producto = _lock_product(product_id)
    movimiento = _apply_inventory_change(
        producto=producto,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        usuario=usuario,
        origen=origen,
        codigo_barras_leido=codigo_barras_leido,
        nota=nota,
    )
    return producto, movimiento


@transaction.atomic
def create_product_with_stock_tracking(*, validated_data: dict, usuario=None, origen: str = "") -> Producto:
    producto = Producto.objects.create(**validated_data)
    _create_inventory_movement(
        producto=producto,
        tipo_movimiento=MovimientoInventario.TIPO_ALTA_PRODUCTO,
        cantidad=producto.stock,
        stock_anterior=0,
        stock_nuevo=producto.stock,
        usuario=usuario,
        origen=origen or "api.productos.create",
        codigo_barras_leido=producto.codigo_barras,
        nota="Alta de producto",
    )
    return producto


@transaction.atomic
def update_product_with_stock_tracking(
    *,
    producto: Producto,
    validated_data: dict,
    usuario=None,
    origen: str = "",
) -> Producto:
    producto_bloqueado = _lock_product(producto.pk)
    stock_anterior = producto_bloqueado.stock
    stock_nuevo = validated_data.pop("stock", None)

    for field_name, value in validated_data.items():
        setattr(producto_bloqueado, field_name, value)

    if stock_nuevo is not None and stock_nuevo < 0:
        raise ValidationError({"stock": "El stock no puede ser negativo."})

    if stock_nuevo is not None:
        producto_bloqueado.stock = stock_nuevo

    producto_bloqueado.save()

    if stock_nuevo is not None and stock_nuevo != stock_anterior:
        tipo_movimiento = (
            MovimientoInventario.TIPO_INCREMENTAR
            if stock_nuevo > stock_anterior
            else MovimientoInventario.TIPO_DISMINUIR
        )
        cantidad = abs(stock_nuevo - stock_anterior)
        _create_inventory_movement(
            producto=producto_bloqueado,
            tipo_movimiento=tipo_movimiento,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            usuario=usuario,
            origen=origen or "api.productos.update",
            codigo_barras_leido=producto_bloqueado.codigo_barras,
            nota="Ajuste de stock desde actualización de producto",
        )

    return producto_bloqueado


def _apply_sale_details(venta: Venta, detalles: list[dict], *, usuario=None) -> Decimal:
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

        _apply_inventory_change(
            producto=producto,
            tipo_movimiento=MovimientoInventario.TIPO_DISMINUIR,
            cantidad=cantidad,
            usuario=usuario,
            origen="venta",
            codigo_barras_leido=producto.codigo_barras,
            nota=f"Salida por venta #{venta.id}",
        )
        total += precio_historico * cantidad

    return total


@transaction.atomic
def create_sale(*, cliente, detalles: list[dict], usuario=None) -> Venta:
    venta = Venta.objects.create(cliente=cliente)
    venta.total = _apply_sale_details(venta, detalles, usuario=usuario)
    venta.save(update_fields=["total"])
    return venta


@transaction.atomic
def update_sale(venta: Venta, *, cliente, detalles: list[dict], usuario=None) -> Venta:
    current_details = list(venta.detalles.select_related("producto"))

    for detail in current_details:
        producto = _lock_product(detail.producto_id)
        _apply_inventory_change(
            producto=producto,
            tipo_movimiento=MovimientoInventario.TIPO_INCREMENTAR,
            cantidad=detail.cantidad,
            usuario=usuario,
            origen="venta",
            codigo_barras_leido=producto.codigo_barras,
            nota=f"Reversión por actualización de venta #{venta.id}",
        )

    venta.detalles.all().delete()
    venta.cliente = cliente
    venta.total = _apply_sale_details(venta, detalles, usuario=usuario)
    venta.save(update_fields=["cliente", "total"])
    return venta


@transaction.atomic
def delete_sale(venta: Venta, *, usuario=None) -> None:
    current_details = list(venta.detalles.select_related("producto"))

    for detail in current_details:
        producto = _lock_product(detail.producto_id)
        _apply_inventory_change(
            producto=producto,
            tipo_movimiento=MovimientoInventario.TIPO_INCREMENTAR,
            cantidad=detail.cantidad,
            usuario=usuario,
            origen="venta",
            codigo_barras_leido=producto.codigo_barras,
            nota=f"Reversión por eliminación de venta #{venta.id}",
        )

    venta.delete()
