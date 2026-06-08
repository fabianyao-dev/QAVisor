# hardware/video_stream.py
import cv2
from hardware.cam_utils import detectar_camaras, seleccionar_camara

def iniciar_stream(update_frame_cb, cam_id=None, backend=None, output_path="captura.jpg"):
    """
    Inicia la captura de video y envía cada frame al callback.
    Permite guardar un frame si el callback devuelve 'save'.
    """
    if cam_id is None:
        camaras = detectar_camaras()
        cam_id, backend = seleccionar_camara(camaras)

    cap = cv2.VideoCapture(cam_id, backend)

    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara (índice {cam_id})")

    guardado = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        seguir = update_frame_cb(frame)

        if seguir == "save":
            cv2.imwrite(output_path, frame)
            guardado = True
            break

        if seguir == "stop":
            break

    cap.release()

    return output_path if guardado else None