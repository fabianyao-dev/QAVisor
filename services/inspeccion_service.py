import cv2
import numpy as np
# Importamos la función para obtener la configuración activa desde la BD
from db.config_repo import get_configuracion_activa 

class InspeccionService:
    def __init__(self, numero_parte):
        # Cargamos la configuración directamente de la BD al iniciar
        config = get_configuracion_activa(numero_parte)
        
        if config and config.get("rois"):
            # 'rois' es el JSON que guardamos en BD
            self.model = config["rois"] 
        else:
            self.model = []
            
        # Tolerancias industriales
        self.roi_pieza = [500, 315, 40, 40]
        self.tolerancia_color = 25
        self.umbral_cable = 200
        self.ratio_cable = 0.10

    @staticmethod
    def color_dist(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    def hay_cable(self, roi_bgr):
        gray  = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        mask  = gray < self.umbral_cable
        ratio = mask.mean()
        return ratio > self.ratio_cable

    def analizar_frame(self, img):
        if not self.model:
            return img, False

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        ok_global = True

        for i, via in enumerate(self.model):
            x, y, w, h = via["roi"]
            roi_bgr    = img[y:y+h, x:x+w]
            
            # Convertimos la lista de vuelta a array si es necesario
            hsv_target = np.array(via.get("hsv", [0, 0, 0])) 

            if roi_bgr.size == 0: continue

            detected = self.hay_cable(roi_bgr)
            ok_via   = True

            # Lógica: Si requiere cable y no detecta, FAIL. 
            # Si tiene hsv y detecta, comparamos color.
            if via["required"]:
                if not detected:
                    ok_via = False
                elif "hsv" in via:
                    roi_hsv = hsv[y:y+h, x:x+w]
                    mean = roi_hsv.reshape(-1, 3).mean(axis=0)
                    if self.color_dist(mean, hsv_target) > self.tolerancia_color:
                        ok_via = False

            if not ok_via: ok_global = False

            color = (0, 255, 0) if ok_via else (0, 0, 255)
            cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
            cv2.putText(img, str(i+1), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return img, ok_global