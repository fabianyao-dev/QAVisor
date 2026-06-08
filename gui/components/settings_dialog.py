# gui/components/settings_dialog.py
import psycopg2
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGroupBox, QMessageBox, QComboBox
)
from PySide6.QtCore import QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Conexiones Base de Datos")
        self.resize(450, 460)
        self.settings = QSettings("QAVisorApp", "DBConfig")
        self._setup_ui()
        self._cargar_valores_guardados()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- NUEVO: Selector de Modo de Operación ---
        group_modo = QGroupBox("Modo de Operación de Red")
        layout_modo = QVBoxLayout(group_modo)
        self.cmb_modo = QComboBox()
        self.cmb_modo.addItems([
            "AUTOMATICO (Híbrido con Failover)",
            "SOLO SERVIDOR CENTRAL (Forzado)",
            "SOLO LOCAL / OFFLINE (Directo - Sin Retrasos)"
        ])
        layout_modo.addWidget(QLabel("Selecciona el comportamiento de la app:"))
        layout_modo.addWidget(self.cmb_modo)
        layout.addWidget(group_modo)

        # --- Grupo Servidor Principal ---
        group_prod = QGroupBox("Servidor Principal (Producción)")
        layout_prod = QVBoxLayout(group_prod)
        self.txt_prod_host = QLineEdit()
        self.txt_prod_db = QLineEdit()
        self.txt_prod_user = QLineEdit()
        self.txt_prod_pass = QLineEdit()
        self.txt_prod_pass.setEchoMode(QLineEdit.Password)

        layout_prod.addWidget(QLabel("Host / IP:"))
        layout_prod.addWidget(self.txt_prod_host)
        layout_prod.addWidget(QLabel("Base de Datos:"))
        layout_prod.addWidget(self.txt_prod_db)
        layout_prod.addWidget(QLabel("Usuario:"))
        layout_prod.addWidget(self.txt_prod_user)
        layout_prod.addWidget(QLabel("Contraseña:"))
        layout_prod.addWidget(self.txt_prod_pass)
        layout.addWidget(group_prod)

        # --- Grupo Redundancia Local ---
        group_local = QGroupBox("Redundancia Local (Estación)")
        layout_local = QVBoxLayout(group_local)
        self.txt_local_host = QLineEdit()
        self.txt_local_db = QLineEdit()
        self.txt_local_user = QLineEdit()
        self.txt_local_pass = QLineEdit()
        self.txt_local_pass.setEchoMode(QLineEdit.Password)

        layout_local.addWidget(QLabel("Host / IP Local:"))
        layout_local.addWidget(self.txt_local_host)
        layout_local.addWidget(QLabel("Base de Datos Local:"))
        layout_local.addWidget(self.txt_local_db)
        layout_local.addWidget(QLabel("Usuario Local:"))
        layout_local.addWidget(self.txt_local_user)
        layout_local.addWidget(QLabel("Contraseña Local:"))
        layout_local.addWidget(self.txt_local_pass)
        layout.addWidget(group_local)

        # --- Botones de Acción ---
        hbox_btns = QHBoxLayout()
        self.btn_probar = QPushButton("⚡ Probar Conexión")
        self.btn_guardar = QPushButton("💾 Guardar y Aplicar")
        self.btn_cancelar = QPushButton("Cancelar")

        self.btn_probar.clicked.connect(self.handle_probar_conexion)
        self.btn_guardar.clicked.connect(self.handle_guardar)
        self.btn_cancelar.clicked.connect(self.reject)

        hbox_btns.addWidget(self.btn_probar)
        hbox_btns.addWidget(self.btn_guardar)
        hbox_btns.addWidget(self.btn_cancelar)
        layout.addLayout(hbox_btns)

    def _cargar_valores_guardados(self):
        # Cargar el modo activo (por defecto 0: AUTOMATICO)
        modo_index = int(self.settings.value("modo_red", 0))
        self.cmb_modo.setCurrentIndex(modo_index)

        self.txt_prod_host.setText(self.settings.value("prod_host", ""))
        self.txt_prod_db.setText(self.settings.value("prod_db", ""))
        self.txt_prod_user.setText(self.settings.value("prod_user", ""))
        self.txt_prod_pass.setText(self.settings.value("prod_pass", ""))

        self.txt_local_host.setText(self.settings.value("local_host", "localhost"))
        self.txt_local_db.setText(self.settings.value("local_db", ""))
        self.txt_local_user.setText(self.settings.value("local_user", "postgres"))
        self.txt_local_pass.setText(self.settings.value("local_pass", ""))

    def handle_probar_conexion(self):
        reporte = []
        prod_ok, local_ok = False, False

        # Probamos el servidor principal
        try:
            conn_prod = psycopg2.connect(
                host=self.txt_prod_host.text(),
                database=self.txt_prod_db.text(),
                user=self.txt_prod_user.text(),
                password=self.txt_prod_pass.text(),
                connect_timeout=2
            )
            conn_prod.close()
            prod_ok = True
            reporte.append("🌐 Servidor Principal: ✅ OK")
        except Exception as e:
            reporte.append(f"🌐 Servidor Principal: ❌ ERROR ({str(e).split('\n')[0]})")

        # Probamos la local
        try:
            conn_local = psycopg2.connect(
                host=self.txt_local_host.text(),
                database=self.txt_local_db.text(),
                user=self.txt_local_user.text(),
                password=self.txt_local_pass.text(),
                connect_timeout=2
            )
            conn_local.close()
            local_ok = True
            reporte.append("💻 Redundancia Local: ✅ OK")
        except Exception as e:
            reporte.append(f"💻 Redundancia Local: ❌ ERROR ({str(e).split('\n')[0]})")

        QMessageBox.information(self, "Diagnóstico de Red", "\n".join(reporte))

    def handle_guardar(self):
        # Guardar el índice del modo seleccionado
        self.settings.setValue("modo_red", self.cmb_modo.currentIndex())

        self.settings.setValue("prod_host", self.txt_prod_host.text())
        self.settings.setValue("prod_db", self.txt_prod_db.text())
        self.settings.setValue("prod_user", self.txt_prod_user.text())
        self.settings.setValue("prod_pass", self.txt_prod_pass.text()) 

        self.settings.setValue("local_host", self.txt_local_host.text())
        self.settings.setValue("local_db", self.txt_local_db.text())
        self.settings.setValue("local_user", self.txt_local_user.text())
        self.settings.setValue("local_pass", self.txt_local_pass.text())

        QMessageBox.information(self, "Guardado", "Modo de red y credenciales actualizadas.")
        self.accept()