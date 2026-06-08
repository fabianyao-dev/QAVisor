# services/config_service.py
import cv2
import numpy as np
import json
from db.config_repo import guardar_configuracion, get_configuracion_activa, get_patron_activo

class ConfigService:
    def procesar_y_guardar_modelo(self, numero_parte, modelo_rois, img_patron_path="patron.jpg"):
        """
        Calcula los valores HSV y guarda la configuración completa en BD.
        """
        if not modelo_rois:
            raise ValueError("No se puede guardar un modelo sin vías (ROIs).")

        img = cv2.imread(img_patron_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo abrir la imagen: {img_patron_path}")

        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        modelo_final = []

        for entry in modelo_rois:
            x, y, w, h = entry["roi"]
            new_entry = {"roi": entry["roi"], "required": entry["required"]}

            # Cálculo de HSV para las vías que requieren cable
            if entry["required"]:
                roi_hsv = hsv_img[y:y+h, x:x+w]
                if roi_hsv.size == 0:
                    raise ValueError("Error: Una vía está fuera de los límites de la imagen.")
                
                mean = roi_hsv.reshape(-1, 3).mean(axis=0)
                new_entry["hsv"] = mean.tolist()

            modelo_final.append(new_entry)

        # Leemos el binario de la imagen para guardarlo en la columna BYTEA
        try:
            with open(img_patron_path, "rb") as f:
                img_binary = f.read()
        except Exception as e:
            raise IOError(f"No se pudo leer el archivo de imagen para guardar: {e}")

        # Guardar en BD
        nuevo_id = guardar_configuracion(numero_parte, modelo_final, img_binary)
        return nuevo_id

    def obtener_activa(self, numero_parte):
        return get_configuracion_activa(numero_parte)
    
    def obtener_foto_patron(self, numero_parte):
        """
        Recupera el binario de la BD y lo guarda temporalmente para mostrarlo.
        """
        datos_binarios = get_patron_activo(numero_parte)
        if datos_binarios:
            ruta_temp = "temp_patron.jpg"
            with open(ruta_temp, "wb") as f:
                f.write(datos_binarios)
            return ruta_temp
        return None