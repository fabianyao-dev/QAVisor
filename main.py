# main.py
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from gui.app import App

def main():
    # ─── FORZAR A WINDOWS A RECONOCER TU LOGO EN LA BARRA DE TAREAS ───
    try:
        # Crea un ID de aplicación único para el sistema
        myappid = u'qavisor.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    # ──────────────────────────────────────────────────────────────────

    app = QApplication(sys.argv)
    window = App()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()