from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from database import query_one, query_all, execute

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("rol") != "administrador":
            flash("No tienes permisos para realizar esa acción.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        usuario = query_one(
            "SELECT id_usuario, nombre, correo, password_hash, rol, estado "
            "FROM usuarios WHERE correo = %s",
            (correo,)
        )
        if usuario and usuario["estado"] and check_password_hash(usuario["password_hash"], password):
            session.clear()
            session["user_id"] = usuario["id_usuario"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]
            flash("Bienvenido al sistema.", "success")
            return redirect(url_for("dashboard"))
        flash("Correo o contraseña incorrectos, o cuenta desactivada.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "clientes": query_one("SELECT COUNT(*) AS total FROM clientes")["total"],
        "servicios": query_one("SELECT COUNT(*) AS total FROM servicios WHERE estado = 1")["total"],
        "pendientes": query_one(
            "SELECT COUNT(*) AS total FROM reservaciones WHERE estado = 'Pendiente'"
        )["total"],
        "atendidas": query_one(
            "SELECT COUNT(*) AS total FROM reservaciones WHERE estado = 'Atendida'"
        )["total"]
    }
    recientes = query_all(
        """SELECT r.id_reservacion, r.fecha, r.hora, r.estado,
                  c.nombre AS cliente, s.nombre AS servicio
           FROM reservaciones r
           JOIN clientes c ON c.id_cliente = r.id_cliente
           JOIN servicios s ON s.id_servicio = r.id_servicio
           ORDER BY r.fecha DESC, r.hora DESC LIMIT 6"""
    )
    return render_template("dashboard.html", stats=stats, recientes=recientes)


# ---------------- CLIENTES: CRUD ----------------
@app.route("/clientes")
@login_required
def clientes():
    buscar = request.args.get("q", "").strip()
    patron = f"%{buscar}%"
    registros = query_all(
        """SELECT * FROM clientes
           WHERE nombre LIKE %s OR correo LIKE %s OR telefono LIKE %s
           ORDER BY id_cliente DESC""",
        (patron, patron, patron)
    )
    return render_template("clientes.html", registros=registros, buscar=buscar)


@app.route("/clientes/nuevo", methods=["POST"])
@login_required
def cliente_nuevo():
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    direccion = request.form.get("direccion", "").strip()
    if not nombre:
        flash("El nombre del cliente es obligatorio.", "danger")
    else:
        execute(
            "INSERT INTO clientes (nombre, telefono, correo, direccion) VALUES (%s,%s,%s,%s)",
            (nombre, telefono, correo, direccion)
        )
        flash("Cliente registrado.", "success")
    return redirect(url_for("clientes"))


@app.route("/clientes/editar/<int:id>", methods=["POST"])
@login_required
def cliente_editar(id):
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    direccion = request.form.get("direccion", "").strip()
    if not nombre:
        flash("El nombre es obligatorio.", "danger")
    else:
        execute(
            """UPDATE clientes SET nombre=%s, telefono=%s, correo=%s, direccion=%s
               WHERE id_cliente=%s""",
            (nombre, telefono, correo, direccion, id)
        )
        flash("Cliente actualizado.", "success")
    return redirect(url_for("clientes"))


@app.route("/clientes/eliminar/<int:id>", methods=["POST"])
@login_required
def cliente_eliminar(id):
    relacionado = query_one(
        "SELECT id_reservacion FROM reservaciones WHERE id_cliente=%s LIMIT 1", (id,)
    )
    if relacionado:
        flash("No se puede eliminar: el cliente tiene reservaciones históricas.", "warning")
    else:
        execute("DELETE FROM clientes WHERE id_cliente=%s", (id,))
        flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes"))


# ---------------- SERVICIOS: CRUD ----------------
@app.route("/servicios")
@login_required
def servicios():
    buscar = request.args.get("q", "").strip()
    patron = f"%{buscar}%"
    registros = query_all(
        """SELECT * FROM servicios
           WHERE nombre LIKE %s OR descripcion LIKE %s
           ORDER BY id_servicio DESC""",
        (patron, patron)
    )
    return render_template("servicios.html", registros=registros, buscar=buscar)


@app.route("/servicios/nuevo", methods=["POST"])
@admin_required
def servicio_nuevo():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", "0").strip()
    duracion = request.form.get("duracion", "30").strip()
    try:
        precio_num = float(precio)
        duracion_num = int(duracion)
        if not nombre or precio_num < 0 or duracion_num <= 0:
            raise ValueError
        execute(
            """INSERT INTO servicios (nombre, descripcion, precio, duracion, estado)
               VALUES (%s,%s,%s,%s,1)""",
            (nombre, descripcion, precio_num, duracion_num)
        )
        flash("Servicio registrado.", "success")
    except ValueError:
        flash("Verifica nombre, precio y duración.", "danger")
    return redirect(url_for("servicios"))


@app.route("/servicios/editar/<int:id>", methods=["POST"])
@admin_required
def servicio_editar(id):
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    try:
        precio = float(request.form.get("precio", "0"))
        duracion = int(request.form.get("duracion", "30"))
        if not nombre or precio < 0 or duracion <= 0:
            raise ValueError
        execute(
            """UPDATE servicios SET nombre=%s, descripcion=%s, precio=%s, duracion=%s
               WHERE id_servicio=%s""",
            (nombre, descripcion, precio, duracion, id)
        )
        flash("Servicio actualizado.", "success")
    except ValueError:
        flash("Datos del servicio no válidos.", "danger")
    return redirect(url_for("servicios"))


@app.route("/servicios/estado/<int:id>", methods=["POST"])
@admin_required
def servicio_estado(id):
    execute(
        "UPDATE servicios SET estado = IF(estado=1,0,1) WHERE id_servicio=%s", (id,)
    )
    flash("Disponibilidad del servicio actualizada.", "success")
    return redirect(url_for("servicios"))


# ---------------- RESERVACIONES: CRUD ----------------
@app.route("/reservaciones")
@login_required
def reservaciones():
    estado = request.args.get("estado", "").strip()
    fecha = request.args.get("fecha", "").strip()
    servicio = request.args.get("servicio", "").strip()
    sql = """SELECT r.*, c.nombre AS cliente, s.nombre AS servicio
              FROM reservaciones r
              JOIN clientes c ON c.id_cliente=r.id_cliente
              JOIN servicios s ON s.id_servicio=r.id_servicio
              WHERE 1=1"""
    params = []
    if estado:
        sql += " AND r.estado=%s"
        params.append(estado)
    if fecha:
        sql += " AND r.fecha=%s"
        params.append(fecha)
    if servicio:
        sql += " AND s.nombre LIKE %s"
        params.append(f"%{servicio}%")
    sql += " ORDER BY r.fecha DESC, r.hora DESC"
    registros = query_all(sql, tuple(params))
    clientes_lista = query_all("SELECT id_cliente,nombre FROM clientes ORDER BY nombre")
    servicios_lista = query_all(
        "SELECT id_servicio,nombre FROM servicios WHERE estado=1 ORDER BY nombre"
    )
    return render_template(
        "reservaciones.html", registros=registros,
        clientes=clientes_lista, servicios=servicios_lista,
        estado=estado, fecha=fecha, servicio=servicio
    )
@app.route("/reservaciones/nueva", methods=["POST"])
@login_required
def reservacion_nueva():
    cliente = request.form.get("id_cliente", type=int)
    servicio = request.form.get("id_servicio", type=int)
    fecha = request.form.get("fecha", "")
    hora = request.form.get("hora", "")
    try:
        fecha_obj = date.fromisoformat(fecha)
        if fecha_obj < date.today() or not cliente or not servicio or not hora:
            raise ValueError
        ocupado = query_one(
            """SELECT id_reservacion FROM reservaciones
               WHERE fecha=%s AND hora=%s AND estado <> 'Cancelada' LIMIT 1""",
            (fecha, hora)
        )
        if ocupado:
            flash("Ese horario ya está ocupado. Selecciona otro.", "warning")
        else:
            execute(
                """INSERT INTO reservaciones
                   (id_cliente,id_servicio,fecha,hora,estado)
                   VALUES (%s,%s,%s,%s,'Pendiente')""",
                (cliente, servicio, fecha, hora)
            )
            flash("Reservación creada.", "success")
    except ValueError:
        flash("Revisa cliente, servicio, fecha y hora. La fecha no puede ser pasada.", "danger")
    return redirect(url_for("reservaciones"))
@app.route("/reservaciones/estado/<int:id>", methods=["POST"])
@login_required
def reservacion_estado(id):
    nuevo_estado = request.form.get("estado", "")
    permitidos = {"Pendiente", "Confirmada", "Atendida", "Cancelada"}
    if nuevo_estado not in permitidos:
        flash("Estado no válido.", "danger")
    else:
        execute(
            "UPDATE reservaciones SET estado=%s WHERE id_reservacion=%s",
            (nuevo_estado, id)
        )
        flash("Estado actualizado.", "success")
    return redirect(url_for("reservaciones"))
@app.route("/reservaciones/eliminar/<int:id>", methods=["POST"])
@admin_required
def reservacion_eliminar(id):
    execute("DELETE FROM reservaciones WHERE id_reservacion=%s", (id,))
    flash("Reservación eliminada.", "success")
    return redirect(url_for("reservaciones"))


# ---------------- USUARIOS: ADMINISTRACIÓN ----------------
@app.route("/usuarios", methods=["GET", "POST"])
@admin_required
def usuarios():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "empleado")
        if rol not in {"administrador", "empleado"} or not nombre or not correo or len(password) < 10:
            flash("Completa los datos. La contraseña debe tener al menos 10 caracteres.", "danger")
        else:
            existe = query_one("SELECT id_usuario FROM usuarios WHERE correo=%s", (correo,))
            if existe:
                flash("Ese correo ya está registrado.", "warning")
            else:
                execute(
                    """INSERT INTO usuarios (nombre,correo,password_hash,rol,estado)
                       VALUES (%s,%s,%s,%s,1)""",
                    (nombre, correo, generate_password_hash(password), rol)
                )
                flash("Usuario creado.", "success")
        return redirect(url_for("usuarios"))
    registros = query_all(
        "SELECT id_usuario,nombre,correo,rol,estado FROM usuarios ORDER BY id_usuario DESC"
    )
    return render_template("usuarios.html", registros=registros)
@app.route("/usuarios/estado/<int:id>", methods=["POST"])
@admin_required
def usuario_estado(id):
    if id == session.get("user_id"):
        flash("No puedes desactivar tu propia cuenta.", "warning")
    else:
        execute("UPDATE usuarios SET estado=IF(estado=1,0,1) WHERE id_usuario=%s", (id,))
        flash("Estado de usuario actualizado.", "success")
    return redirect(url_for("usuarios"))
@app.errorhandler(404)
def no_encontrado(error):
    return render_template("error.html", codigo=404, mensaje="Página no encontrada"), 404
@app.errorhandler(500)
def error_servidor(error):
    return render_template("error.html", codigo=500, mensaje="Ocurrió un error interno"), 500
if __name__ == "__main__":
    # Solo para desarrollo local. No usar debug=True en producción.
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("FLASK_DEBUG") == "1")