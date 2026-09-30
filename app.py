from flask import Flask, render_template, request, redirect, url_for, flash, session 

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"


@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("registro"))
    return render_template("registro.html")

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
            return redirect(url_for("labiales"))

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

        gestor.crear_usuario(nombre, email, password)
        return redirect(url_for("login"))

    return render_template("registro.html")

@app.route("/cerrarsesion")
def cerrarsesion():
    session.clear()
    flash("Haz cerrado sesión", "success")
    return redirect(url_for("login"))

if __name__ == "__main__": 
    app.run(debug=True) 