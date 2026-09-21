# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, send_from_directory
import uuid
import os
import io
import csv
import re
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

from menu import cargar_menu, guardar_menu, menu_activo
from chatbot import responder
from pedidos import (
    cargar_pedidos, crear_pedido, actualizar_estado,
    eliminar_pedido, pedidos_pendientes_hoy
)

load_dotenv()

app = Flask(__name__)
app.secret_key = "cambia_esta_clave_secreta_123"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 🔥 Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def archivo_permitido(nombre):
    return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parsear_opciones(opciones_texto):
    """
    Convierte el texto de opciones en lista de dicts.
    Acepta: "Lechuga|10", "Lechuga Q10", "Lechuga - 10", "Lechuga"
    """
    resultado = []
    if not opciones_texto:
        return resultado

    for linea in opciones_texto.split("\n"):
        linea = linea.strip()
        if not linea:
            continue

        partes = re.split(r'[|]|\s+Q\s*|\s+-\s+', linea, maxsplit=1, flags=re.IGNORECASE)
        nombre = partes[0].strip()
        precio = 0

        if len(partes) > 1:
            precio_limpio = re.sub(r'[^0-9.]', '', partes[1])
            try:
                precio = float(precio_limpio) if precio_limpio else 0
            except:
                precio = 0

        resultado.append({"nombre": nombre, "precio": precio})

    return resultado


def calcular_extra_opciones(clave, opciones_elegidas, menu):
    if clave not in menu:
        return 0
    opciones_data = menu[clave].get("opciones", "")
    opciones_lista = parsear_opciones(opciones_data)
    precio_extra = 0
    for opcion in opciones_lista:
        if opcion["nombre"] in opciones_elegidas:
            precio_extra += opcion["precio"]
    return precio_extra


# 🔥 Inicializar base de datos
from database import init_db
from menu import inicializar_menu_si_vacio

try:
    init_db()
    inicializar_menu_si_vacio()
    print("✅ Base de datos lista")
except Exception as e:
    print(f"⚠️ Error con BD: {e}")
    print("   La app funcionará con archivos JSON locales")


# ------------------- UTILIDADES -------------------
def calcular_total(pedido, detalles_opciones=None):
    menu = menu_activo()
    total = 0

    for combo_key, cant in pedido.items():
        partes = combo_key.split("|", 1)
        clave = partes[0]
        opciones_str = partes[1] if len(partes) > 1 else ""

        if clave not in menu:
            continue

        precio_base = menu[clave]["precio"]
        precio_extra = 0

        if opciones_str:
            opciones_elegidas = [o.strip() for o in opciones_str.split(",")]
            precio_extra = calcular_extra_opciones(clave, opciones_elegidas, menu)

        total += (precio_base + precio_extra) * cant

    return total


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(app.static_folder, 'service-worker.js')


# ------------------- CLIENTE -------------------
@app.route("/")
def index():
    return render_template("index.html", menu=menu_activo())


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "").strip()

    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]

    try:
        respuesta = responder(user_id, mensaje)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"respuesta": f"Error: {e}"}), 500

    return jsonify({"respuesta": respuesta})


@app.route("/pedido", methods=["POST"])
def pedido():
    print("\n🟢 Entrando a /pedido")
    try:
        data = request.get_json()
        pedido_cliente = data.get("pedido", {})
        nombre = data.get("nombre", "Cliente")
        telefono = data.get("telefono", "")
        direccion = data.get("direccion", "")
        detalles_opciones = data.get("detallesOpciones", {})

        if not pedido_cliente:
            return jsonify({"ok": False, "error": "Pedido vacío"}), 400

        menu = menu_activo()
        detalle_lineas = []
        total_calculado = 0

        for combo_key, cant in pedido_cliente.items():
            partes = combo_key.split("|", 1)
            clave_real = partes[0]
            opciones_str = partes[1] if len(partes) > 1 else ""

            if clave_real not in menu:
                continue

            precio_base = menu[clave_real]["precio"]
            precio_extra = 0

            if opciones_str:
                opciones_elegidas = [o.strip() for o in opciones_str.split(",")]
                precio_extra = calcular_extra_opciones(clave_real, opciones_elegidas, menu)

            subtotal = (precio_base + precio_extra) * cant
            total_calculado += subtotal

            detalle_item = f"{cant} x {menu[clave_real]['nombre']}"
            if opciones_str:
                detalle_item += f" ({opciones_str})"
            detalle_item += f" = Q{subtotal:.2f}"
            detalle_lineas.append(detalle_item)

        detalle = "\n".join(detalle_lineas)

        nuevo = crear_pedido(pedido_cliente, nombre, telefono, direccion, total_calculado, detalle)
        print(f"✅ Pedido #{nuevo['id']} guardado - Total: Q{total_calculado:.2f}")

        return jsonify({"ok": True, "total": total_calculado, "pedido_id": nuevo["id"]})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------- ADMIN -------------------
def requiere_admin():
    return session.get("admin_logueado", False)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logueado"] = True
            return redirect(url_for("admin_pedidos"))
        return render_template("admin_login.html", error="Contraseña incorrecta")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logueado", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_panel():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    return render_template("admin.html", menu=cargar_menu())


@app.route("/admin/guardar", methods=["POST"])
def admin_guardar():
    if not requiere_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 401

    data = request.get_json()
    menu = cargar_menu()

    if data["accion"] == "agregar":
        clave = data["clave"].strip().lower().replace(" ", "_")
        if not clave:
            return jsonify({"ok": False, "error": "Clave vacía"}), 400
        if clave in menu:
            return jsonify({"ok": False, "error": "Ya existe esa clave"}), 400

        max_orden = max([item.get("orden", 0) for item in menu.values()], default=0)

        menu[clave] = {
            "nombre": data["nombre"],
            "precio": float(data["precio"]),
            "activo": True,
            "descripcion": data.get("descripcion", ""),
            "emoji": data.get("emoji", "🍽️"),
            "color": data.get("color", "#888"),
            "imagen": data.get("imagen", ""),
            "opciones": data.get("opciones", ""),
            "orden": max_orden + 1,
        }

    elif data["accion"] == "editar":
        clave = data["clave"]
        if clave not in menu:
            return jsonify({"ok": False, "error": "No existe"}), 404
        menu[clave]["nombre"] = data["nombre"]
        menu[clave]["precio"] = float(data["precio"])
        menu[clave]["descripcion"] = data.get("descripcion", "")
        if "emoji" in data:
            menu[clave]["emoji"] = data["emoji"]
        if "imagen" in data:
            menu[clave]["imagen"] = data["imagen"]
        if "opciones" in data:
            menu[clave]["opciones"] = data["opciones"]

    elif data["accion"] == "toggle":
        clave = data["clave"]
        if clave not in menu:
            return jsonify({"ok": False, "error": "No existe"}), 404
        menu[clave]["activo"] = not menu[clave].get("activo", True)

    elif data["accion"] == "eliminar":
        menu.pop(data["clave"], None)

    else:
        return jsonify({"ok": False, "error": "Acción inválida"}), 400

    guardar_menu(menu)
    return jsonify({"ok": True})


@app.route("/admin/reordenar", methods=["POST"])
def admin_reordenar():
    """Reordena los platillos."""
    if not requiere_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 401

    data = request.get_json()
    nuevo_orden = data.get("orden", [])

    menu = cargar_menu()

    for i, clave in enumerate(nuevo_orden):
        if clave in menu:
            menu[clave]["orden"] = i + 1

    guardar_menu(menu)
    return jsonify({"ok": True})


@app.route("/admin/subir_imagen", methods=["POST"])
def admin_subir_imagen():
    if not requiere_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 401

    if "imagen" not in request.files:
        return jsonify({"ok": False, "error": "No se envió archivo"}), 400

    archivo = request.files["imagen"]
    if archivo.filename == "":
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400

    if not archivo_permitido(archivo.filename):
        return jsonify({"ok": False, "error": "Formato no permitido (usa PNG, JPG, WEBP o GIF)"}), 400

    try:
        # 🔥 SUBIR A CLOUDINARY (no al servidor local)
        resultado = cloudinary.uploader.upload(
            archivo,
            folder="como-en-casa/platillos",
            transformation=[
                {"width": 800, "height": 600, "crop": "fill", "gravity": "auto"},
                {"quality": "auto:good"}
            ]
        )

        url = resultado.get("secure_url")
        print(f"✅ Imagen subida a Cloudinary: {url}")

        return jsonify({"ok": True, "url": url, "nombre": resultado.get("public_id")})

    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"Error al subir: {str(e)}"}), 500


# ------------------- PEDIDOS -------------------
@app.route("/admin/pedidos")
def admin_pedidos():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    return render_template("admin_pedidos.html")


@app.route("/admin/pedidos/lista")
def admin_pedidos_lista():
    if not requiere_admin():
        return jsonify({"ok": False}), 401

    pedidos = cargar_pedidos()
    pedidos_ordenados = list(reversed(pedidos))
    pendientes = pedidos_pendientes_hoy()

    hoy = datetime.now().strftime("%Y-%m-%d")
    pedidos_hoy = [p for p in pedidos if p["fecha"].startswith(hoy)]
    total_hoy = sum(p["total"] for p in pedidos_hoy)

    return jsonify({
        "ok": True,
        "pedidos": pedidos_ordenados,
        "pendientes": len(pendientes),
        "total_hoy": total_hoy,
        "cantidad_hoy": len(pedidos_hoy),
    })


@app.route("/admin/pedidos/estado", methods=["POST"])
def admin_pedidos_estado():
    if not requiere_admin():
        return jsonify({"ok": False}), 401
    data = request.get_json()
    if actualizar_estado(data.get("id"), data.get("estado")):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404


@app.route("/admin/pedidos/eliminar", methods=["POST"])
def admin_pedidos_eliminar():
    if not requiere_admin():
        return jsonify({"ok": False}), 401
    data = request.get_json()
    eliminar_pedido(data.get("id"))
    return jsonify({"ok": True})


# ------------------- REPORTES -------------------
@app.route("/admin/reportes")
def admin_reportes():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    return render_template("admin_reportes.html")


@app.route("/admin/reportes/datos")
def admin_reportes_datos():
    if not requiere_admin():
        return jsonify({"ok": False}), 401

    periodo = request.args.get("periodo", "dia")
    pedidos = cargar_pedidos()

    hoy = datetime.now()
    if periodo == "dia":
        desde = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "semana":
        desde = hoy - timedelta(days=hoy.weekday())
        desde = desde.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "mes":
        desde = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        desde = hoy.replace(hour=0, minute=0, second=0, microsecond=0)

    filtrados = []
    for p in pedidos:
        try:
            fecha_p = datetime.strptime(p["fecha"], "%Y-%m-%d %H:%M:%S")
            if fecha_p >= desde:
                filtrados.append(p)
        except:
            pass

    total_ventas = sum(p["total"] for p in filtrados)
    cantidad = len(filtrados)

    productos = {}
    for p in filtrados:
        for clave, cant in p.get("items", {}).items():
            clave_real = clave.split("|")[0]
            if clave_real not in productos:
                productos[clave_real] = {"cantidad": 0, "ventas": 0}
            productos[clave_real]["cantidad"] += cant

    menu = menu_activo()
    for clave in productos:
        if clave in menu:
            productos[clave]["nombre"] = menu[clave]["nombre"]
            productos[clave]["precio"] = menu[clave]["precio"]
            productos[clave]["ventas"] = productos[clave]["cantidad"] * menu[clave]["precio"]
        else:
            productos[clave]["nombre"] = clave
            productos[clave]["precio"] = 0

    productos_ordenados = sorted(productos.items(), key=lambda x: x[1]["cantidad"], reverse=True)

    return jsonify({
        "ok": True,
        "periodo": periodo,
        "total_ventas": total_ventas,
        "cantidad": cantidad,
        "promedio": total_ventas / cantidad if cantidad > 0 else 0,
        "pedidos": filtrados,
        "productos": [{"clave": k, **v} for k, v in productos_ordenados],
    })


@app.route("/admin/reportes/excel")
def admin_reportes_excel():
    if not requiere_admin():
        return redirect(url_for("admin_login"))

    periodo = request.args.get("periodo", "dia")
    pedidos = cargar_pedidos()

    hoy = datetime.now()
    if periodo == "dia":
        desde = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "semana":
        desde = hoy - timedelta(days=hoy.weekday())
        desde = desde.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        desde = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    filtrados = []
    for p in pedidos:
        try:
            fecha_p = datetime.strptime(p["fecha"], "%Y-%m-%d %H:%M:%S")
            if fecha_p >= desde:
                filtrados.append(p)
        except:
            pass

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["Reporte del restaurante"])
    writer.writerow([f"Período: {periodo}"])
    writer.writerow([f"Generado: {hoy.strftime('%Y-%m-%d %H:%M')}"])
    writer.writerow([])

    total = sum(p["total"] for p in filtrados)
    writer.writerow(["RESUMEN"])
    writer.writerow(["Total pedidos", len(filtrados)])
    writer.writerow(["Ventas totales", f"Q{total:.2f}"])
    writer.writerow(["Promedio por pedido", f"Q{(total/len(filtrados) if filtrados else 0):.2f}"])
    writer.writerow([])

    writer.writerow(["DETALLE DE PEDIDOS"])
    writer.writerow(["ID", "Fecha", "Cliente", "Teléfono", "Dirección", "Detalle", "Total", "Estado"])
    for p in filtrados:
        writer.writerow([
            p["id"], p["fecha"], p["cliente"], p.get("telefono", ""),
            p.get("direccion", ""), p.get("detalle", "").replace("\n", " | "),
            f"Q{p['total']:.2f}", p["estado"]
        ])

    contenido = output.getvalue()
    return Response(
        contenido,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_{periodo}_{hoy.strftime('%Y%m%d')}.csv"
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)