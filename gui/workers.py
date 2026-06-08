# gui/components/workers.py
import time
from PySide6.QtCore import QObject, Signal
from hardware.video_stream import iniciar_stream
from services.inspeccion_service import InspeccionService 

class Worker(QObject):
    finished   = Signal(object)
    frameReady = Signal(object)
    piezaOk    = Signal() 

    def __init__(self, modo, cam_id, backend, arnes_activo=None):
        super().__init__()
        self.modo = modo
        self.cam_id = cam_id
        self.backend = backend
        self.arnes_activo = arnes_activo 
        self.command = None

    def update_frame_cb(self, frame):
        self.frameReady.emit(frame)
        cmd = self.command
        self.command = None
        return cmd

    def run(self):
        try:
            if self.modo == "captura":
                iniciar_stream(self.update_frame_cb,
                               cam_id=self.cam_id,
                               backend=self.backend,
                               output_path="patron.jpg")
                self.finished.emit("captura")

            elif self.modo == "run":
                self._correr_inspeccion()
                self.finished.emit("run")

        except Exception as e:
            self.finished.emit("error: " + str(e))

    def _correr_inspeccion(self):
        """
        Inyecta la lógica de inspección con un Debounce de tiempo 
        para evitar lecturas duplicadas de una misma pieza.
        """
        inspeccion_service = InspeccionService(self.arnes_activo) 
        self.ok_anterior = False
        
        # ─── MÁQUINA DE ESTADOS DE TIEMPO (DEBOUNCE) ───
        self.ultimo_tiempo_ok = 0  # Almacena el timestamp del último OK válido
        self.tiempo_bloqueo = 2.0  # Ventana de espera en segundos

        def procesar_frame(frame):
            # 1. El servicio analiza y dibuja los ROIs
            frame_pintado, ok_global = inspeccion_service.analizar_frame(frame)
            
            tiempo_actual = time.time()

            # 2. Lógica de conteo con filtro de tiempo de 2 segundos
            if ok_global and not self.ok_anterior:
                # Calculamos cuánto tiempo ha pasado desde el último pitido/registro exitoso
                tiempo_transcurrido = tiempo_actual - self.ultimo_tiempo_ok
                
                if tiempo_transcurrido >= self.tiempo_bloqueo:
                    self.piezaOk.emit()          # Dispara contador y Beep en app.py
                    self.ultimo_tiempo_ok = tiempo_actual  # Bloquea el reloj desde este instante
                else:
                    # Opcional: Escribe en la consola de debug si está ignorando ráfagas
                    pass
            
            self.ok_anterior = ok_global

            # 3. Mostrar frame pintado en la UI
            self.frameReady.emit(frame_pintado)

            # 4. Escuchar comandos de la UI (como 'stop')
            cmd = self.command
            self.command = None
            return cmd

        # Arranca el stream de video infinito pasándole el callback inteligente
        iniciar_stream(procesar_frame, cam_id=self.cam_id, backend=self.backend)