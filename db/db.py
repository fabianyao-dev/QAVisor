# db/db.py
import psycopg2
from PySide6.QtCore import QSettings
from contextlib import contextmanager

@contextmanager
def get_connection():
    settings = QSettings("QAVisorApp", "DBConfig")
    
    # Leer modo de red seleccionado (0: AUTOMATICO, 1: FORZAR_SERVER, 2: FORZAR_LOCAL)
    modo_red = int(settings.value("modo_red", 0))

    DB_PROD = {
        "host": settings.value("prod_host", ""),
        "database": settings.value("prod_db", ""),
        "user": settings.value("prod_user", ""),
        "password": settings.value("prod_pass", ""),
        "connect_timeout": 2
    }

    DB_LOCAL = {
        "host": settings.value("local_host", "localhost"),
        "database": settings.value("local_db", ""),
        "user": settings.value("local_user", "postgres"),
        "password": settings.value("local_pass", "")
    }

    conn = None
    
    try:
        # CASO 1: MODO SÓLO LOCAL / OFFLINE (Forzado directo)
        if modo_red == 2:
            conn = psycopg2.connect(**DB_LOCAL)
            yield conn
            return # Termina el contexto de forma inmediata

        # CASO 2: MODO SÓLO SERVIDOR CENTRAL
        elif modo_red == 1:
            conn = psycopg2.connect(**DB_PROD)
            yield conn
            return

        # CASO 3: MODO AUTOMÁTICO (Failover con reintento por software)
        else:
            try:
                conn = psycopg2.connect(**DB_PROD)
                yield conn
            except psycopg2.OperationalError:
                # El principal no respondió, conmutamos al local
                conn = psycopg2.connect(**DB_LOCAL)
                yield conn

    except Exception as e:
        raise RuntimeError(f"Fallo de conexión en el modo seleccionado ({modo_red}): {str(e)}")
        
    finally:
        if conn is not None:
            conn.close()