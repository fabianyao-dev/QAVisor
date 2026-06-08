from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QLineEdit, QPushButton, QMessageBox, QWidget
)
from services.arnes_service import ArnesService

class ArnesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar o Crear Arnés")
        self.setMinimumWidth(350)
        
        self.arnes_service = ArnesService()
        self.arnes_seleccionado = None

        self.layout = QVBoxLayout(self)

        # ── 1. Selector ──
        self.layout.addWidget(QLabel("Selecciona un Arnés activo:"))
        self.combo = QComboBox()
        self.cargar_arneses()
        self.layout.addWidget(self.combo)

        # Botón toggle
        self.btn_toggle_crear = QPushButton("➕ Registrar Nuevo Arnés")
        self.btn_toggle_crear.clicked.connect(self.toggle_crear_form)
        self.layout.addWidget(self.btn_toggle_crear)

        # ── 2. Contenedor de Crear ──
        self.crear_widget = QWidget()
        crear_layout = QVBoxLayout(self.crear_widget)
        crear_layout.setContentsMargins(0, 10, 0, 0)
        
        self.input_np = QLineEdit()
        self.input_np.setPlaceholderText("Número de Parte (Ej. ARN-001)")
        crear_layout.addWidget(self.input_np)
        
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descripción (Opcional)")
        crear_layout.addWidget(self.input_desc)

        self.btn_crear = QPushButton("Guardar y Seleccionar")
        self.btn_crear.setStyleSheet("background-color: #2e7d32; color: white;")
        self.btn_crear.clicked.connect(self.crear_arnes)
        crear_layout.addWidget(self.btn_crear)
        
        self.crear_widget.setVisible(False)
        self.layout.addWidget(self.crear_widget)

        # ── 3. Botones finales ──
        self.layout.addSpacing(15)
        btn_layout = QHBoxLayout()
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_cancelar = QPushButton("Cancelar")
        
        self.btn_aceptar.clicked.connect(self.aceptar)
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_aceptar)
        btn_layout.addWidget(self.btn_cancelar)
        self.layout.addLayout(btn_layout)

    def toggle_crear_form(self):
        """Muestra/oculta y ajusta el tamaño de la ventana inmediatamente."""
        is_visible = not self.crear_widget.isVisible()
        self.crear_widget.setVisible(is_visible)
        
        if is_visible:
            self.btn_toggle_crear.setText("➖ Cancelar Nuevo Arnés")
        else:
            self.btn_toggle_crear.setText("➕ Registrar Nuevo Arnés")
            # Limpiamos campos al cancelar
            self.input_np.clear()
            self.input_desc.clear()
        
        # Ajuste dinámico de altura
        self.adjustSize()

    def cargar_arneses(self):
        self.combo.clear()
        arneses = self.arnes_service.obtener_todos()
        if arneses:
            for arnes in arneses:
                self.combo.addItem(f"{arnes['numero_parte']} - {arnes['descripcion']}", arnes['numero_parte'])
        else:
            self.combo.addItem("No hay arneses registrados", None)

    def crear_arnes(self):
        np = self.input_np.text().strip()
        desc = self.input_desc.text().strip()
        if not np:
            QMessageBox.warning(self, "Atención", "El número de parte es obligatorio.")
            return
        try:
            self.arnes_service.obtener_o_crear(np, desc)
            self.cargar_arneses()
            
            # Seleccionar el nuevo
            index = self.combo.findData(np)
            if index >= 0:
                self.combo.setCurrentIndex(index)
            
            # Cerrar el formulario y limpiar
            self.toggle_crear_form() 
            QMessageBox.information(self, "Éxito", f"Arnés {np} registrado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear: {str(e)}")

    def aceptar(self):
        data = self.combo.currentData()
        if data:
            self.arnes_seleccionado = data
            self.accept()
        else:
            QMessageBox.warning(self, "Atención", "Selecciona un arnés válido.")