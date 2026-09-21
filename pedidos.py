# pedidos.py
import os
import json
from datetime import datetime
from database import get_connection

DATABASE_URL = os.getenv("DATABASE_URL")


def cargar_pedidos():
    """Carga todos los pedidos desde la BD."""
    if not DATABASE_URL:
        archivo = os.path.join(os.path.dirname(__file__), "pedidos.json")
        if not os.path.exists(archivo):
            return []
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos ORDER BY id")
    filas = cur.fetchall()
    cur.close()
    conn.close()

    pedidos = []
    for fila in filas:
        pedidos.append({
            "id": fila["id"],
            "fecha": fila["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
            "cliente": fila["cliente"],
            "telefono": fila["telefono"] or "",
            "direccion": fila["direccion"] or "",
            "items": fila["items"] if isinstance(fila["items"], dict) else json.loads(fila["items"]),
            "detalle": fila["detalle"],
            "total": float(fila["total"]),
            "estado": fila["estado"],
        })
    return pedidos


def guardar_pedidos(pedidos):
    """Solo para compatibilidad (JSON fallback)."""
    if not DATABASE_URL:
        archivo = os.path.join(os.path.dirname(__file__), "pedidos.json")
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)


def crear_pedido(pedido_items, nombre, telefono, direccion, total, detalle):
    """Crea un pedido en la BD."""
    if not DATABASE_URL:
        pedidos = cargar_pedidos()
        nuevo = {
            "id": len(pedidos) + 1,
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

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pedidos (cliente, telefono, direccion, items, detalle, total, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, fecha
    """, (nombre, telefono, direccion, json.dumps(pedido_items), detalle, total, "pendiente"))

    resultado = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": resultado["id"],
        "fecha": resultado["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
        "cliente": nombre,
        "telefono": telefono,
        "direccion": direccion,
        "items": pedido_items,
        "detalle": detalle,
        "total": total,
        "estado": "pendiente",
    }


def actualizar_estado(pedido_id, nuevo_estado):
    if not DATABASE_URL:
        pedidos = cargar_pedidos()
        for p in pedidos:
            if p["id"] == pedido_id:
                p["estado"] = nuevo_estado
                guardar_pedidos(pedidos)
                return True
        return False

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id))
    filas = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return filas > 0


def eliminar_pedido(pedido_id):
    if not DATABASE_URL:
        pedidos = cargar_pedidos()
        pedidos = [p for p in pedidos if p["id"] != pedido_id]
        guardar_pedidos(pedidos)
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
    conn.commit()
    cur.close()
    conn.close()


def pedidos_pendientes_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    pedidos = cargar_pedidos()
    return [p for p in pedidos if p["fecha"].startswith(hoy) and p["estado"] == "pendiente"]