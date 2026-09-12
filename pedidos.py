# pedidos.py
import json
import os
from datetime import datetime

ARCHIVO = os.path.join(os.path.dirname(__file__), "pedidos.json")


def cargar_pedidos():
    if not os.path.exists(ARCHIVO):
        return []
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def guardar_pedidos(pedidos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=2, ensure_ascii=False)


def crear_pedido(pedido_items, nombre, telefono, direccion, total, detalle):
    pedidos = cargar_pedidos()
    numero = len(pedidos) + 1

    nuevo = {
        "id": numero,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente": nombre,
        "telefono": telefono,
        "direccion": direccion,
        "items": pedido_items,
        "detalle": detalle,
        "total": total,
        "estado": "pendiente",
    }

    pedidos.append(nuevo)
    guardar_pedidos(pedidos)
    return nuevo


def actualizar_estado(pedido_id, nuevo_estado):
    pedidos = cargar_pedidos()
    for p in pedidos:
        if p["id"] == pedido_id:
            p["estado"] = nuevo_estado
            guardar_pedidos(pedidos)
            return True
    return False


def eliminar_pedido(pedido_id):
    pedidos = cargar_pedidos()
    pedidos = [p for p in pedidos if p["id"] != pedido_id]
    guardar_pedidos(pedidos)


def pedidos_pendientes_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    pedidos = cargar_pedidos()
    return [p for p in pedidos if p["fecha"].startswith(hoy) and p["estado"] == "pendiente"]