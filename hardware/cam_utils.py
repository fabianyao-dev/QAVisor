import cv2


def detectar_camaras(max_idx=6):
    """
    Escanea índices y regresa lista de (índice, backend) disponibles.
    Prueba CAP_DSHOW, CAP_MSMF y CAP_ANY en orden.
    """
    encontradas = []

    for i in range(max_idx):
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                cap = cv2.VideoCapture(i, backend)
                if cap.isOpened():
                    encontradas.append((i, backend))
                    cap.release()
                    break
            except Exception:
                pass

    return encontradas


def seleccionar_camara(camaras):
    """
    Si hay una sola cámara, la regresa directo.
    Si hay varias, regresa la primera (la GUI maneja la selección).
    Regresa (cam_id, backend).
    """
    if not camaras:
        raise RuntimeError("No se encontró ninguna cámara conectada.")

    return camaras[0]