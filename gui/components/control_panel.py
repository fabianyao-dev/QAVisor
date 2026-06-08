from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QTextEdit
)
from PySide6.QtCore import Signal, Qt

class ControlPanel(QWidget):
    # Señales (Eventos)
    on_seleccionar_arnes_clicked = Signal()
    on_camara_changed = Signal(int)
    on_configurar_clicked = Signal() # <--- LA NUEVA SEÑAL
    on_run_clicked = Signal()

    def __init__(self, camaras, parent=None):
        super().__init__(parent)
        self.camaras = camaras
        self._setup_ui()

    def _setup_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(9, 9, 9, 9)
        vbox.setSpacing(8)

        # -- Arnés Activo --
        self.lbl_arnes_activo = QLabel("Arnés Activo: NINGUNO")
        self.lbl_arnes_activo.setStyleSheet("font-weight: bold; color: #ffcc00; font-size: 14px;")
        vbox.addWidget(self.lbl_arnes_activo)

        self.btn_seleccionar = QPushButton("Seleccionar / Crear Arnés")
        self.btn_seleccionar.clicked.connect(self.on_seleccionar_arnes_clicked.emit)
        vbox.addWidget(self.btn_seleccionar)
        vbox.addSpacing(15)

        # -- Selector de Cámara --
        hbox_cam = QHBoxLayout()
        self.combo_camara = QComboBox()
        for idx, (c_id, _) in enumerate(self.camaras):
            label = "Simulada" if c_id == -1 else f"Cámara {idx}"
            self.combo_camara.addItem(label)
        self.combo_camara.currentIndexChanged.connect(self.on_camara_changed.emit)
        hbox_cam.addWidget(QLabel("Cámara:"))
        hbox_cam.addWidget(self.combo_camara)
        vbox.addLayout(hbox_cam)

        # -- Botón Único de Configuración (Asistente) --
        self.btn_configurar = QPushButton("⚙️ Configurar Arnés")
        self.btn_configurar.clicked.connect(self.on_configurar_clicked.emit)
        vbox.addWidget(self.btn_configurar)

        # -- Botón Inspección --
        self.btn_run = QPushButton("▶ Iniciar Inspección")
        self.btn_run.clicked.connect(self.on_run_clicked.emit)
        vbox.addWidget(self.btn_run)

        # -- Ayuda Visual --
        vbox.addWidget(QLabel("Ayuda Visual:"))
        self.lbl_ayuda = QLabel("Sin configuración")
        self.lbl_ayuda.setMinimumSize(200, 150)
        self.lbl_ayuda.setStyleSheet("background: #222; border: 1px solid #555; color: #888;")
        self.lbl_ayuda.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_ayuda)

        # -- Consola de Logs --
        self.txt_salida = QTextEdit()
        self.txt_salida.setReadOnly(True)
        vbox.addWidget(self.txt_salida)

    # Métodos Helper
    def set_arnes_activo(self, nombre):
        self.lbl_arnes_activo.setText(f"Arnés Activo: {nombre}")
        self.lbl_arnes_activo.setStyleSheet("font-weight: bold; color: #4caf50; font-size: 14px;")

    def set_ayuda_visual(self, pixmap):
        self.lbl_ayuda.setPixmap(pixmap.scaled(self.lbl_ayuda.size(), Qt.KeepAspectRatio))

    def add_log(self, text):
        self.txt_salida.append(text)

    def bloquear_controles(self, estado):
        self.btn_seleccionar.setEnabled(not estado)
        self.btn_configurar.setEnabled(not estado)
        self.btn_run.setEnabled(not estado)