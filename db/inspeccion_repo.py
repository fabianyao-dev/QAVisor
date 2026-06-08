from psycopg2.extras import RealDictCursor
from db.db import get_connection

def registrar_inspeccion(configuracion_id, resultado):
    """
    Registra una sola inspección (una pieza).
    resultado: True = OK, False = FAIL
    Regresa el id del registro.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO quality.inspeccion
                    (configuracion_id, resultado, total_ok, total_fail)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    configuracion_id,
                    resultado,
                    1 if resultado else 0,
                    0 if resultado else 1,
                )
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id

def get_resumen_sesion(configuracion_id, desde=None):
    """
    Regresa conteo de OK, FAIL y total de una sesión.
    Si se pasa 'desde' (datetime), filtra solo desde esa fecha.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT
                    COUNT(*)           AS total,
                    SUM(CASE WHEN resultado THEN 1 ELSE 0 END) AS ok,
                    SUM(CASE WHEN NOT resultado THEN 1 ELSE 0 END) AS fail
                FROM quality.inspeccion
                WHERE configuracion_id = %s
            """
            params = [configuracion_id]

            if desde:
                query += " AND fecha_hora >= %s"
                params.append(desde)

            cur.execute(query, params)
            return cur.fetchone()