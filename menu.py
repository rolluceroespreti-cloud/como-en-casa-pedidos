# menu.py
import json
import os

ARCHIVO_MENU = os.path.join(os.path.dirname(__file__), "menu.json")


def cargar_menu():
    if not os.path.exists(ARCHIVO_MENU):
        return {}
    with open(ARCHIVO_MENU, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_menu(menu):
    with open(ARCHIVO_MENU, "w", encoding="utf-8") as f:
        json.dump(menu, f, indent=2, ensure_ascii=False)


def menu_activo():
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
    lineas.append("\nEscribe lo que deseas pedir. Ejemplo:")
    lineas.append('"2 hamburguesas y 1 refresco"')
    return "\n".join(lineas)