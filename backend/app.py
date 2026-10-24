"""
app.py
Backend en Flask para el Sistema de Inventario Tecnológico del colegio.
Usa MySQL como base de datos.

Estructura de datos (igual que antes):
  - usuarios (id, nombre, apellido, correo, contrasena_hash, rol, fecha_registro)
  - equipos (id, codigo, tipo, marca, modelo, numero_serie, caracteristicas,
             estado, salon_actual, fecha_registro)
  - asignaciones (id, equipo_id, usuario_id, salon, fecha_inicio, fecha_fin)

Funcionalidades:
- Login por correo (devuelve éxito/error para animar el robot en verde/rojo)
- Registro público de cuentas (siempre como 'encargado')
- Control de acceso por roles ('administrador' / 'encargado')
- Registro y consulta de equipos
- Asignación de un equipo a un encargado y salón

Requisitos: instalar las dependencias de requirements.txt con pip.
"""

import os
import mimetypes
import json
import html
from io import BytesIO
from datetime import date, datetime
import smtplib
import ssl
import threading
from email.message import EmailMessage

from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import obtener_conexion, inicializar_base_datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("INVENTARIO_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "Configura INVENTARIO_SECRET_KEY antes de iniciar el servidor."
    )
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
    "INVENTARIO_COOKIE_SECURE", "0"
) == "1"
import re

PATRON_ORIGEN_LOCAL = re.compile(
    r"^https?:\/\/(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$"
)

CORS(
    app,
    origins=PATRON_ORIGEN_LOCAL,
    supports_credentials=True
)

@app.before_request
def validar_origen_solicitud():
    """Evita que otro sitio use la sesión para cambiar datos."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origen = request.headers.get("Origin")
        if origen and not PATRON_ORIGEN_LOCAL.match(origen):
            return jsonify({"error": "Origen no permitido"}), 403


@app.after_request
def agregar_cabeceras_seguridad(respuesta):
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    return respuesta


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    return jsonify({"success": False, "mensaje": "La foto no puede superar 5 MB"}), 413


@app.errorhandler(404)
def ruta_no_encontrada(error):
    if (
        request.method == "POST"
        and re.fullmatch(r"/equipos/\d+/reportar-dano/?", request.path)
    ):
        return jsonify({
            "success": False,
            "mensaje": (
                "El servidor no reconoce la ruta para reportar daños. "
                "Reinicia Flask para que cargue la versión actualizada."
            )
        }), 404
    return error


DIRECTORIO_PLANTILLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
DIRECTORIO_FOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DIRECTORIO_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DIRECTORIO_IMAGENES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes")

os.makedirs(DIRECTORIO_STATIC, exist_ok=True)
os.makedirs(DIRECTORIO_IMAGENES, exist_ok=True)

@app.route("/static/<filename>")
def servir_static(filename):
    mimetype = "image/webp" if filename.lower().endswith(".webp") else None
    return send_from_directory(DIRECTORIO_STATIC, filename, mimetype=mimetype)
EXTENSIONES_FOTO = {"jpg", "jpeg", "png", "webp", "gif"}
os.makedirs(DIRECTORIO_FOTOS, exist_ok=True)


def foto_valida(archivo, extension):
    """Comprueba la firma del archivo, no solo su nombre."""
    firma = archivo.stream.read(12)
    archivo.stream.seek(0)
    firmas = {
        "jpg": lambda datos: datos.startswith(b"\xff\xd8\xff"),
        "jpeg": lambda datos: datos.startswith(b"\xff\xd8\xff"),
        "png": lambda datos: datos.startswith(b"\x89PNG\r\n\x1a\n"),
        "gif": lambda datos: datos.startswith((b"GIF87a", b"GIF89a")),
        "webp": lambda datos: datos.startswith(b"RIFF") and datos[8:12] == b"WEBP"
    }
    return firmas[extension](firma)


def guardar_foto_en_directorio(codigo, nombre_equipo, archivo, extension):
    """Guarda la foto en backend/imagenes con el código y el tipo del equipo."""
    codigo_seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", (codigo or "equipo").strip()) or "equipo"
    nombre_equipo_seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", (nombre_equipo or "equipo").strip()) or "equipo"
    nombre_archivo = f"{codigo_seguro}_{nombre_equipo_seguro}.{extension}"
    ruta_archivo = os.path.join(DIRECTORIO_IMAGENES, nombre_archivo)
    archivo.stream.seek(0)
    archivo.save(ruta_archivo)
    return f"/imagenes/{nombre_archivo}"


def migrar_fotos_a_base_datos():
    """Migra a MySQL las fotos antiguas que todavía estén en uploads."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, foto FROM equipos "
            "WHERE foto IS NOT NULL AND foto_datos IS NULL"
        )
        pendientes = cursor.fetchall()
        for equipo in pendientes:
            nombre = os.path.basename(equipo["foto"])
            ruta = os.path.join(DIRECTORIO_FOTOS, nombre)
            if not os.path.isfile(ruta):
                continue
            with open(ruta, "rb") as archivo:
                datos = archivo.read()
            mime = mimetypes.guess_type(nombre)[0] or "application/octet-stream"
            cursor.execute(
                "UPDATE equipos SET foto_datos = %s, foto_mime = %s WHERE id = %s",
                (datos, mime, equipo["id"])
            )
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def registrar_movimiento(usuario_id, accion, detalle):
    """Guarda una acción sin interrumpir la operación principal si falla el registro."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO movimientos (usuario_id, accion, detalle)
               VALUES (%s, %s, %s)""",
            (usuario_id, accion, detalle[:255])
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()


def obtener_correos_alertas():
    """Obtiene los destinatarios de alertas, incluyendo configuraciones antiguas de un solo correo."""
    correo_defecto = os.environ.get("INVENTARIO_ADMIN_EMAIL", "admin@colegio.local").strip().lower()
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'correo_alertas'")
        fila = cursor.fetchone()
        if fila:
            valor = (fila.get("valor") or "").strip()
            if not valor:
                return []
            try:
                datos = json.loads(valor)
            except json.JSONDecodeError:
                datos = valor.split(",")
            if isinstance(datos, str):
                datos = [datos]
            if isinstance(datos, list):
                return list(dict.fromkeys(
                    str(correo).strip().lower()
                    for correo in datos
                    if str(correo).strip()
                ))
    except Exception:
        app.logger.exception("No se pudo cargar la configuración de correos de alerta")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conexion" in locals():
            conexion.close()
    return [correo_defecto] if correo_defecto else []


def correo_valido(correo):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo))


def enviar_correo_smtp(destinatario, asunto, cuerpo_texto, cuerpo_html=None):
    """Envía un correo mediante SMTP. Si falla o no está configurado, registra el evento sin abortar."""
    if not destinatario or "@" not in destinatario:
        return False, "Dirección de correo no válida"

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    if not smtp_host:
        mensaje = "Servidor SMTP no configurado; el correo no fue enviado"
        app.logger.error("%s para %s: %s", mensaje, destinatario, asunto)
        return False, mensaje

    try:
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        return False, "SMTP_PORT debe ser un número válido"
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    remitente = os.environ.get("SMTP_FROM", smtp_user or "inventario@colegio.local")

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario
    msg.set_content(cuerpo_texto)
    if cuerpo_html:
        msg.add_alternative(cuerpo_html, subtype="html")

    try:
        if smtp_port == 465:
            contexto = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=contexto, timeout=10) as servidor:
                if smtp_user and smtp_pass:
                    servidor.login(smtp_user, smtp_pass)
                servidor.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as servidor:
                servidor.starttls(context=ssl.create_default_context())
                if smtp_user and smtp_pass:
                    servidor.login(smtp_user, smtp_pass)
                servidor.send_message(msg)
        app.logger.info("Correo de alerta enviado a %s", destinatario)
        return True, "Correo enviado correctamente"
    except Exception as e:
        app.logger.exception("Error enviando correo a %s", destinatario)
        return False, str(e)


def notificar_equipo_danado_async(
    equipo_info,
    usuario_id,
    accion="registro",
    detalle_reporte=None,
    enviar_ahora=False
):
    """Registra el movimiento de equipo dañado y notifica a cada destinatario configurado."""
    correos_destino = obtener_correos_alertas()
    codigo = equipo_info.get("codigo", "N/A")
    tipo = str(equipo_info.get("tipo", "N/A")).replace("_", " ").title()
    marca = equipo_info.get("marca", "")
    modelo = equipo_info.get("modelo", "")
    salon = equipo_info.get("salon_actual") or equipo_info.get("salon") or "Sin salón asignado"
    seccion = equipo_info.get("seccion") or "N/A"
    docente = equipo_info.get("docente_cargo") or "Sin docente a cargo"
    caracteristicas = detalle_reporte or equipo_info.get("caracteristicas") or "Sin observaciones especificadas"
    ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    destinatarios_texto = ", ".join(correos_destino) or "Sin destinatarios configurados"

    # Registrar el evento en la tabla de movimientos
    detalle_mov = f"ALERTA DAÑADO: Equipo {codigo} ({tipo} {marca}) en {salon} - Docente: {docente} -> Notif: {destinatarios_texto}"
    if detalle_reporte:
        detalle_mov += f" - Reporte: {detalle_reporte}"
    registrar_movimiento(usuario_id, "alerta_equipo_danado", detalle_mov)
    if not correos_destino:
        app.logger.error("No hay destinatarios configurados para la alerta del equipo %s", codigo)
        return {"enviados": [], "fallidos": [], "mensaje": "No hay correos destinatarios configurados"}

    # Preparar el correo
    asunto = f"🚨 ALERTA: Equipo reportado como DAÑADO [{codigo}] - Inventario Tecnológico"
    cuerpo_texto = f"""ALERTA DE INVENTARIO TECNOLÓGICO

Se ha registrado o modificado un equipo tecnológico en estado DAÑADO:

- Código del equipo: {codigo}
- Tipo: {tipo}
- Marca / Modelo: {marca} {modelo}
- Docente a cargo: {docente}
- Salón / Ubicación: {salon}
- Sección / Área: {seccion}
- Estado: DAÑADO
- Descripción / Falla: {caracteristicas}
- Fecha y hora exacta: {ahora_str}

Por favor, revise este equipo y gestione su reparación o sustitución técnica.
Sistema de Inventario Tecnológico Escolar
"""
    cuerpo_html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 620px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
      <div style="background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%); color: #ffffff; padding: 18px 22px; border-radius: 10px; margin-bottom: 22px;">
        <h2 style="margin: 0; font-size: 20px; letter-spacing: -0.02em;">🚨 Alerta: Equipo Tecnológico DAÑADO</h2>
        <p style="margin: 6px 0 0; font-size: 13px; opacity: 0.92;">Notificación automática del Sistema de Inventario</p>
      </div>
      <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #1e293b;">
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; width: 160px;">Código:</td><td style="padding: 10px 0; font-size: 16px; font-weight: bold; color: #dc2626;">{html.escape(str(codigo))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Tipo de equipo:</td><td style="padding: 10px 0;">{html.escape(str(tipo))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Marca y Modelo:</td><td style="padding: 10px 0;">{html.escape(str(marca))} {html.escape(str(modelo))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Docente a cargo:</td><td style="padding: 10px 0; color: #0284c7; font-weight: bold;">{html.escape(str(docente))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Salón / Ubicación:</td><td style="padding: 10px 0;">{html.escape(str(salon))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Sección / Área:</td><td style="padding: 10px 0;">{html.escape(str(seccion))}</td></tr>
        <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold;">Falla / Detalle:</td><td style="padding: 10px 0; background: #fff1f2; padding-left: 8px; border-radius: 4px; color: #991b1b;">{html.escape(str(caracteristicas))}</td></tr>
        <tr><td style="padding: 10px 0; font-weight: bold;">Fecha y hora exacta:</td><td style="padding: 10px 0; font-family: monospace;">{ahora_str}</td></tr>
      </table>
      <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
        Esta notificación fue enviada automáticamente a: <strong>{html.escape(destinatarios_texto)}</strong>.
      </div>
    </div>
    """

    def enviar_a_destinatarios():
        enviados = []
        fallidos = []
        for correo_dest in correos_destino:
            exito, mensaje = enviar_correo_smtp(correo_dest, asunto, cuerpo_texto, cuerpo_html)
            (enviados if exito else fallidos).append(
                {"correo": correo_dest, "mensaje": mensaje}
            )
        return {"enviados": enviados, "fallidos": fallidos}

    if enviar_ahora:
        return enviar_a_destinatarios()
    hilo = threading.Thread(target=enviar_a_destinatarios, daemon=True)
    hilo.start()
    return {"enviados": [], "fallidos": [], "mensaje": "Notificación en proceso"}


def crear_salas_iniciales():
    """Crea un listado base de salas y evita duplicados."""
    nombres = [
        "Sala 21",
        "Sala de informática",
        "Sala 1",
        "Sala 2",
        "Sala 3",
        "Sala 4",
        "Sala 5",
        "Sala 6",
        "Sala 7",
        "Sala 8",
    ]
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM salas")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO salas (nombre) VALUES (%s)",
                [(nombre,) for nombre in nombres]
            )
            conexion.commit()
    finally:
        cursor.close()
        conexion.close()


# Crea las tablas automáticamente la primera vez que arranca el servidor
inicializar_base_datos()
crear_salas_iniciales()
migrar_fotos_a_base_datos()


def crear_administrador_inicial():
    """Crea el primer administrador si no existe."""
    correo = os.environ.get("INVENTARIO_ADMIN_EMAIL", "").strip().lower()
    contrasena = os.environ.get("INVENTARIO_ADMIN_PASSWORD", "")
    nombre = os.environ.get("INVENTARIO_ADMIN_NAME", "").strip()
    apellido = os.environ.get("INVENTARIO_ADMIN_LASTNAME", "").strip()
    
    if not correo or len(contrasena) < 12 or not nombre or not apellido:
        print("Administrador inicial no configurado: define las variables INVENTARIO_ADMIN_*")
        return

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'administrador'")
    cantidad = cursor.fetchone()[0]
    if cantidad == 0:
        cursor.execute(
            """INSERT INTO usuarios
               (nombre, apellido, correo, contrasena_hash, rol)
               VALUES (%s, %s, %s, %s, 'administrador')""",
            (nombre, apellido, correo, generate_password_hash(contrasena))
        )
        conexion.commit()
        print(f"✓ Administrador creado: {nombre} {apellido} ({correo})")
    cursor.close()
    conexion.close()


crear_administrador_inicial()


# ---------------------------------------------------------------------------
# PÁGINAS (sirve tu HTML directamente desde el mismo servidor)
# ---------------------------------------------------------------------------

@app.route("/")
def pagina_principal():
    """Muestra login o panel según el estado de la sesión."""
    archivo = "panel.html" if "usuario_id" in session else "login.html"
    return send_from_directory(DIRECTORIO_PLANTILLAS, archivo)


@app.route("/<path:nombre_archivo>")
def servir_archivo(nombre_archivo):
    # Sirve cualquier otro archivo de la carpeta de páginas.
    if nombre_archivo == "panel.html" and "usuario_id" not in session:
        return send_from_directory(DIRECTORIO_PLANTILLAS, "login.html")
    return send_from_directory(DIRECTORIO_PLANTILLAS, nombre_archivo)


@app.route("/uploads/<path:nombre_archivo>")
def servir_foto(nombre_archivo):
    return send_from_directory(DIRECTORIO_FOTOS, nombre_archivo)


@app.route("/imagenes/<path:nombre_archivo>")
def servir_imagen_equipo(nombre_archivo):
    return send_from_directory(DIRECTORIO_IMAGENES, nombre_archivo)


@app.route("/fotos/<int:equipo_id>")
def servir_foto_desde_bd(equipo_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT foto_datos, foto_mime FROM equipos WHERE id = %s",
            (equipo_id,)
        )
        foto = cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()
    if not foto or not foto["foto_datos"]:
        return jsonify({"error": "Foto no encontrada"}), 404
    return send_file(
        BytesIO(foto["foto_datos"]),
        mimetype=foto["foto_mime"] or "application/octet-stream",
        max_age=3600
    )


# ---------------------------------------------------------------------------
# DECORADORES DE SEGURIDAD
# ---------------------------------------------------------------------------

def login_requerido(funcion):
    """Bloquea el acceso si el usuario no ha iniciado sesión."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"error": "Debes iniciar sesión"}), 401
        return funcion(*args, **kwargs)
    return envoltura


def admin_requerido(funcion):
    """Bloquea el acceso si el usuario no tiene rol de administrador."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"error": "Debes iniciar sesión"}), 401
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (session["usuario_id"],))
        fila = cursor.fetchone()
        cursor.close()
        conexion.close()
        if not fila or str(fila[0]).strip().lower() != "administrador":
            return jsonify({"error": "Solo el administrador puede hacer esto"}), 403
        return funcion(*args, **kwargs)
    return envoltura


def roles_requeridos(*roles_permitidos):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if "usuario_id" not in session:
                return jsonify({"error": "Debes iniciar sesión"}), 401
            rol = str(session.get("rol", "")).strip().lower()
            if rol not in roles_permitidos:
                return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

@app.route("/login", methods=["POST"])
def login():
    """
    Recibe correo y contraseña desde el formulario del frontend.
    Devuelve {"success": true/false} para que el JavaScript del frontend
    ponga el robot en verde (correcto) o rojo (incorrecto).
    """
    datos = request.get_json(silent=True) or {}
    correo = datos.get("correo", "").strip().lower()
    contrasena = datos.get("contrasena", "")

    if not correo or not contrasena:
        return jsonify({"success": False, "mensaje": "Correo y contraseña son obligatorios"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM usuarios WHERE correo = %s", (correo,)
    )
    fila = cursor.fetchone()
    cursor.close()
    conexion.close()

    if fila and check_password_hash(fila["contrasena_hash"], contrasena):
        fila["rol"] = str(fila["rol"]).strip().lower()
        # Solo validar estado_autorizacion para encargados, no para administradores
        if fila["rol"] == "encargado" and fila.get("estado_autorizacion", "aprobado") != "aprobado":
            mensajes = {
                "pendiente": "Tu cuenta está pendiente de autorización por un administrador",
                "rechazado": "Tu solicitud de cuenta fue rechazada"
            }
            return jsonify({
                "success": False,
                "mensaje": mensajes.get(fila.get("estado_autorizacion"), "Cuenta no autorizada")
            }), 403
        session["usuario_id"] = fila["id"]
        session["rol"] = fila["rol"]
        registrar_movimiento(fila["id"], "inicio_sesion", "Inicio de sesión correcto")
        return jsonify({
            "success": True,
            "rol": fila["rol"],
            "nombre": f'{fila["nombre"]} {fila["apellido"]}'
        })

    return jsonify({"success": False, "mensaje": "Correo o contraseña incorrectos"})


@app.route("/logout", methods=["POST"])
def logout():
    usuario_id = session.get("usuario_id")
    if usuario_id:
        registrar_movimiento(usuario_id, "cierre_sesion", "Cierre de sesión")
    session.clear()
    return jsonify({"success": True})


@app.route("/cambiar-contrasena", methods=["POST"])
@login_requerido
def cambiar_contrasena():
    datos = request.get_json(silent=True) or {}
    actual = datos.get("contrasena_actual", "")
    nueva = datos.get("contrasena_nueva", "")
    confirmacion = datos.get("confirmacion", "")

    if not actual or not nueva or not confirmacion:
        return jsonify({"success": False, "mensaje": "Completa todos los campos"}), 400
    if len(nueva) < 8:
        return jsonify({"success": False, "mensaje": "La nueva contraseña debe tener mínimo 8 caracteres"}), 400
    if nueva != confirmacion:
        return jsonify({"success": False, "mensaje": "Las nuevas contraseñas no coinciden"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT contrasena_hash FROM usuarios WHERE id = %s",
            (session["usuario_id"],)
        )
        usuario = cursor.fetchone()
        if not usuario or not check_password_hash(usuario["contrasena_hash"], actual):
            return jsonify({"success": False, "mensaje": "La contraseña actual no es correcta"}), 400
        cursor.execute(
            "UPDATE usuarios SET contrasena_hash = %s WHERE id = %s",
            (generate_password_hash(nueva), session["usuario_id"])
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo cambiar la contraseña"}), 500
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "cambiar_contrasena",
        "Contraseña actualizada correctamente"
    )
    return jsonify({"success": True, "mensaje": "Contraseña actualizada correctamente"})


@app.route("/sesion", methods=["GET"])
@login_requerido
def sesion_actual():
    """Devuelve los datos del usuario autenticado para el panel."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nombre, apellido, correo, rol FROM usuarios WHERE id = %s",
        (session["usuario_id"],)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()

    if not usuario:
        session.clear()
        return jsonify({"error": "La sesión ya no es válida"}), 401

    usuario["rol"] = str(usuario["rol"]).strip().lower()
    session["rol"] = usuario["rol"]
    return jsonify(usuario)


# ---------------------------------------------------------------------------
# REGISTRO PÚBLICO (pestaña "Registrarse" del frontend)
# ---------------------------------------------------------------------------

@app.route("/registro", methods=["POST"])
@login_requerido
@admin_requerido
def registro_publico():
    """
    Registra usuarios. Los administradores se crean directamente, los encargados requieren autorización.
    """
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre", "").strip()
    apellido = datos.get("apellido", "").strip()
    correo = datos.get("correo", "").strip().lower()
    contrasena = datos.get("contrasena", "")
    rol = datos.get("rol", "encargado")

    if not nombre or not apellido or not correo or len(contrasena) < 8:
        return jsonify({
            "success": False,
            "mensaje": "Completa todos los campos y usa una contraseña de mínimo 8 caracteres"
        }), 400
    if rol not in {"encargado", "administrador", "rector", "coordinador"}:
        return jsonify({"success": False, "mensaje": "Rol no válido"}), 400

    contrasena_hash = generate_password_hash(contrasena)
    
    rol = "encargado"
    estado = "pendiente"

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
                """INSERT INTO usuarios
                    (nombre, apellido, correo, contrasena_hash, rol, estado_autorizacion)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                (nombre, apellido, correo, contrasena_hash, rol, estado)
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "Ese correo ya está registrado"}), 400
    finally:
        cursor.close()
        conexion.close()
    
    registrar_movimiento(None, "solicitud_usuario", f"Solicitud de encargado: {correo}")
    return jsonify({
        "success": True,
        "mensaje": "Solicitud enviada. Un administrador debe autorizar tu cuenta."
    })


# ---------------------------------------------------------------------------
# GESTIÓN DE USUARIOS (solo administrador, para crear otros administradores)
# ---------------------------------------------------------------------------

@app.route("/usuarios", methods=["POST"])
@login_requerido
@admin_requerido
def crear_usuario():
    """El administrador registra un nuevo usuario (encargado o administrador)."""
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre", "").strip()
    apellido = datos.get("apellido", "").strip()
    correo = datos.get("correo", "").strip().lower()
    contrasena = datos.get("contrasena", "")
    rol = datos.get("rol", "encargado")

    if not nombre or not apellido or not correo or len(contrasena) < 8:
        return jsonify({"success": False, "mensaje": "Datos de usuario incompletos"}), 400
    if rol not in {"encargado", "administrador", "rector", "coordinador"}:
        return jsonify({"success": False, "mensaje": "Rol no válido"}), 400
    contrasena_hash = generate_password_hash(contrasena)
    
    # Los encargados requieren aprobación; los demás perfiles son internos.
    estado = "pendiente" if rol == "encargado" else "aprobado"

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO usuarios (nombre, apellido, correo, contrasena_hash, rol, estado_autorizacion)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nombre, apellido, correo, contrasena_hash, rol, estado)
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo crear el usuario"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "crear_usuario",
        f"Usuario creado: {correo} ({rol})"
    )

    return jsonify({"success": True, "mensaje": "Usuario creado correctamente"})


# ---------------------------------------------------------------------------
# EQUIPOS (inventario)
# ---------------------------------------------------------------------------

@app.route("/equipos", methods=["GET"])
@login_requerido
def listar_equipos():
    """Devuelve la lista completa de equipos registrados con hora exacta y docente."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT e.id, e.codigo, e.tipo, e.marca, e.modelo, e.numero_serie,
                  e.caracteristicas, e.foto, e.estado, e.salon_actual, e.seccion,
                  e.docente_cargo, e.fecha_registro, e.fecha_modificacion, e.modificado_por, e.foto_mime,
                  a.salon AS salon_asignacion,
                  CONCAT(u.nombre, ' ', u.apellido) AS asignado,
                  CONCAT(mu.nombre, ' ', mu.apellido) AS modificado_por_nombre,
                  e.foto_datos IS NOT NULL AS tiene_foto
           FROM equipos e
           LEFT JOIN asignaciones a
             ON a.equipo_id = e.id AND a.fecha_fin IS NULL
           LEFT JOIN usuarios u ON u.id = a.usuario_id
           LEFT JOIN usuarios mu ON mu.id = e.modificado_por
           ORDER BY e.fecha_registro DESC"""
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    for fila in filas:
        fila.pop("foto_datos", None)
        if fila.pop("tiene_foto", False):
            fila["foto_url"] = f"/fotos/{fila['id']}"
        elif fila.get("foto"):
            fila["foto_url"] = f"/uploads/{os.path.basename(fila['foto'])}"

        # Formateo de fecha y hora exacta como string estándar
        if isinstance(fila.get("fecha_registro"), (datetime, date)):
            fila["fecha_registro"] = fila["fecha_registro"].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(fila.get("fecha_modificacion"), (datetime, date)):
            fila["fecha_modificacion"] = fila["fecha_modificacion"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(filas)


@app.route("/equipos", methods=["POST"])
@login_requerido
@roles_requeridos("administrador", "encargado")
def registrar_equipo():
    """
    Registra un equipo tecnológico, valida duplicidad de código,
    guarda el docente a cargo y notifica por correo si está dañado.
    """
    codigo = request.form.get("codigo", "").strip()
    tipo = request.form.get("tipo", "").strip().lower()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    numero_serie = request.form.get("numero_serie")
    caracteristicas = request.form.get("caracteristicas")
    estado = request.form.get("estado", "bueno").strip().lower()
    salon_actual = request.form.get("salon_actual", "").strip()
    seccion = request.form.get("seccion", "").strip()
    docente_cargo = request.form.get("docente_cargo", "").strip()

    tipos_validos = {"computador", "tablet", "televisor", "aire_acondicionado", "torre", "teclado", "mouse", "router", "estabilizador", "pantalla"}
    if not codigo or tipo not in tipos_validos:
        return jsonify({"success": False, "mensaje": "Código y tipo son obligatorios"}), 400
    if estado not in {"bueno", "danado", "reparacion"}:
        return jsonify({"success": False, "mensaje": "Estado no válido"}), 400

    # 1. Validación de código duplicado
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id FROM equipos WHERE codigo = %s", (codigo,))
    if cursor.fetchone():
        cursor.close()
        conexion.close()
        return jsonify({
            "success": False,
            "mensaje": f"El equipo con el código '{codigo}' ya está registrado. Por favor, ingresa un código diferente."
        }), 400

    archivo = request.files.get("foto")
    foto_datos = None
    foto_mime = None
    foto_relativa = None
    if archivo and archivo.filename:
        extension = os.path.splitext(archivo.filename)[1].lower().lstrip(".")
        if extension not in EXTENSIONES_FOTO:
            cursor.close()
            conexion.close()
            return jsonify({"success": False, "mensaje": "La foto debe ser JPG, PNG, WEBP o GIF"}), 400
        if not foto_valida(archivo, extension):
            cursor.close()
            conexion.close()
            return jsonify({"success": False, "mensaje": "El archivo no es una imagen válida"}), 400
        foto_datos = archivo.read()
        foto_mime = mimetypes.types_map.get(f".{extension}", archivo.mimetype)
        nombre_descriptivo = tipo.replace("_", " ").title() if tipo else "equipo"
        foto_relativa = guardar_foto_en_directorio(codigo, nombre_descriptivo, archivo, extension)

    cursor.close()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """INSERT INTO equipos
                     (codigo, tipo, marca, modelo, numero_serie, caracteristicas,
                      foto_datos, foto_mime, estado, salon_actual, seccion, docente_cargo)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (codigo, tipo, marca, modelo, numero_serie, caracteristicas,
                 foto_datos, foto_mime, estado, salon_actual, seccion, docente_cargo)
        )
        equipo_id = cursor.lastrowid

        if salon_actual:
            cursor.execute(
                """INSERT INTO asignaciones (equipo_id, usuario_id, salon, fecha_inicio)
                   VALUES (%s, %s, %s, %s)""",
                (equipo_id, session["usuario_id"], salon_actual, date.today().isoformat())
            )
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": f"No se pudo guardar el equipo: {e}"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "crear_equipo",
        f"Equipo registrado: {codigo}"
    )

    # Si se registra como dañado, enviar notificación automática por correo
    if estado == "danado":
        equipo_info = {
            "codigo": codigo,
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "numero_serie": numero_serie,
            "caracteristicas": caracteristicas,
            "estado": estado,
            "salon_actual": salon_actual,
            "seccion": seccion,
            "docente_cargo": docente_cargo
        }
        notificar_equipo_danado_async(equipo_info, session["usuario_id"], accion="registro")

    return jsonify({
        "success": True,
        "mensaje": "Equipo registrado correctamente" + (" (notificación de daño generada)" if estado == "danado" else ""),
        "id": equipo_id,
        "foto": foto_relativa or (f"/fotos/{equipo_id}" if foto_datos else None)
    })


@app.route("/equipos/<int:equipo_id>", methods=["PUT"])
@login_requerido
@roles_requeridos("administrador", "encargado")
def editar_equipo(equipo_id):
    """Actualiza la información de un equipo, valida código único y notifica si pasa a dañado."""
    codigo = request.form.get("codigo", "").strip()
    tipo = request.form.get("tipo", "").strip().lower()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    numero_serie = request.form.get("numero_serie", "").strip()
    caracteristicas = request.form.get("caracteristicas", "").strip()
    estado = request.form.get("estado", "").strip().lower()
    salon_actual = request.form.get("salon_actual", "").strip()
    seccion = request.form.get("seccion", "").strip()
    docente_cargo = request.form.get("docente_cargo", "").strip()

    tipos_validos = {"computador", "tablet", "televisor", "aire_acondicionado", "torre", "teclado", "mouse", "router", "estabilizador", "pantalla"}
    if not codigo or tipo not in tipos_validos:
        return jsonify({"success": False, "mensaje": "Código y tipo son obligatorios"}), 400
    if estado not in {"bueno", "danado", "reparacion"}:
        return jsonify({"success": False, "mensaje": "Estado no válido"}), 400

    archivo = request.files.get("foto")
    foto_datos = None
    foto_mime = None
    if archivo and archivo.filename:
        extension = os.path.splitext(archivo.filename)[1].lower().lstrip(".")
        if extension not in EXTENSIONES_FOTO or not foto_valida(archivo, extension):
            return jsonify({"success": False, "mensaje": "La foto debe ser JPG, PNG, WEBP o GIF válida"}), 400
        foto_datos = archivo.read()
        foto_mime = mimetypes.types_map.get(f".{extension}", archivo.mimetype)
        nombre_descriptivo = tipo.replace("_", " ").title() if tipo else "equipo"
        guardar_foto_en_directorio(codigo, nombre_descriptivo, archivo, extension)

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, estado, foto FROM equipos WHERE id = %s", (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            return jsonify({"success": False, "mensaje": "El equipo no existe"}), 404

        # Validación de código duplicado en otro equipo
        cursor.execute("SELECT id FROM equipos WHERE codigo = %s AND id != %s", (codigo, equipo_id))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "mensaje": f"Ya existe otro equipo registrado con el código '{codigo}'. Por favor, usa un código diferente."
            }), 400

        estado_anterior = equipo.get("estado")

        cursor.execute(
            """UPDATE equipos
               SET codigo = %s, tipo = %s, marca = %s, modelo = %s,
                   numero_serie = %s, caracteristicas = %s,
                   foto_datos = COALESCE(%s, foto_datos),
                   foto_mime = COALESCE(%s, foto_mime),
                   estado = %s, salon_actual = %s, seccion = %s, docente_cargo = %s,
                   fecha_modificacion = CURRENT_TIMESTAMP, modificado_por = %s
               WHERE id = %s""",
            (codigo, tipo, marca, modelo, numero_serie, caracteristicas,
                 foto_datos, foto_mime, estado, salon_actual, seccion, docente_cargo,
                 session["usuario_id"], equipo_id)
        )
        cursor.execute(
            """UPDATE asignaciones
               SET salon = %s
               WHERE equipo_id = %s AND fecha_fin IS NULL""",
            (salon_actual, equipo_id)
        )
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": f"No se pudo actualizar el equipo: {e}"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "editar_equipo",
        f"Equipo actualizado: {codigo}"
    )

    # Si se cambia o se guarda en estado dañado, enviar alerta
    if estado == "danado":
        equipo_info = {
            "codigo": codigo,
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "numero_serie": numero_serie,
            "caracteristicas": caracteristicas,
            "estado": estado,
            "salon_actual": salon_actual,
            "seccion": seccion,
            "docente_cargo": docente_cargo
        }
        notificar_equipo_danado_async(equipo_info, session["usuario_id"], accion="modificacion")

    return jsonify({"success": True, "mensaje": "Equipo actualizado correctamente" + (" (notificación de daño generada)" if estado == "danado" else "")})


@app.route("/equipos/<int:equipo_id>/reportar-dano", methods=["POST"])
@login_requerido
@roles_requeridos("administrador", "encargado")
def reportar_dano_equipo(equipo_id):
    """Marca un equipo como dañado y envía el reporte a todos los correos configurados."""
    datos = request.get_json(silent=True) or {}
    detalle = str(datos.get("detalle", "")).strip()
    if not detalle:
        return jsonify({"success": False, "mensaje": "Describe el daño antes de enviar el reporte."}), 400
    if len(detalle) > 2000:
        return jsonify({"success": False, "mensaje": "La descripción no puede superar 2000 caracteres."}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT codigo, tipo, marca, modelo, numero_serie, caracteristicas,
                      estado, salon_actual, seccion, docente_cargo
               FROM equipos WHERE id = %s""",
            (equipo_id,)
        )
        equipo = cursor.fetchone()
        if not equipo:
            return jsonify({"success": False, "mensaje": "El equipo no existe."}), 404

        cursor.execute(
            """UPDATE equipos
               SET estado = 'danado', fecha_modificacion = CURRENT_TIMESTAMP,
                   modificado_por = %s
               WHERE id = %s""",
            (session["usuario_id"], equipo_id)
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        app.logger.exception("No se pudo guardar el reporte de daño del equipo %s", equipo_id)
        return jsonify({"success": False, "mensaje": "No se pudo guardar el reporte del equipo."}), 500
    finally:
        cursor.close()
        conexion.close()

    resultado_envio = notificar_equipo_danado_async(
        equipo,
        session["usuario_id"],
        accion="reporte",
        detalle_reporte=detalle,
        enviar_ahora=True
    )
    if resultado_envio.get("fallidos") or not resultado_envio.get("enviados"):
        return jsonify({
            "success": False,
            "reportado": True,
            "mensaje": "El equipo quedó reportado como dañado, pero no se pudo enviar el correo. Verifica la configuración SMTP y los destinatarios.",
            "enviados": resultado_envio.get("enviados", []),
            "fallidos": resultado_envio.get("fallidos", []),
            "error": resultado_envio.get("mensaje")
        }), 502

    return jsonify({
        "success": True,
        "reportado": True,
        "mensaje": f"Daño reportado. Se notificó a {len(resultado_envio['enviados'])} correo(s).",
        "enviados": resultado_envio["enviados"]
    })


@app.route("/equipos/<int:equipo_id>", methods=["DELETE"])
@login_requerido
@admin_requerido
def eliminar_equipo(equipo_id):
    """Elimina un equipo, sus asignaciones y su foto asociada."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT foto FROM equipos WHERE id = %s", (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            return jsonify({"success": False, "mensaje": "El equipo no existe"}), 404

        cursor.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo eliminar el equipo"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "eliminar_equipo",
        f"Equipo eliminado: {equipo_id}"
    )

    return jsonify({"success": True, "mensaje": "Equipo eliminado correctamente"})


@app.route("/salas", methods=["GET"])
@login_requerido
def listar_salas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre FROM salas ORDER BY id ASC")
        filas = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()
    return jsonify(filas)


@app.route("/salas", methods=["POST"])
@login_requerido
@admin_requerido
def crear_sala():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("nombre", "")).strip()
    if not nombre:
        return jsonify({"success": False, "mensaje": "El nombre de la sala es obligatorio"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM salas WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            return jsonify({"success": False, "mensaje": "Esa sala ya existe"}), 409

        cursor.execute(
            "INSERT INTO salas (nombre) VALUES (%s)",
            (nombre,)
        )
        conexion.commit()
        sala_id = cursor.lastrowid
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo crear la sala"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(session["usuario_id"], "crear_sala", f"Sala creada: {nombre}")
    return jsonify({"success": True, "mensaje": "Sala creada correctamente", "id": sala_id})


@app.route("/salas/<int:sala_id>", methods=["PUT"])
@login_requerido
@admin_requerido
def renombrar_sala(sala_id):
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("nombre", "")).strip()
    if not nombre:
        return jsonify({"success": False, "mensaje": "El nombre nuevo es obligatorio"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre FROM salas WHERE id = %s", (sala_id,))
        sala = cursor.fetchone()
        if not sala:
            return jsonify({"success": False, "mensaje": "La sala no existe"}), 404

        cursor.execute("SELECT id FROM salas WHERE nombre = %s AND id != %s", (nombre, sala_id))
        if cursor.fetchone():
            return jsonify({"success": False, "mensaje": "Ya existe otra sala con ese nombre"}), 409

        cursor.execute("UPDATE salas SET nombre = %s WHERE id = %s", (nombre, sala_id))
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo renombrar la sala"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(session["usuario_id"], "renombrar_sala", f"Sala renombrada: {sala['nombre']} -> {nombre}")
    return jsonify({"success": True, "mensaje": "Sala renombrada correctamente"})


@app.route("/salas/<int:sala_id>", methods=["DELETE"])
@login_requerido
@admin_requerido
def eliminar_sala(sala_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre FROM salas WHERE id = %s", (sala_id,))
        sala = cursor.fetchone()
        if not sala:
            return jsonify({"success": False, "mensaje": "La sala no existe"}), 404

        cursor.execute("DELETE FROM salas WHERE id = %s", (sala_id,))
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo eliminar la sala"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(session["usuario_id"], "eliminar_sala", f"Sala eliminada: {sala['nombre']}")
    return jsonify({"success": True, "mensaje": "Sala eliminada correctamente"})


@app.route("/usuarios", methods=["GET"])
@login_requerido
@roles_requeridos("administrador", "encargado")
def listar_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT id, nombre, apellido, rol
           FROM usuarios
           WHERE estado_autorizacion = 'aprobado'
             AND rol IN ('administrador', 'encargado')
           ORDER BY nombre, apellido"""
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(filas)


@app.route("/usuarios/gestion", methods=["GET"])
@login_requerido
@admin_requerido
def listar_usuarios_gestion():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT id, nombre, apellido, correo, rol, estado_autorizacion, fecha_registro
           FROM usuarios ORDER BY nombre, apellido"""
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(filas)


@app.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@login_requerido
@admin_requerido
def eliminar_usuario(usuario_id):
    if usuario_id == session["usuario_id"]:
        return jsonify({"success": False, "mensaje": "No puedes eliminar tu propia cuenta"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nombre, apellido, correo FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({"success": False, "mensaje": "El usuario no existe"}), 404
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo eliminar el usuario"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "eliminar_usuario",
        f"Usuario eliminado: {usuario['correo']}"
    )
    return jsonify({"success": True, "mensaje": "Usuario eliminado correctamente"})


# ---------------------------------------------------------------------------
# ASIGNACIONES
# ---------------------------------------------------------------------------

@app.route("/asignaciones/<int:equipo_id>", methods=["GET"])
@login_requerido
def historial_asignaciones(equipo_id):
    """Devuelve el historial de salones/encargados que ha tenido un equipo."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT a.*, u.nombre, u.apellido
           FROM asignaciones a
           JOIN usuarios u ON u.id = a.usuario_id
           WHERE a.equipo_id = %s
           ORDER BY a.fecha_inicio DESC""",
        (equipo_id,)
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(filas)


@app.route("/asignaciones", methods=["POST"])
@login_requerido
@roles_requeridos("administrador", "encargado")
def crear_asignacion():
    datos = request.get_json(silent=True) or {}
    equipo_id = datos.get("equipo_id")
    usuario_id = datos.get("usuario_id")
    salon = datos.get("salon", "").strip()
    fecha_inicio = datos.get("fecha_inicio") or date.today().isoformat()

    if not equipo_id or not usuario_id or not salon:
        return jsonify({"success": False, "mensaje": "Equipo, responsable y salón son obligatorios"}), 400
    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return jsonify({"success": False, "mensaje": "La fecha no es válida"}), 400
    if fecha_inicio > date.today():
        return jsonify({"success": False, "mensaje": "La fecha no puede ser futura"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id FROM equipos WHERE id = %s FOR UPDATE",
            (equipo_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "mensaje": "El equipo no existe"}), 404
        cursor.execute(
            """SELECT id FROM usuarios
               WHERE id = %s
                 AND estado_autorizacion = 'aprobado'
                 AND rol IN ('administrador', 'encargado')""",
            (usuario_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "mensaje": "El responsable no existe"}), 404
        cursor.execute(
            "UPDATE asignaciones SET fecha_fin = %s WHERE equipo_id = %s AND fecha_fin IS NULL",
            (fecha_inicio, equipo_id)
        )
        cursor.execute(
            """INSERT INTO asignaciones (equipo_id, usuario_id, salon, fecha_inicio)
               VALUES (%s, %s, %s, %s)""",
            (equipo_id, usuario_id, salon, fecha_inicio)
        )
        cursor.execute(
            "UPDATE equipos SET salon_actual = %s WHERE id = %s",
            (salon, equipo_id)
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo guardar la asignación"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "asignar_equipo",
        f"Equipo {equipo_id} asignado al usuario {usuario_id} en {salon}"
    )

    return jsonify({"success": True, "mensaje": "Asignación guardada correctamente"})


@app.route("/movimientos", methods=["GET"])
@login_requerido
@admin_requerido
def listar_movimientos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT m.id, m.accion, m.detalle, m.fecha,
                  COALESCE(CONCAT(u.nombre, ' ', u.apellido), 'Sistema') AS usuario
           FROM movimientos m
           LEFT JOIN usuarios u ON u.id = m.usuario_id
           ORDER BY m.fecha DESC, m.id DESC
           LIMIT 200"""
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(filas)


@app.route("/solicitudes", methods=["GET"])
@login_requerido
@admin_requerido
def listar_solicitudes():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """SELECT id, nombre, apellido, correo, rol, fecha_registro
           FROM usuarios WHERE estado_autorizacion = 'pendiente'
           ORDER BY fecha_registro ASC"""
    )
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(filas)


@app.route("/solicitudes/<int:usuario_id>", methods=["POST"])
@login_requerido
@admin_requerido
def resolver_solicitud(usuario_id):
    datos = request.get_json(silent=True) or {}
    decision = datos.get("decision")
    if decision not in {"aprobar", "rechazar"}:
        return jsonify({"success": False, "mensaje": "Decisión no válida"}), 400

    estado = "aprobado" if decision == "aprobar" else "rechazado"
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT correo, rol FROM usuarios WHERE id = %s AND estado_autorizacion = 'pendiente'",
            (usuario_id,)
        )
        solicitud = cursor.fetchone()
        if not solicitud:
            return jsonify({"success": False, "mensaje": "La solicitud no existe"}), 404
        cursor.execute(
            "UPDATE usuarios SET estado_autorizacion = %s WHERE id = %s",
            (estado, usuario_id)
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": "No se pudo resolver la solicitud"}), 400
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        f"{decision}_usuario",
        f"Solicitud resuelta: {solicitud['correo']} ({solicitud['rol']})"
    )
    return jsonify({"success": True, "mensaje": f"Solicitud {estado} correctamente"})


# ---------------------------------------------------------------------------
# CONFIGURACIÓN (Correo para Alertas de Equipos Dañados)
# ---------------------------------------------------------------------------

@app.route("/configuracion/correo", methods=["GET"])
@login_requerido
def obtener_configuracion_correo():
    """Devuelve las direcciones configuradas para recibir alertas de equipos dañados."""
    correos = obtener_correos_alertas()
    return jsonify({"success": True, "correos": correos, "correo": correos[0] if correos else ""})


@app.route("/configuracion/correo", methods=["POST"])
@login_requerido
@admin_requerido
def guardar_configuracion_correo():
    """Permite al administrador reemplazar la lista de destinatarios de alertas."""
    datos = request.get_json(silent=True) or {}
    correos = datos.get("correos")
    if correos is None:
        correo = str(datos.get("correo", "")).strip().lower()
        correos = [correo] if correo else []
    if not isinstance(correos, list):
        return jsonify({"success": False, "mensaje": "La lista de correos no es válida."}), 400

    correos_limpios = list(dict.fromkeys(
        str(correo).strip().lower() for correo in correos
        if str(correo).strip()
    ))
    if any(not correo_valido(correo) for correo in correos_limpios):
        return jsonify({"success": False, "mensaje": "Verifica que todos los correos sean válidos."}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO configuracion (clave, valor)
            VALUES ('correo_alertas', %s)
            ON DUPLICATE KEY UPDATE valor = %s
        """, (json.dumps(correos_limpios), json.dumps(correos_limpios)))
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        return jsonify({"success": False, "mensaje": f"No se pudo guardar el correo: {e}"}), 500
    finally:
        cursor.close()
        conexion.close()

    registrar_movimiento(
        session["usuario_id"],
        "configurar_correo_alertas",
        f"Destinatarios de alertas actualizados: {', '.join(correos_limpios) or 'ninguno'}"
    )
    return jsonify({
        "success": True,
        "mensaje": "Correos de alertas guardados correctamente",
        "correos": correos_limpios
    })


@app.route("/configuracion/correo/probar", methods=["POST"])
@login_requerido
@admin_requerido
def probar_envio_correo():
    """Envía un correo de prueba a todos los destinatarios configurados."""
    correos = obtener_correos_alertas()
    if not correos:
        return jsonify({"success": False, "mensaje": "Agrega al menos un correo destinatario."}), 400
    asunto = "🔔 Prueba de Alerta - Sistema de Inventario Tecnológico"
    cuerpo = f"Este es un correo de prueba para verificar las notificaciones automáticas del Sistema de Inventario.\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
      <h3 style="color: #0284c7; margin-top: 0;">🔔 Prueba de Configuración de Correo</h3>
      <p>Este es un correo de prueba del <strong>Sistema de Inventario Tecnológico</strong>.</p>
      <p>Si recibes este mensaje, la configuración de correo y alertas está lista para notificar equipos dañados.</p>
      <p style="font-size: 12px; color: #64748b;">Fecha y hora de envío: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """
    resultados = [
        (correo, *enviar_correo_smtp(correo, asunto, cuerpo, cuerpo_html))
        for correo in correos
    ]
    fallidos = [
        {"correo": correo, "mensaje": mensaje}
        for correo, exito, mensaje in resultados if not exito
    ]
    enviados = [correo for correo, exito, _ in resultados if exito]
    if fallidos:
        return jsonify({
            "success": False,
            "mensaje": "No se pudo enviar la prueba a todos los destinatarios. Verifica la configuración SMTP.",
            "enviados": enviados,
            "fallidos": fallidos
        }), 502
    return jsonify({
        "success": True,
        "mensaje": f"Prueba enviada a {len(enviados)} destinatario(s).",
        "enviados": enviados
    })


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)