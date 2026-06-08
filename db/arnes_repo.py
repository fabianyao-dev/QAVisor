from psycopg2.extras import RealDictCursor
from db.db import get_connection

def get_arnes(numero_parte):
    """Regresa un arnés por número de parte, o None si no existe."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM quality.arnes WHERE numero_parte = %s",
                (numero_parte,)
            )
            return cur.fetchone()

def get_todos_arnes():
    """Regresa todos los arneses registrados."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM quality.arnes ORDER BY numero_parte"
            )
            return cur.fetchall()

def crear_arnes(numero_parte, descripcion=""):
    """Crea un nuevo arnés. Regresa el registro creado."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO quality.arnes (numero_parte, descripcion)
                VALUES (%s, %s)
                ON CONFLICT (numero_parte) DO NOTHING
                RETURNING *
                """,
                (numero_parte, descripcion)
            )
            conn.commit()
            return cur.fetchone()