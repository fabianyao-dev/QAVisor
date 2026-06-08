# gui/widgets.py
import cv2
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor

class ROISelectorLabel(QLabel):
    """Lienzo interactivo para dibujar cajas sobre la imagen del patrón."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #111;")
        self.setMinimumSize(640, 480)
        
        self.modo_teach = False
        self.rois_originales = []
        self.current_rect = None
        self.start_point = None
        
        self.pix_w = 0
        self.pix_h = 0
        self.orig_w = 0
        self.orig_h = 0

    def activar_teach(self, img_path):
        self.modo_teach = True
        self.rois_originales = []
        
        img = cv2.imread(img_path)
        if img is None:
            return False
            
        self.orig_h, self.orig_w = img.shape[:2]
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, self.orig_w, self.orig_h, img_rgb.strides[0], QImage.Format_RGB888)
        self._original_pixmap = QPixmap.fromImage(qimg)
        self.update_pixmap_scale()
        return True

    def update_pixmap_scale(self):
        if hasattr(self, '_original_pixmap'):
            scaled_pix = self._original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pix)
            self.pix_w = scaled_pix.width()
            self.pix_h = scaled_pix.height()

    def resizeEvent(self, event):
        if self.modo_teach:
            self.update_pixmap_scale()
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