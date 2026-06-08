# gui/app.py
import sys
import cv2
import os

from PySide6.QtWidgets import QDialog, QGridLayout, QMessageBox, QHBoxLayout, QLabel, QWidget, QPushButton
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QIcon, QPixmap, QKeyEvent

from hardware.cam_utils import detectar_camaras
from gui.workers import Worker
from gui.components.arnes_gui import ArnesDialog
from services.config_service import ConfigService

# --- Componentes UI ---
from gui.components.camera_view import CameraView
from gui.components.control_panel import ControlPanel
from gui.components.settings_dialog import SettingsDialog


class App:
    def __init__(self):
        # 1. Estados del Sistema y Contadores
        self.arnes_activo = None
        self.estado_config = "INICIAL" 
        self.config_service = ConfigService()
        self.thread = None
        self.worker = None
        
        self.contador_ok = 0
        self.contador_fail = 0

        # 2. Inicializar Hardware
        self.camaras = detectar_camaras()
        if not self.camaras:
            self.camaras = [(-1, cv2.CAP_ANY)]
        self.cam_id, self.backend = self.camaras[0]

        # 3. Construir la Ventana Principal
        self.window = QDialog()
        self.window.setWindowTitle("QAVisor - Inspección de Conectores")
        self.window.resize(1122, 849)

        # ─── MOTOR DE RUTAS OFICIAL PARA PYINSTALLER 6+ (LOGO) ───
        def obtener_ruta_recurso(nombre_archivo):
            if hasattr(sys, '_MEIPASS'):
                # En el .exe, PyInstaller guarda los archivos en la carpeta _internal (sys._MEIPASS)
                return os.path.join(sys._MEIPASS, nombre_archivo)
            else:
                # En desarrollo (VS Code), subimos un nivel desde gui/app.py a la raíz
                raiz_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                return os.path.join(raiz_proyecto, nombre_archivo)

        ruta_logo = obtener_ruta_recurso("logo.ico")

        if os.path.exists(ruta_logo):
            self.window.setWindowIcon(QIcon(ruta_logo))
        # ─────────────────────────────────────────────────────────

        # Inyectar el manejador de cierre de la ventana de Qt
        self.window.closeEvent = self.handle_close_window

        main_grid = QGridLayout(self.window)
        main_grid.setColumnStretch(0, 3)
        main_grid.setColumnStretch(1, 1)

        # ─── BARRA SUPERIOR DE CONTADORES Y RED ───
        self.stats_widget = QWidget()
        self.stats_widget.setStyleSheet("background-color: #1a1a1a; border-bottom: 2px solid #333;")
        stats_layout = QHBoxLayout(self.stats_widget)
        stats_layout.setContentsMargins(15, 5, 15, 5)

        self.lbl_counter_ok = QLabel("PIEZAS OK: 0")
        self.lbl_counter_ok.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 16px;")
        stats_layout.addWidget(self.lbl_counter_ok)
        
        stats_layout.addStretch()
        
        # Botón de Ajustes de Red
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Conexiones de Red")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                font-size: 14px;
                border-radius: 4px;
                border: 1px solid #555;
            }
            QPushButton:hover {
                background-color: #444;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)
        self.btn_settings.clicked.connect(self.handle_abrir_ajustes)
        stats_layout.addWidget(self.btn_settings)
        
        main_grid.addWidget(self.stats_widget, 0, 0)

        # Visor de la Cámara
        self.camera_view = CameraView()
        main_grid.addWidget(self.camera_view, 1, 0)

        # Panel de Control Lateral
        self.control_panel = ControlPanel(self.camaras)
        main_grid.addWidget(self.control_panel, 0, 1, 2, 1)

        # Filtro de eventos de teclado
        self.window.keyPressEvent = self.handle_key_press

        # Conectar Callbacks
        self.control_panel.on_seleccionar_arnes_clicked.connect(self.handle_seleccionar_arnes)
        self.control_panel.on_configurar_clicked.connect(self.handle_configurar) 
        self.control_panel.on_run_clicked.connect(self.handle_toggle_inspeccion)
        self.control_panel.on_camara_changed.connect(self.handle_cambiar_camara)
        self.camera_view.on_shutter_clicked.connect(self.handle_hud_action)

        self.control_panel.add_log("Sistema iniciado.")
        self.window.show()

    # ─────────────────────────────────────────
    #  Flujo del Asistente Unificado
    # ─────────────────────────────────────────
    def handle_configurar(self):
        if not self.arnes_activo:
            QMessageBox.warning(self.window, "Atención", "Selecciona un arnés primero.")
            return

        if self.estado_config == "INICIAL":
            self.lanzar_worker("captura")
            self.camera_view.set_hud_visible(True)
            self.camera_view.set_instrucciones("PASO 1: Centre el conector y presione ENTER o el botón central para capturar el patrón.")
            
            self.control_panel.btn_configurar.setText("❌ Cancelar Configuración")
            self.control_panel.btn_configurar.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold;")
            self.estado_config = "FOTO_TOMADA"
        else:
            if self.worker and self.worker.modo == "captura":
                self.worker.command = "stop"
            
            self.eliminar_archivos_temporales()
            self.finalizar_asistente_contexto("❌ Configuración cancelada por el usuario. Temporales eliminados.")

    def handle_hud_action(self):
        if self.estado_config == "FOTO_TOMADA":
            if self.worker:
                self.worker.command = "save"
                self.control_panel.add_log("Capturando imagen patrón...")
                
        elif self.estado_config == "DIBUJANDO":
            rois = self.camera_view.obtener_rois()
            if not rois:
                self.control_panel.add_log("⚠️ Error: No dibujaste cajas.")
                return
                
            modelo = [{"roi": r, "required": True} for r in rois]
            self.config_service.procesar_y_guardar_modelo(self.arnes_activo, modelo, "patron.jpg")
            
            self.eliminar_archivos_temporales()
            self.finalizar_asistente_contexto("✅ Configuración guardada exitosamente en BD. Temporales limpios.")

    def eliminar_archivos_temporales(self):
        archivos = ["patron.jpg", "temp_patron.jpg"]
        for archivo in archivos:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                except Exception as e:
                    self.control_panel.add_log(f"Aviso: No se pudo borrar {archivo}: {str(e)}")

    def finalizar_asistente_contexto(self, log_msg):
        self.estado_config = "INICIAL"
        self.camera_view.modo_teach = False
        self.camera_view.set_hud_visible(False)
        
        self.control_panel.btn_configurar.setText("⚙️ Configurar Arnés")
        self.control_panel.btn_configurar.setStyleSheet("")
        self.control_panel.btn_configurar.setEnabled(True)
        
        ruta_img = self.config_service.obtener_foto_patron(self.arnes_activo)
        if ruta_img:
            self.control_panel.set_ayuda_visual(QPixmap(ruta_img))
        else:
            self.control_panel.lbl_ayuda.clear()
            self.control_panel.lbl_ayuda.setText("Sin configuración")
            
        self.control_panel.add_log(log_msg)

    def handle_key_press(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.estado_config in ("FOTO_TOMADA", "DIBUJANDO") and self.camera_view.btn_shutter.isVisible():
                self.handle_hud_action()
        elif event.key() == Qt.Key_Escape:
            if self.estado_config != "INICIAL":
                self.handle_configurar()
        else:
            QDialog.keyPressEvent(self.window, event)

    def handle_close_window(self, event):
        if self.worker:
            self.worker.command = "stop"
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
            
        self.eliminar_archivos_temporales()
        event.accept()

    def handle_toggle_inspeccion(self):
        if self.worker and self.worker.modo == "run":
            self.worker.command = "stop"
            self.control_panel.add_log("Deteniendo inspección de línea...")
        else:
            self.contador_ok = 0
            self.contador_fail = 0
            self.lbl_counter_ok.setText("PIEZAS OK: 0") 
            
            self.lanzar_worker("run")
            self.control_panel.btn_run.setText("🛑 Detener Inspección")
            self.control_panel.btn_run.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold;")

    def lanzar_worker(self, modo):
        if not self.arnes_activo and modo == "run": return
        
        self.thread = QThread()
        self.worker = Worker(modo, self.cam_id, self.backend, self.arnes_activo)

        self.control_panel.bloquear_controles(True)
        if modo == "run":
            self.control_panel.btn_run.setEnabled(True)
        elif modo == "captura":
            self.control_panel.btn_configurar.setEnabled(True)

        self.worker.frameReady.connect(self.camera_view.actualizar_frame)
        self.worker.piezaOk.connect(self.registrar_pieza_ok)
        self.worker.finished.connect(self.worker_finalizado)
        
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def worker_finalizado(self, data):
        self.worker = None
        self.thread.quit()
        self.control_panel.bloquear_controles(False)
        
        self.control_panel.btn_run.setText("▶ Iniciar Inspección")
        self.control_panel.btn_run.setStyleSheet("")

        if data == "captura" and self.estado_config == "FOTO_TOMADA":
            self.camera_view.mostrar_imagen_estatica("patron.jpg")
            if self.camera_view.activar_teach("patron.jpg"):
                self.camera_view.set_hud_modo_siguiente()
                self.camera_view.set_instrucciones("PASO 2: Dibuje las cavidades arrastrando el mouse. Al terminar pulse 'Siguiente'.")
                self.estado_config = "DIBUJANDO"

    def handle_seleccionar_arnes(self):
        dialogo = ArnesDialog(self.window)
        if dialogo.exec():
            self.arnes_activo = dialogo.arnes_seleccionado
            self.control_panel.set_arnes_activo(self.arnes_activo)
            ruta_img = self.config_service.obtener_foto_patron(self.arnes_activo)
            if ruta_img: 
                self.control_panel.set_ayuda_visual(QPixmap(ruta_img))

    def handle_cambiar_camara(self, idx):
        if 0 <= idx < len(self.camaras):
            self.cam_id, self.backend = self.camaras[idx]

    def handle_abrir_ajustes(self):
        dialogo = SettingsDialog(self.window)
        dialogo.exec()

    def registrar_pieza_ok(self):
        self.contador_ok += 1
        self.lbl_counter_ok.setText(f"PIEZAS OK: {self.contador_ok}")
        self.control_panel.add_log("🟢 ¡Pieza OK!")
        
        import winsound
        try: 
            winsound.Beep(2000, 200)
        except Exception: 
            pass