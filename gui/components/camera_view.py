# gui/components/camera_view.py
import cv2
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor

class CameraView(QLabel):
    on_shutter_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #111;")
        self.setMinimumSize(640, 480)
        
        # Estados internos del componente
        self.modo_teach = False
        self.rois_originales = []
        self.current_rect = None
        self.start_point = None
        
        self.pix_w = 0
        self.pix_h = 0
        self.orig_w = 0
        self.orig_h = 0

        # Layout de Capas (HUD)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 25)

        # Barra Superior de Instrucciones
        self.lbl_instrucciones = QLabel("")
        self.lbl_instrucciones.setAlignment(Qt.AlignCenter)
        self.lbl_instrucciones.setFixedHeight(35)
        self.lbl_instrucciones.setStyleSheet("""
            QLabel {
                background-color: rgba(33, 33, 33, 220);
                color: #ffcc00;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                border: 1px solid #555;
            }
        """)
        self.lbl_instrucciones.hide()
        self.main_layout.addWidget(self.lbl_instrucciones)

        self.main_layout.addStretch()

        # Contenedor inferior para el botón Shutter
        self.hud_container = QHBoxLayout()
        self.hud_container.setAlignment(Qt.AlignCenter)

        # Botón Shutter Circular Estilizado (Premium)
        self.btn_shutter = QPushButton()
        self.btn_shutter.setFixedSize(65, 65)
        self.btn_shutter.setCursor(Qt.PointingHandCursor)
        self._set_shutter_style_capture()
        
        self.btn_shutter.clicked.connect(self.on_shutter_clicked.emit)
        self.hud_container.addWidget(self.btn_shutter)
        self.main_layout.addLayout(self.hud_container)
        
        self.btn_shutter.hide()

    def set_instrucciones(self, texto: str):
        if texto:
            self.lbl_instrucciones.setText(texto)
            self.lbl_instrucciones.show()
        else:
            self.lbl_instrucciones.hide()

    def set_hud_visible(self, visible: bool):
        if visible:
            self.btn_shutter.show()
            self._set_shutter_style_capture()
        else:
            self.btn_shutter.hide()
            self.lbl_instrucciones.hide()

    def set_hud_modo_siguiente(self):
        """Convierte el disparador en un botón dinámico para avanzar."""
        self.btn_shutter.show()
        self.btn_shutter.setFixedSize(160, 45)
        self.btn_shutter.setText("Siguiente ➡️")
        self.btn_shutter.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 22px;
                border: 2px solid #4caf50;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)

    def _set_shutter_style_capture(self):
        """Diseño minimalista de obturador fotográfico (Estilo iOS)"""
        self.btn_shutter.setText("") # Sin texto plano molesto
        self.btn_shutter.setFixedSize(65, 65)
        self.btn_shutter.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 120);
                border-radius: 32px; /* Redondeo perfecto */
                border: 5px solid rgba(255, 255, 255, 220);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);
                border: 5px solid #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(200, 200, 200, 150);
                border: 7px solid rgba(255, 255, 255, 250);
            }
        """)

    # ─── API de Renderizado e Interacción ───
    def actualizar_frame(self, frame):
        if self.modo_teach: return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0], QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mostrar_imagen_estatica(self, img_path):
        img = cv2.imread(img_path)
        if img is None: return False
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], img_rgb.strides[0], QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return True

    def activar_teach(self, img_path):
        self.modo_teach = True
        self.rois_originales = []
        img = cv2.imread(img_path)
        if img is None: return False
        self.orig_h, self.orig_w = img.shape[:2]
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, self.orig_w, self.orig_h, img_rgb.strides[0], QImage.Format_RGB888)
        self._original_pixmap = QPixmap.fromImage(qimg)
        self.update_pixmap_scale()
        return True

    def obtener_rois(self):
        return self.rois_originales

    def update_pixmap_scale(self):
        if hasattr(self, '_original_pixmap'):
            scaled_pix = self._original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pix)
            self.pix_w = scaled_pix.width()
            self.pix_h = scaled_pix.height()

    def resizeEvent(self, event):
        if self.modo_teach: self.update_pixmap_scale()
        super().resizeEvent(event)

    def map_to_original(self, point):
        off_x = (self.width() - self.pix_w) / 2.0
        off_y = (self.height() - self.pix_h) / 2.0
        sx = max(0, min(point.x() - off_x, self.pix_w))
        sy = max(0, min(point.y() - off_y, self.pix_h))
        ratio_x = self.orig_w / self.pix_w if self.pix_w > 0 else 1
        ratio_y = self.orig_h / self.pix_h if self.pix_h > 0 else 1
        return int(sx * ratio_x), int(sy * ratio_y)

    def map_to_scaled(self, x, y):
        ratio_x = self.pix_w / self.orig_w if self.orig_w > 0 else 1
        ratio_y = self.pix_h / self.orig_h if self.orig_h > 0 else 1
        off_x = (self.width() - self.pix_w) / 2.0
        off_y = (self.height() - self.pix_h) / 2.0
        return int(x * ratio_x + off_x), int(y * ratio_y + off_y)

    def mousePressEvent(self, event):
        if self.modo_teach and event.button() == Qt.LeftButton:
            self.start_point = event.position().toPoint()
            self.current_rect = QRect(self.start_point, self.start_point)

    def mouseMoveEvent(self, event):
        if self.modo_teach and self.start_point:
            self.current_rect = QRect(self.start_point, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.modo_teach and event.button() == Qt.LeftButton and self.start_point:
            tl = self.map_to_original(self.current_rect.topLeft())
            br = self.map_to_original(self.current_rect.bottomRight())
            x, y = tl[0], tl[1]
            w, h = br[0] - tl[0], br[1] - tl[1]
            if w > 5 and h > 5:
                self.rois_originales.append((x, y, w, h))
            self.start_point = None
            self.current_rect = None
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.modo_teach: return
        painter = QPainter(self)
        pen = QPen(QColor(0, 255, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        for (x, y, w, h) in self.rois_originales:
            tl_x, tl_y = self.map_to_scaled(x, y)
            br_x, br_y = self.map_to_scaled(x + w, y + h)
            painter.drawRect(tl_x, tl_y, br_x - tl_x, br_y - tl_y)
        if self.current_rect:
            pen.setColor(QColor(255, 255, 0))
            painter.setPen(pen)
            painter.drawRect(self.current_rect)