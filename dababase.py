# database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Devuelve una conexión a la base de datos PostgreSQL."""
    if not DATABASE_URL:
        raise Exception("Falta DATABASE_URL en las variables de entorno")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Crea las tablas si no existen."""
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL no configurada. Saltando inicialización de BD.")
        return

    conn = get_connection()
    cur = conn.cursor()

    # Tabla de menú
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            clave VARCHAR(100) PRIMARY KEY,
            nombre VARCHAR(200) NOT NULL,
            precio NUMERIC(10, 2) NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            descripcion TEXT,
            emoji VARCHAR(10),
            color VARCHAR(20),
            imagen TEXT
        )
    """)

    # Tabla de pedidos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente VARCHAR(200) NOT NULL,
            telefono VARCHAR(50),
            direccion TEXT,
            items JSONB NOT NULL,
            detalle TEXT NOT NULL,
            total NUMERIC(10, 2) NOT NULL,
            estado VARCHAR(30) DEFAULT 'pendiente'
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de datos inicializada")