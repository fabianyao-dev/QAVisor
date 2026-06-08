    # services/arnes_service.py
from db.arnes_repo import crear_arnes, get_arnes, get_todos_arnes

class ArnesService:
    def obtener_o_crear(self, numero_parte, descripcion=""):
        if not numero_parte or not numero_parte.strip():
            raise ValueError("El número de parte no puede estar vacío.")
        
        arnes = get_arnes(numero_parte)
        if not arnes:
            arnes = crear_arnes(numero_parte, descripcion)
        return arnes

    def obtener_todos(self):
        return get_todos_arnes()

    # Nota: Aquí en el futuro puedes agregar eliminar_arnes o actualizar_descripcion
    # cuando agreguemos esos queries a tu arnes_repo.py