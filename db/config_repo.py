import json
import psycopg2
from psycopg2.extras import RealDictCursor
from db.db import get_connection

def get_configuracion_activa(numero_parte):
    """Regresa la configuración activa de un arnés, o None si no tiene."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM quality.configuracion
                WHERE numero_parte = %s AND activo = TRUE
                ORDER BY creado_en DESC
                LIMIT 1
                """,
                (numero_parte,)
            )
            return cur.fetchone()

def guardar_configuracion(numero_parte, rois, imagen_bytes=None):
    """
    Guarda la configuración y la imagen en formato binario.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Desactivar anteriores
            cur.execute("UPDATE quality.configuracion SET activo = FALSE WHERE numero_parte = %s", (numero_parte,))
            
            # Insertar nueva con el campo 'patron'
            cur.execute(
                """
                INSERT INTO quality.configuracion (numero_parte, rois, activo, patron)
                VALUES (%s, %s, TRUE, %s)
                RETURNING id
                """,
                (numero_parte, json.dumps(rois), psycopg2.Binary(imagen_bytes) if imagen_bytes else None)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
def get_patron_activo(numero_parte):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT patron FROM quality.configuracion WHERE numero_parte = %s AND activo = TRUE LIMIT 1",
                (numero_parte,)
            )
            res = cur.fetchone()
            return res[0] if res and res[0] else None