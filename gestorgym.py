import bcrypt
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv


load_dotenv()


class GestorGYM:

    def __init__(self):

        try:
            uri = os.getenv("MONGO_URI")

            self.cliente = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )

            self.cliente.admin.command("ping")

            self.db = self.cliente["gestorgym"]

            # Colecciones
            self.usuarios = self.db["usuarios"]
            self.evaluaciones = self.db["evaluaciones"]
            self.rutinas = self.db["rutinas"]
            self.progreso = self.db["progreso"]
            self.nutricion = self.db["nutricion"]

            self._crear_indices()

            print("✅ Conectado a MongoDB")

        except ConnectionFailure:
            print("❌ Error: No se pudo conectar a MongoDB")
            raise

    # ==========================================================
    # ÍNDICES
    # ==========================================================

    def _crear_indices(self):

        self.usuarios.create_index(
            "email",
            unique=True
        )

        self.evaluaciones.create_index(
            "usuario_id",
            unique=True
        )

        self.progreso.create_index(
            [
                ("usuario_id", 1),
                ("fecha", -1)
            ]
        )

    # ==========================================================
    # USUARIOS
    # ==========================================================

    def crear_usuario(
        self,
        nombre: str,
        email: str,
        password: str
    ) -> Optional[str]:

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

            print(
                f"❌ El email {email} ya está registrado"
            )

            return None

    def obtener_usuario(
        self,
        usuario_id: str
    ) -> Optional[Dict]:

        try:

            usuario = self.usuarios.find_one({
                "_id": ObjectId(usuario_id)
            })

            if usuario:

                usuario["_id"] = str(
                    usuario["_id"]
                )

            return usuario

        except Exception as e:

            print(
                f"❌ Error al obtener usuario: {e}"
            )

            return None

    def actualizar_foto(self, usuario_id: str, foto: str) -> bool:

        try:

            resultado = self.usuarios.update_one(

                {
                    "_id": ObjectId(usuario_id)
                },

                {
                    "$set": {
                        "foto": foto
                    }
                }
            )

            return resultado.matched_count > 0

        except Exception as e:

            print(f"❌ Error al actualizar foto: {e}")

            return False    

    def iniciar_sesion(
        self,
        email: str,
        password: str
    ) -> Optional[str]:

        usuario = self.usuarios.find_one({
            "email": email
        })

        if not usuario:

            return None

        password_correcta = bcrypt.checkpw(
            password.encode("utf-8"),
            usuario["password"].encode("utf-8")
        )

        if password_correcta:

            return str(usuario["_id"])

        return None

    # ==========================================================
    # EVALUACIÓN
    # ==========================================================

    def guardar_evaluacion(
        self,
        usuario_id: str,
        edad: int,
        peso: float,
        altura: float,
        tipo_cuerpo: str,
        objetivo: str,
        dias_entrenamiento: int
    ) -> Optional[str]:

        try:

            evaluacion = {

                "usuario_id": ObjectId(usuario_id),
                "edad": edad,
                "peso": peso,
                "altura": altura,
                "tipo_cuerpo": tipo_cuerpo,
                "objetivo": objetivo,
                "dias_entrenamiento": dias_entrenamiento,
                "fecha": datetime.now()

            }

            resultado = self.evaluaciones.update_one(

                {
                    "usuario_id": ObjectId(usuario_id)
                },

                {
                    "$set": evaluacion
                },

                upsert=True
            )

            if resultado.upserted_id:

                return str(resultado.upserted_id)

            evaluacion_guardada = self.evaluaciones.find_one({
                "usuario_id": ObjectId(usuario_id)
            })

            if evaluacion_guardada:

                return str(
                    evaluacion_guardada["_id"]
                )

            return None

        except Exception as e:

            print(
                f"❌ Error al guardar evaluación: {e}"
            )

            return None

    def obtener_evaluacion(
        self,
        usuario_id: str
    ) -> Optional[Dict]:

        evaluacion = self.evaluaciones.find_one({
            "usuario_id": ObjectId(usuario_id)
        })

        if evaluacion:

            evaluacion["_id"] = str(
                evaluacion["_id"]
            )

            evaluacion["usuario_id"] = str(
                evaluacion["usuario_id"]
            )

        return evaluacion

    # ==========================================================
    # RUTINAS
    # ==========================================================

    def crear_rutina(
        self,
        nombre: str,
        objetivo: str,
        dias: int,
        tipo_cuerpo: str,
        ejercicios: List[str]
    ) -> Optional[str]:

        try:

            rutina = {

                "nombre": nombre,
                "objetivo": objetivo,
                "dias": dias,
                "tipo_cuerpo": tipo_cuerpo,
                "ejercicios": ejercicios,
                "fecha_registro": datetime.now()

            }

            resultado = self.rutinas.insert_one(
                rutina
            )

            return str(
                resultado.inserted_id
            )

        except Exception as e:

            print(
                f"❌ Error al crear rutina: {e}"
            )

            return None

    def obtener_rutinas_recomendadas(
        self,
        usuario_id: str
    ) -> List[Dict]:

        evaluacion = self.obtener_evaluacion(
            usuario_id
        )

        if not evaluacion:

            return []

        filtro = {

            "objetivo": evaluacion["objetivo"],
            "dias": evaluacion["dias_entrenamiento"]

        }

        rutinas = self.rutinas.find(filtro)

        resultado = []

        for rutina in rutinas:

            rutina["_id"] = str(
                rutina["_id"]
            )

            resultado.append(rutina)

        return resultado

    def obtener_rutinas(self) -> List[Dict]:

        rutinas = self.rutinas.find()

        resultado = []

        for rutina in rutinas:

            rutina["_id"] = str(
                rutina["_id"]
            )

            resultado.append(rutina)

        return resultado

    def obtener_rutina(
        self,
        rutina_id: str
    ) -> Optional[Dict]:

        rutina = self.rutinas.find_one({
            "_id": ObjectId(rutina_id)
        })

        if rutina:

            rutina["_id"] = str(
                rutina["_id"]
            )

        return rutina

    # ==========================================================
    # RUTINA ELEGIDA POR EL USUARIO
    # ==========================================================

    def guardar_rutina_usuario(
        self,
        usuario_id: str,
        rutina_id: str
    ) -> bool:

        try:

            resultado = self.usuarios.update_one(

                {
                    "_id": ObjectId(usuario_id)
                },

                {
                    "$set": {
                        "rutina_seleccionada":
                            ObjectId(rutina_id)
                    }
                }
            )

            return resultado.modified_count > 0

        except Exception as e:

            print(
                f"❌ Error al guardar rutina: {e}"
            )

            return False

    def obtener_rutina_usuario(
        self,
        usuario_id: str
    ) -> Optional[Dict]:

        usuario = self.usuarios.find_one({
            "_id": ObjectId(usuario_id)
        })

        if not usuario:

            return None

        rutina_id = usuario.get(
            "rutina_seleccionada"
        )

        if not rutina_id:

            return None

        return self.obtener_rutina(
            str(rutina_id)
        )

    # ==========================================================
    # PROGRESO
    # ==========================================================

    def guardar_progreso(
        self,
        usuario_id: str,
        peso: float
    ) -> Optional[str]:

        try:

            progreso = {

                "usuario_id":
                    ObjectId(usuario_id),

                "peso": peso,

                "fecha":
                    datetime.now()

            }

            resultado = self.progreso.insert_one(
                progreso
            )

            return str(
                resultado.inserted_id
            )

        except Exception as e:

            print(
                f"❌ Error al guardar progreso: {e}"
            )

            return None

    def obtener_progreso(
        self,
        usuario_id: str
    ) -> List[Dict]:

        registros = self.progreso.find({

            "usuario_id":
                ObjectId(usuario_id)

        }).sort(
            "fecha",
            -1
        )

        resultado = []

        for registro in registros:

            registro["_id"] = str(
                registro["_id"]
            )

            registro["usuario_id"] = str(
                registro["usuario_id"]
            )

            resultado.append(
                registro
            )

        return resultado

    # ==========================================================
    # IMC
    # ==========================================================

    def calcular_imc(
        self,
        peso: float,
        altura: float
    ) -> float:

        imc = peso / (altura ** 2)

        return round(imc, 2)

    # ==========================================================
    # NUTRICIÓN
    # ==========================================================

    def guardar_recomendacion_nutricion(
        self,
        objetivo: str,
        recomendacion: str
    ) -> Optional[str]:

        try:

            resultado = self.nutricion.insert_one({

                "objetivo": objetivo,
                "recomendacion": recomendacion

            })

            return str(
                resultado.inserted_id
            )

        except Exception as e:

            print(
                f"❌ Error al guardar nutrición: {e}"
            )

            return None

    def obtener_recomendaciones_nutricion(
        self,
        objetivo: str
    ) -> List[Dict]:

        recomendaciones = self.nutricion.find({
            "objetivo": objetivo
        })

        resultado = []

        for recomendacion in recomendaciones:

            recomendacion["_id"] = str(
                recomendacion["_id"]
            )

            resultado.append(
                recomendacion
            )

        return resultado

    # ==========================================================
    # CERRAR CONEXIÓN
    # ==========================================================

    def cerrar_conexion(self):

        if self.cliente:

            self.cliente.close()

            print("🔌 Conexión cerrada")