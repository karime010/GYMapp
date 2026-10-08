from flask import Flask, render_template, request, redirect, url_for, flash, session 
from gestorgym import GestorGYM 
import bcrypt

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"

gestor = GestorGYM()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        usuario = gestor.usuarios.find_one({"email": email})

        if not usuario:
            return render_template("login.html", error="Usuario no encontrado")

        if "password" not in usuario:
            return render_template("login.html", error="Usuario no tiene contraseña")

        if bcrypt.checkpw(
            password.encode("utf-8"),
            usuario["password"].encode("utf-8")
        ):
            session["usuario_id"] = str(usuario["_id"])
            return redirect(url_for("paginaprincipal"))

        return render_template("login.html", error="Contraseña incorrecta")
    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("registro.html", error="Las contraseñas no coinciden!")

        usuario_id = gestor.crear_usuario(nombre, email ,password)

        if usuario_id:
            session["usuario_id"] = usuario_id
        return redirect(url_for("paginaprincipal"))

    return render_template("registro.html")

@app.route("/paginaprincipal")
def paginaprincipal():
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    usuario = gestor.obtener_usuario(session["usuario_id"])

    return render_template("paginaprincipal.html", usuario=usuario)

@app.route("/cerrarsesion")
def cerrarsesion():
    session.clear()
    flash("Haz cerrado sesión", "success")
    return redirect(url_for("login"))


@app.route("/evaluacion", methods=["GET", "POST"])
def evaluacion():
    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    recomendaciones = []

    if request.method == "POST":
        edad = int(request.form.get("edad"))
        peso = float(request.form.get("peso"))
        altura = float(request.form.get("altura"))
        tipo_cuerpo = request.form.get("tipo_cuerpo")
        objetivo = request.form.get("objetivo")
        dias_entrenamiento = int(request.form.get("dias_entrenamiento"))

        # Rangos para validar los datos
        if edad < 13 or edad > 100:
            return render_template(
                "evaluacion.html",
                error="Ingresa una edad válida."
            )

        if peso < 30 or peso > 200:
            return render_template(
                "evaluacion.html",
                error="Ingresa un peso válido."
            )

        if altura < 100 or altura > 230:
            return render_template(
                "evaluacion.html",
                error="Ingresa una altura válida en centímetros."
            )

        if dias_entrenamiento < 1 or dias_entrenamiento > 7:
            return render_template(
                "evaluacion.html",
                error="Los días de entrenamiento deben estar entre 1 y 7."
            )

        # Guardar evaluación
        evaluacion_id = gestor.guardar_evaluacion(
            session["usuario_id"],
            edad,
            peso,
            altura,
            tipo_cuerpo,
            objetivo,
            dias_entrenamiento
        )

        # Crear opciones de recomendación según los datos
        if objetivo == "ganar_fuerza":
            recomendaciones.append(
                "Opción 1: Rutina enfocada en fuerza."
            )
            recomendaciones.append(
                "Opción 2: Rutina de fuerza y acondicionamiento."
            )

        elif objetivo == "mejorar_condicion":
            recomendaciones.append(
                "Opción 1: Rutina de acondicionamiento físico."
            )
            recomendaciones.append(
                "Opción 2: Rutina combinada de cardio y fuerza."
            )

        elif objetivo == "ganar_musculo":
            recomendaciones.append(
                "Opción 1: Rutina de entrenamiento de fuerza."
            )
            recomendaciones.append(
                "Opción 2: Rutina de fuerza con ejercicios complementarios."
            )

        else:
            recomendaciones.append(
                "Opción 1: Rutina general de acondicionamiento."
            )
            recomendaciones.append(
                "Opción 2: Rutina combinada de fuerza y movilidad."
            )

        return render_template(
            "evaluacion.html",
            recomendaciones=recomendaciones,
            evaluacion_guardada=True
        )

    return render_template("evaluacion.html")

@app.route('/calculadoraIMC', methods=['GET', 'POST'])
def calculadoraimc():
    resultado = None
    imagen = None
    recomendacion = None

    if request.method == 'POST':
        peso = float(request.form.get("peso"))
        altura = float(request.form.get("altura"))
        altura = altura / 100

        imc = peso / (altura ** 2)
        resultado = round(imc, 2)

        if resultado < 18.5:
            imagen = "plato-equilibrado-proteinas-grasas-carbohidratos-nutritivos_997321-32102.avif"
            recomendacion = "Procura mantener una alimentación variada y suficiente para obtener los nutrientes que tu cuerpo necesita."

        elif resultado < 25:
            imagen = "OIP (1).webp"
            recomendacion = "Continúa con una alimentación variada, actividad física regular y buenos hábitos de descanso."

        else:
            imagen = "OIP (2).webp"
            recomendacion = "Mantén hábitos saludables y, si tienes dudas sobre tu peso o crecimiento, consulta con un profesional de la salud."

    return render_template(
        "calculadoraIMC.html",
        resultado=resultado,
        imagen=imagen,
        recomendacion=recomendacion
    )
@app.route("/contactos")
def contactos():
    return render_template("contactos.html")


@app.route("/entrenamientos")
def entrenamientos():
    return render_template("entrenamientos.html")


@app.route("/nutricion")
def nutricion():
    return render_template("nutricion.html")

if __name__ == "__main__": 
    app.run(debug=True) 