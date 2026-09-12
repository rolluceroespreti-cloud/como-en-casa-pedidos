# chatbot.py
# Chatbot simplificado: solo responde preguntas y permite cancelar

from menu import menu_activo, mostrar_menu_texto

sesiones = {}


def obtener_sesion(user_id):
    if user_id not in sesiones:
        sesiones[user_id] = {"historial": []}
    return sesiones[user_id]


def responder(user_id, mensaje):
    """
    Chatbot de soporte:
    - Muestra el menú
    - Responde preguntas frecuentes
    - Ayuda a cancelar/modificar pedidos
    - NO toma pedidos (eso se hace con el carrito)
    """
    sesion = obtener_sesion(user_id)
    texto = mensaje.lower().strip()

    # --- Menú ---
    if any(p in texto for p in ["menu", "menú", "carta", "opciones", "que tienen", "qué tienen"]):
        return mostrar_menu_texto()

    # --- Saludos ---
    if any(p in texto for p in ["hola", "buenas", "buenos días", "buenas tardes", "hey"]):
        return (
            "¡Hola! 👋 Soy el asistente virtual.\n\n"
            "Puedo ayudarte con:\n"
            "• 📋 Ver el menú → escribe *menu*\n"
            "• ❌ Cancelar un pedido → escribe *cancelar*\n"
            "• 🕐 Horarios → escribe *horario*\n"
            "• 📍 Ubicación → escribe *dirección*\n"
            "• 💳 Formas de pago → escribe *pago*\n"
            "• 🛵 Envíos → escribe *envío*\n\n"
            "Para hacer un pedido, usa los botones ➕ del menú y luego el carrito 🛒."
        )

    # --- Cancelar ---
    if "cancelar" in texto:
        return (
            "❌ *Cancelar un pedido*\n\n"
            "Si ya confirmaste un pedido y quieres cancelarlo, por favor:\n"
            "1. Llama o escribe al restaurante directamente\n"
            "2. Indica tu nombre y número de pedido\n\n"
            "📞 También puedes ir al carrito y eliminar platillos antes de confirmar."
        )

    # --- Horarios ---
    if any(p in texto for p in ["horario", "hora", "abren", "cierran", "atienden"]):
        return (
            "🕐 *Nuestros horarios:*\n\n"
            "• Lunes a Viernes: 8:00 AM - 9:00 PM\n"
            "• Sábados: 8:00 AM - 10:00 PM\n"
            "• Domingos: 9:00 AM - 8:00 PM\n\n"
            "_Personaliza estos horarios con los tuyos._"
        )

    # --- Ubicación ---
    if any(p in texto for p in ["direccion", "dirección", "ubicacion", "ubicación", "donde", "dónde", "local"]):
        return (
            "📍 *Nuestra ubicación:*\n\n"
            "Estamos en: [Tu dirección aquí]\n"
            "Referencia: [Punto de referencia]\n\n"
            "_Personaliza esta dirección con la tuya._"
        )

    # --- Formas de pago ---
    if any(p in texto for p in ["pago", "pagar", "efectivo", "tarjeta", "transferencia", "formas de pago"]):
        return (
            "💳 *Formas de pago aceptadas:*\n\n"
            "• 💵 Efectivo (contra entrega)\n"
            "• 📱 Transferencia bancaria\n"
            "• 💳 Tarjeta (en local)\n\n"
            "_Personaliza esta lista con tus métodos._"
        )

    # --- Envíos ---
    if any(p in texto for p in ["envio", "envío", "domicilio", "delivery", "entrega", "reparto"]):
        return (
            "🛵 *Información de envíos:*\n\n"
            "• Hacemos entregas a domicilio\n"
            "• Costo de envío: Q10 - Q25 según la zona\n"
            "• Tiempo estimado: 30-45 minutos\n"
            "• Pedido mínimo: Q30\n\n"
            "_Personaliza estos datos con los tuyos._"
        )

    # --- Agradecimientos ---
    if any(p in texto for p in ["gracias", "graciass", "thanks"]):
        return "¡Con gusto! 😊 ¿Hay algo más en lo que pueda ayudarte?"

    # --- Despedida ---
    if any(p in texto for p in ["adios", "adiós", "chao", "bye", "hasta luego"]):
        return "¡Hasta luego! 👋 Gracias por visitarnos 🍔"

    # --- Precio de un platillo específico ---
    menu = menu_activo()
    for clave, item in menu.items():
        if item["nombre"].lower() in texto:
            return (
                f"🍽️ *{item['nombre']}*\n\n"
                f"💰 Precio: Q{item['precio']:.2f}\n"
                f"📝 {item.get('descripcion', 'Delicioso platillo')}\n\n"
                f"¿Deseas agregarlo al carrito? Usa el botón ➕ en el menú."
            )

    # --- Respuesta por defecto ---
    return (
        "🤔 No entendí bien tu pregunta. Prueba con:\n\n"
        "• *menu* → Ver el menú\n"
        "• *horario* → Nuestros horarios\n"
        "• *dirección* → Cómo llegar\n"
        "• *pago* → Formas de pago\n"
        "• *envío* → Info de delivery\n"
        "• *cancelar* → Cancelar un pedido\n\n"
        "Para hacer un pedido usa los botones ➕ del menú y luego el carrito 🛒."
    )