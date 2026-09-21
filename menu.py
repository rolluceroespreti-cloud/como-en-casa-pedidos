# menu.py
import os
import json
from database import get_connection

DATABASE_URL = os.getenv("DATABASE_URL")


def cargar_menu():
    """Carga todo el menú desde la BD ordenado por 'orden'."""
    if not DATABASE_URL:
        archivo = os.path.join(os.path.dirname(__file__), "menu.json")
        if not os.path.exists(archivo):
            return {}
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu ORDER BY orden ASC, nombre ASC")
    filas = cur.fetchall()
    cur.close()
    conn.close()

    menu = {}
    for fila in filas:
        menu[fila["clave"]] = {
            "nombre": fila["nombre"],
            "precio": float(fila["precio"]),
            "activo": fila["activo"],
            "descripcion": fila["descripcion"] or "",
            "emoji": fila["emoji"] or "🍽️",
            "color": fila["color"] or "#888",
            "imagen": fila["imagen"] or "",
            "opciones": fila["opciones"] or "",
            "orden": fila.get("orden", 999) or 999,
        }
    return menu


def guardar_menu(menu):
    """Guarda el menú completo en la BD."""
    if not DATABASE_URL:
        archivo = os.path.join(os.path.dirname(__file__), "menu.json")
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(menu, f, indent=2, ensure_ascii=False)
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM menu")
    for clave, item in menu.items():
        cur.execute("""
            INSERT INTO menu (clave, nombre, precio, activo, descripcion, emoji, color, imagen, opciones, orden)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            clave,
            item["nombre"],
            item["precio"],
            item.get("activo", True),
            item.get("descripcion", ""),
            item.get("emoji", "🍽️"),
            item.get("color", "#888"),
            item.get("imagen", ""),
            item.get("opciones", ""),
            item.get("orden", 999),
        ))

    conn.commit()
    cur.close()
    conn.close()


def menu_activo():
    """Devuelve solo los platillos activos, ya ordenados."""
    menu = cargar_menu()
    return {k: v for k, v in menu.items() if v.get("activo", True)}


def mostrar_menu_texto():
    menu = menu_activo()
    if not menu:
        return "😔 Por ahora no hay platillos disponibles."

    lineas = ["📋 *MENÚ DISPONIBLE:*\n"]
    for clave, item in menu.items():
        linea = f"• {item['nombre']} - Q{item['precio']:.2f}"
        if item.get("descripcion"):
            linea += f"\n   _{item['descripcion']}_"
        lineas.append(linea)
    lineas.append("\nEscribe lo que deseas pedir.")
    return "\n".join(lineas)


def inicializar_menu_si_vacio():
    menu = cargar_menu()
    if menu:
        return

    archivo = os.path.join(os.path.dirname(__file__), "menu.json")
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            menu_inicial = json.load(f)
        guardar_menu(menu_inicial)
        print("✅ Menú inicial cargado desde menu.json")