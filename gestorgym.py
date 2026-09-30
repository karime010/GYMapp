import bcrypt
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os


def main():
    print("Hello from practica1!")


class GestorGYM:

    def __init__(self, uri: str = 'mongodb+srv://karimeDB:cruzsilvaari091217@clusterkarimecruz.eb4k36a.mongodb.net/?appName=ClusterKarimeCruz'):

        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')

            self.db = self.cliente['gestor_labiales']

            self.labiales = self.db['labiales']
            self.usuarios = self.db['usuarios']

            # Crear índices necesarios
            self._crear_indices()

            print("✅ Conectado a MongoDB")

        except ConnectionFailure:
            print("❌ Error: No se pudo conectar a MongoDB")
            raise

    def _crear_indices(self):

        self.usuarios.create_index("email", unique=True)
        self.labiales.create_index([("usuario_id", 1), ("fecha_registro", -1)])
        self.labiales.create_index("color")

    def crear_usuario(self, nombre: str, email: str, password: str) -> Optional[str]:

        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")
        
            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password_hash,
                "fecha_registro": datetime.now(),
                "activo": True
            })

            return str(resultado.inserted_id)

        except DuplicateKeyError:

            print(f"❌ Error: El email {email} ya está registrado")
            return None

    def obtener_usuario(self, usuario_id: str) -> Optional[Dict]:

        try:

            usuario = self.usuarios.find_one({
                "_id": ObjectId(usuario_id)
            })

            if usuario:
                usuario['_id'] = str(usuario['_id'])

            return usuario

        except Exception as e:

            print(f"Error al obtener usuario: {e}")
            return None

    def agregar_labial(self, usuario_id: str,
                        nombre: str,
                        descripcion:str,
                        color: str,
                        precio: float,
                        imagen: str) -> Optional[str]:
        

        if not self.obtener_usuario(usuario_id):

            print(f"❌ Error: Usuario {usuario_id} no existe")
            return None

        labial = {

            "usuario_id": ObjectId(usuario_id),
            "nombre": nombre,
            "descripcion": descripcion,
            "color": color,
            "precio": precio,
            "imagen": imagen,
            "stock": 10,
            "vendido": False,
            "fecha_registro": datetime.now()
        }  

        resultado = self.labiales.insert_one(labial)

        return str(resultado.inserted_id)

    def obtener_labiales_usuario(self,
                                usuario_id: str) -> List[Dict]:

        filtro = {"usuario_id": ObjectId(usuario_id)}

        labiales = self.labiales.find(filtro).sort(
            "fecha_registro", -1
        )

        resultado = []

        for l in labiales:

            l['_id'] = str(l['_id'])
            l['usuario_id'] = str(l['usuario_id'])

            resultado.append(l)

        return resultado

    def vender_labial(self,
                    labial_id: str,
                    cantidad: int = 1) -> bool:

        resultado = self.labiales.update_one(

            {"_id": ObjectId(labial_id)},

            {
                "$inc": {"stock": -cantidad},

                "$set": {
                    "vendido": True,
                    "fecha_venta": datetime.now()
                }
            }
        )

        return resultado.modified_count > 0

    def eliminar_labial(self, labial_id: str) -> bool:

        resultado = self.labiales.delete_one({
            "_id": ObjectId(labial_id)
        })

        return resultado.deleted_count > 0

    def actualizar_labial(self, labial_id: str, nombre: str, descripcion: str, color: str, precio: float, imagen: str) -> bool:
        resultado = self.labiales.update_one(
        {"_id": ObjectId(labial_id)},
        {
            "$set": {
                "nombre": nombre,
                "descripcion": descripcion,
                "color": color,
                "precio": precio,
                "imagen": imagen
            }
        }
    )
        return resultado.modified_count > 0
    def buscar_labiales(self, texto: str) -> List[Dict]:

        labiales = self.labiales.find({
            "$text": {"$search": texto}
        })

        resultado = []

        for l in labiales:

            l['_id'] = str(l['_id'])
            l['usuario_id'] = str(l['usuario_id'])

            resultado.append(l)

        return resultado

    def cerrar_conexion(self):

        if self.cliente:

            self.cliente.close()

            print("🔌 Conexión cerrada")


# Ejemplo de uso
def ejemplo_uso():

    gestor = GestorLabiales()

    usuario_id = gestor.crear_usuario(
        "mitzy",
        "24308060610657@cetis61.edu.mx",
        "1234"
    )

    print(f"Usuario creado con ID: {usuario_id}")

    if usuario_id:

        labial1 = gestor.agregar_labial(
            usuario_id,
            "Labial Rojo",
            "Rojo intenso",
            15.99
        )

        print(f"Labial creado: {labial1}")

        labiales = gestor.obtener_labiales_usuario(
            usuario_id
        )

        print(f"\nLabiales de {usuario_id}:")

        for l in labiales:

            print(
                f" - {l['nombre']} | "
                f"{l['color']} | "
                f"${l['precio']} | "
                f"Stock: {l['stock']}"
            )

        vendido = gestor.vender_labial(
            labial1,
            2
        )

        print(f"\nVenta realizada: {vendido}")

    gestor.cerrar_conexion()

if __name__ == "__main__":
    ejemplo_uso()



if __name__ == "__main__":
    main()