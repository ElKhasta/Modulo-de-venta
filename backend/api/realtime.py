import json
import logging
from typing import TYPE_CHECKING, Protocol

from django.conf import settings

if TYPE_CHECKING:
    from .models import MovimientoInventario

logger = logging.getLogger(__name__)


class InventoryEventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class NoOpInventoryPublisher:
    def publish(self, event_name: str, payload: dict) -> None:
        return None


class LoggerInventoryPublisher:
    def publish(self, event_name: str, payload: dict) -> None:
        logger.info(
            "inventory-event name=%s payload=%s",
            event_name,
            json.dumps(payload, ensure_ascii=False),
        )


def get_inventory_publisher() -> InventoryEventPublisher:
    backend = getattr(settings, "INVENTORY_REALTIME_BACKEND", "noop")
    if backend == "logger":
        return LoggerInventoryPublisher()
    return NoOpInventoryPublisher()


def build_inventory_movement_payload(movimiento: "MovimientoInventario") -> dict:
    return {
        "movement_id": movimiento.id,
        "producto_id": movimiento.producto_id,
        "codigo_barras": movimiento.producto.codigo_barras,
        "tipo_movimiento": movimiento.tipo_movimiento,
        "cantidad": movimiento.cantidad,
        "stock_anterior": movimiento.stock_anterior,
        "stock_nuevo": movimiento.stock_nuevo,
        "origen": movimiento.origen,
        "usuario_id": movimiento.usuario_id,
        "created_at": movimiento.created_at.isoformat(),
    }


def publish_inventory_movement(movimiento: "MovimientoInventario") -> None:
    if not getattr(settings, "INVENTORY_REALTIME_ENABLED", False):
        return

    try:
        payload = build_inventory_movement_payload(movimiento)
        get_inventory_publisher().publish("inventario.movimiento.creado", payload)
    except Exception:
        logger.exception("No se pudo publicar el evento de inventario en tiempo real.")
