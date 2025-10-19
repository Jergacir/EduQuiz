from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql.cursors
from functools import wraps
from flask_bcrypt import Bcrypt
from extensions import bcrypt as bcrypt_ext
import sys
from dotenv import load_dotenv
import os
import random
import smtplib
import ssl
from email.message import EmailMessage
import requests
import cloudinary
import secrets
import hashlib
from datetime import datetime, timedelta
import string

# Importar utilidades compartidas (mask_email, envía verificación)
try:
    from utils import mask_email, send_verification_email
except Exception:
    # Si utils no está disponible en tiempo de import (durante refactor), ignoramos
    mask_email = lambda e: e
    send_verification_email = None

# Intentar importar el helper de restablecimiento (si existe)
try:
    from controllers.modificarcontrasena import send_password_reset_email
except Exception:
    send_password_reset_email = None

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = Flask(__name__)
app.secret_key = 'supersecreto123' # Importante para la autenticación
# Inicializar extensiones desde extensions.py
bcrypt_ext.init_app(app)
# para compatibilidad con el código existente, dejamos una referencia `bcrypt`
bcrypt = bcrypt_ext

# --- FUNCIÓN DE CONEXIÓN A LA BASE DE DATOS ---
def obtenerConexion():
    # Delegar la creación de conexión al módulo central `db.py` (dbmod)
    try:
        import db as dbmod
        return dbmod.obtenerConexion()
    except Exception as e:
        # Si algo falla al importar o al obtener la conexión, registrarlo y devolver None
        print(f"Error delegando obtenerConexion a dbmod: {e}", file=sys.stderr)
        return None


# ---------- ENDPOINTS PARA RECUPERACIÓN DE CONTRASEÑA ----------
try:
    from controllers.modificarcontrasena import (
        frm_solicitar_restablecer as ctrl_frm_solicitar_restablecer,
        solicitar_restablecer as ctrl_solicitar_restablecer,
        frm_restablecer as ctrl_frm_restablecer,
        restablecer_post as ctrl_restablecer_post,
    )
except Exception as e:
    print(f"[DEBUG] No se pudo importar controllers.modificarcontrasena: {e}")


@app.route('/solicitar_restablecer', methods=['GET'])
def frm_solicitar_restablecer():
    return ctrl_frm_solicitar_restablecer()


@app.route('/solicitar_restablecer', methods=['POST'])
def solicitar_restablecer():
    return ctrl_solicitar_restablecer()


@app.route('/restablecer', methods=['GET'])
def frm_restablecer():
    return ctrl_frm_restablecer()


@app.route('/restablecer', methods=['POST'])
def restablecer_post():
    return ctrl_restablecer_post()

# OBTENER DATOS DEL USUARIO LOGEADO
# ==============================================================================

def obtener_datos_usuario_logueado(usuario_id):
    """
    Obtiene todos los datos no sensibles del usuario actualmente logueado
    utilizando su ID de sesión.

    :param usuario_id: El ID del usuario almacenado en la sesión de Flask.
    :return: Un diccionario con los datos del usuario o None si no se encuentra.
    """
    conexion = obtenerConexion()
    if not conexion:
        return None

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # 🔑 CLAVE: La consulta es por un único ID usando el WHERE.
                sql = """
                    SELECT usuario_id, username, nombre, correo, tipo_usuario,
                           cant_monedas, dni, vigencia
                    FROM usuario
                    WHERE usuario_id = %s
                """
                # IMPORTANTE: Usar %s y una tupla para evitar inyección SQL
                cursor.execute(sql, (usuario_id,))
                usuario = cursor.fetchone()  # Solo se necesita un registro

                if usuario:
                    # Mapear el resultado de la base de datos a un diccionario
                    user_dict = {
                        'usuario_id': usuario.get('usuario_id'),
                        'username': usuario.get('username'),
                        'nombre': usuario.get('nombre'),
                        'correo': usuario.get('correo'),
                        'tipo_usuario': usuario.get('tipo_usuario'),
                        'cant_monedas': usuario.get('cant_monedas'),
                        'dni': usuario.get('dni'),
                        # Convertir 1/0 de la BD a booleano de Python
                        'vigencia': bool(usuario.get('vigencia')),
                    }
                    return user_dict
                else:
                    return None  # Usuario no encontrado
    except Exception as e:
        print(f"Error al obtener datos del usuario ID {usuario_id}: {e}", file=sys.stderr)
        return None

# RUTA DATOS DEL USUARIO LOGEADO
@app.route("/api/perfil", methods=["GET"])
def api_obtener_perfil():
    """
    Ruta API que devuelve los datos del usuario logueado en formato JSON.
    El frontend puede usar esta ruta vía Fetch/AJAX.
    """
    # 1. Verificar autenticación
    if 'user_id' not in session:
        # Devuelve un 401 Unauthorized si no hay sesión
        return jsonify({"error": "No autenticado"}), 401

    user_id = session['user_id']

    # 2. Obtener datos con la función existente
    datos_usuario = obtener_datos_usuario_logueado(user_id)

    if not datos_usuario:
        # Devuelve un 404 si el usuario no existe (aunque esté logueado)
        return jsonify({"error": "Usuario no encontrado"}), 404

    # 3. Devolver los datos como JSON
    return jsonify(datos_usuario), 200

# --- FUNCIÓN PARA OBTENER TODOS LOS USUARIOS DE LA BD (NUEVA IMPLEMENTACIÓN) ---
def obtener_todos_los_usuarios():
    """
    Obtiene todos los usuarios de la base de datos, incluyendo el nuevo campo 'vigencia'.
    """
    conexion = obtenerConexion()
    if not conexion:
        return []

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # 🔑 CLAVE: Asegurarse de que 'vigencia' esté incluido en el SELECT.
                sql = """
                    SELECT usuario_id, username, nombre, correo, tipo_usuario, cant_monedas, dni, vigencia
                    FROM usuario
                    ORDER BY usuario_id
                """
                cursor.execute(sql)
                usuarios = cursor.fetchall()

                # Convertir los resultados, asegurando que 'vigencia' se interprete como booleano para JSON
                lista_usuarios = []
                for user in usuarios:
                    user_dict = {
                        'usuario_id': user.get('usuario_id'),
                        'username': user.get('username'),
                        'nombre': user.get('nombre'),
                        'correo': user.get('correo'),
                        'tipo_usuario': user.get('tipo_usuario'),
                        'cant_monedas': user.get('cant_monedas'),
                        'dni': user.get('dni'),
                        # Convertir 1/0 de la BD a booleano de Python
                        'vigencia': bool(user.get('vigencia')),
                    }
                    lista_usuarios.append(user_dict)
                return lista_usuarios
    except Exception as e:
        print(f"Error en obtener_todos_los_usuarios: {e}", file=sys.stderr)
        return []


# --- DECORADORES DE AUTORIZACIÓN ---

# VERIFICACIÓN DE SESIÓN:
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Protección de la Ruta: Verifica si hay un user_id en la sesión
        if 'user_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página.", 'warning')
            return redirect(url_for('frm_login'))

        # Si el usuario está autenticado, ejecuta la función original
        return f(*args, **kwargs)
    return decorated_function

# RESTRINGIR ACCESO A GESTORES ('G'):
def gestor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar si está logueado
        if 'user_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página.", 'warning')
            return redirect(url_for('frm_login'))

        # 2. Obtener los datos del usuario (que ya contiene tipo_usuario gracias al context_processor)
        user_data = inject_user_data().get('logged_in_user')

        # 3. Verificar el tipo de usuario
        if not user_data or user_data.get('tipo_usuario') != 'G':
            flash("No tienes permiso para acceder a esta sección de administración.", 'error')
            return redirect(url_for('frm_home')) # Redirige al home si no es gestor

        return f(*args, **kwargs)
    return decorated_function

# RESTRINGIR ACCESO A profesores ('P'):
def profesor_required(f):
    @wraps(f)
    def function(*args, **kwargs):
        # 1. Verificar si está logueado
        if 'user_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página.", 'warning')
            return redirect(url_for('frm_login'))

        # 2. Obtener los datos del usuario (que ya contiene tipo_usuario gracias al context_processor)
        user_data = inject_user_data().get('logged_in_user')

        # 3. Verificar el tipo de usuario
        if not user_data or user_data.get('tipo_usuario') != 'P':
            flash("No tienes permiso para acceder a esta sección de profesor.", 'error')
            return redirect(url_for('frm_home')) # Redirige al home si no es gestor

        return f(*args, **kwargs)
    return function

# CONTIENE LOS DATOS DEL USUARIO AUTENTICADO
@app.context_processor
def inject_user_data():
    """
    Inyecta el diccionario 'logged_in_user' en el contexto de todas las plantillas.
    Contiene los datos del usuario autenticado.
    """
    if 'user_id' in session:
        user_id = session['user_id']
        conexion = obtenerConexion()

        if not conexion:
            return {} # Si no hay conexión, no inyecta datos.

        try:
            with conexion:
                with conexion.cursor() as cursor:
                    # Traemos 'tipo_usuario' para usarlo en el decorador 'gestor_required'
                    sql = "SELECT usuario_id,nombre, cant_monedas, tipo_usuario FROM usuario WHERE usuario_id=%s"
                    cursor.execute(sql, (user_id,))
                    user_data = cursor.fetchone()

            if user_data:
                # Retornamos el diccionario que se inyectará en las plantillas
                # Ahora incluye 'tipo_usuario'
                return dict(logged_in_user=user_data)
            else:
                # Limpiamos la sesión si el ID no es válido
                session.pop('user_id', None)
                return {}
        except Exception:
            return {} # Fallo de DB

    # Si el usuario no ha iniciado sesión, retorna vacío
    return {}

# --- RUTA DE RESULTADOS DE PARTIDA (PROFESOR) ---
@app.route('/resultados_partida/<int:partida_id>')
@login_required
@profesor_required
def frm_resultados_partida(partida_id):
    # Lógica: Consultar la base de datos usando partida_id para obtener:
    # 1. Información general de la partida (nombre, fecha).
    # 2. Lista de jugadores y sus puntajes/respuestas.

    # Datos de ejemplo (sustituir por la consulta a la DB)
    partida_info = {
        'nombre_cuestionario': 'Historia de México',
        'fecha': '2020-10-15',
        'jugadores_totales': 35,
        'modalidad': 'Individual',
        'cuestionario_id': 5,
        # Añade estas variables de análisis para el wireframe
        'acierto_promedio': '75%',
        'tiempo_promedio': '25 min',
        'participacion': '92%',
    }

    # IMPORTANTE: Se añadió 'avatar_url' a los datos de ejemplo
    resultados_jugadores = [
        {'nombre': 'Carlos M.', 'puntaje': 9500, 'avatar_url': '/static/img/avatar.jpeg'},
        {'nombre': 'Ana G.', 'puntaje': 8000, 'avatar_url': '/static/img/avatar.jpeg'},
        {'nombre': 'Luis R.', 'puntaje': 7500, 'avatar_url': '/static/img/avatar.jpeg'},
        {'nombre': 'Javier L.', 'puntaje': 6200, 'avatar_url': '/static/img/avatar.jpeg'},
        {'nombre': 'Maria C.', 'puntaje': 5800, 'avatar_url': '/static/img/avatar.jpeg'},
        {'nombre': 'Sofía P.', 'puntaje': 5000, 'avatar_url': '/static/img/avatar.jpeg'},
    ]

    # Opcional: Ordenar los resultados por puntaje (descendente)
    # resultados_jugadores.sort(key=lambda x: x['puntaje'], reverse=True)

    return render_template(
        'resultados_partida.html',
        partida_info=partida_info,
        resultados=resultados_jugadores,
        partida_id=partida_id
    )

@app.route('/exportar_resultados/<int:partida_id>')
@login_required
@profesor_required
def frm_exportar_resultados(partida_id):
    # Esto es solo para mostrar el nombre del cuestionario en la cabecera
    # En un caso real, harías una consulta a la DB
    partida_info = {
        'nombre_cuestionario': 'Cuestionario de Historia de México',
        'partida_id': partida_id
    }

    return render_template(
        'exportar_resultados.html',
        partida_id=partida_id,
        partida_info=partida_info
    )

# RUTA PARA EL PROCESO DE EXPORTACIÓN REAL (API)
@app.route('/api/exportar_partida/<int:partida_id>', methods=['POST'])
@login_required
@profesor_required
def api_exportar_partida(partida_id):
    data = request.json
    formato = data.get('formato')
    campos = data.get('campos') # Lista de campos seleccionados

    # --- Lógica de Exportación Real ---
    # 1. Obtener los datos de la partida y los campos seleccionados de la DB.
    # 2. Formatear los datos según el `formato` (CSV, Excel, PDF).
    # 3. Devolver la respuesta adecuada (por ejemplo, un archivo binario o un enlace de descarga).

    # Placeholder: En una implementación real, esto devolvería el archivo.
    print(f"Exportando partida #{partida_id} a {formato} con campos: {campos}")

    return jsonify({
        "status": "success",
        "mensaje": f"Exportación a {formato} iniciada. Se descargará pronto.",
        "download_url": "#" # Enlace de descarga real
    }), 200

# --- RUTAS DE NAVEGACIÓN ---

@app.route("/probarconexion")
def probarconexion():
    connection = obtenerConexion()
    if connection is None:
        return "<p>Error al conectar a la base de datos</p>"
    else:
        return "<p>Conexión exitosa</p>"

@app.route("/")
def frm_bienvenido():
    return render_template('bienvenido.html')

@app.route("/login")
def frm_login():
    return render_template('login.html')

@app.route("/registro")
def frm_registro():
    return render_template('registro.html')


@app.route('/verificar', methods=['GET'])
def frm_verificar():
    """Página para que el usuario ingrese el código de verificación que recibió por email.

    Acepta un parámetro `email` en la query string para prellenar el campo.
    """
    email = request.args.get('email', '')
    masked = mask_email(email) if email else ''
    return render_template('verificar.html', email=email, email_masked=masked)

@app.route("/home")
@login_required
def frm_home():
    return render_template('home.html')

# --- RUTA DE LA TIENDA ---

# --- RUTA DE PARTIDAS (PARA EL PROFESOR) ---
@app.route('/partidas_profesor')
@login_required
@profesor_required # Esta vista solo debe ser para profesores
def frm_partidas_profesor():
    # Aquí puedes cargar las partidas recientes del profesor
    # Por ahora, solo renderiza la plantilla.
    # Ejemplo:
    # partidas = obtener_partidas_del_profesor(session['user_id'])
    return render_template('partidas_profesor.html') # Asumiendo que partidas.html es ahora la vista del profesor

# --- RUTA PARA CREAR NUEVA PARTIDA (PARA EL PROFESOR) ---
@app.route('/crear_partida')
@login_required
@profesor_required # Solo accesible para profesores
def frm_crear_partida():
    # Esta ruta debería mostrar un formulario o una interfaz para
    # seleccionar un cuestionario y configurar la nueva partida.
    # Por ahora, puedes redirigir o mostrar un placeholder.
    flash("Aquí se creará una nueva partida (Vista en desarrollo)", 'info')
    return render_template('crear_partida.html') # O redirigir a una página de creación


# --- NUEVAS RUTAS DE PARTIDAS ---

    



# --- RUTAS API PARA CRUD DE TIENDA (Skins y Accesorios) ---

def obtener_items_crud(tabla, id_columna):
    """Función genérica para obtener todos los items de una tabla."""
    conexion = obtenerConexion()
    if not conexion:
        return []

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql = f"SELECT {id_columna} AS id, nombre,url_imagen, precio FROM {tabla}  WHERE vigencia = 1 ORDER BY {id_columna} ASC"
                cursor.execute(sql)
                items = cursor.fetchall()
                return items
    except Exception as e:
        print(f"Error al obtener items de la tabla {tabla}: {e}", file=sys.stderr)
        return []

@app.route('/api/tienda/accesorios', methods=['GET'])
@login_required
@gestor_required # Solo permite a Gestores ver la lista CRUD
def listar_accesorios_api():
    """Ruta API para devolver la lista completa de accesorios para el CRUD."""
    accesorios = obtener_items_crud('accesorios', 'accesorio_id')
    return jsonify(accesorios)

@app.route('/api/tienda/skins', methods=['GET'])
@login_required
@gestor_required # Solo permite a Gestores ver la lista CRUD
def listar_skins_api():
    """Ruta API para devolver la lista completa de skins para el CRUD."""
    skins = obtener_items_crud('skins', 'skin_id')
    return jsonify(skins)

#Estos son genéricos, sirven para estandarizar tanto skins como accesorios
def insertar_item(tabla, nombre, url_imagen, precio, id_columna):
    """
    Inserta un nuevo item (accesorio o skin) en la base de datos.
    Retorna True si la inserción fue exitosa, False en caso contrario.
    """
    conexion = obtenerConexion()
    if not conexion:
        return False, "Error de conexión a la base de datos."

    try:
        with conexion.cursor() as cursor:
            # La tabla y la columna ID se pasan como argumentos para hacer la función genérica
            sql = f"INSERT INTO `{tabla}` (`nombre`, `url_imagen`, `precio`) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, url_imagen, precio))
            conexion.commit()

            # Opcional: obtener el ID del item recién insertado
            nuevo_id = cursor.lastrowid

            return True, nuevo_id

    except Exception as e:
        print(f"Error al insertar en {tabla}: {e}", file=sys.stderr)
        return False, f"Error al insertar el ítem: {e}"


def actualizar_item(tabla, id_item, nombre, url_imagen, precio, columna_id):
    """
    Actualiza un item (accesorio o skin) existente en la base de datos.
    Requiere el ID del item para la cláusula WHERE.
    Retorna True si la actualización fue exitosa, False en caso contrario.
    """
    conexion = obtenerConexion()
    if not conexion:
        return False, "Error de conexión a la base de datos."

    try:
        with conexion.cursor() as cursor:
            # Construimos la consulta SQL usando el nombre de la tabla y la columna ID
            sql = f"""
                UPDATE `{tabla}`
                SET
                    `nombre` = %s,
                    `url_imagen` = %s,
                    `precio` = %s
                WHERE `{columna_id}` = %s
            """
            cursor.execute(sql, (nombre, url_imagen, precio, id_item))
            conexion.commit()

            if cursor.rowcount == 0:
                return False, "No se encontró el ítem para actualizar o los datos eran idénticos."

            return True, "Ítem actualizado exitosamente."

    except Exception as e:
        print(f"Error al actualizar en {tabla}: {e}", file=sys.stderr)
        return False, f"Error al actualizar el ítem: {e}"


def darbaja_item(tabla, id_item, vigencia, columna_id):
    """
    Marca un ítem (accesorio o skin) como inactivo (vigencia = 0 o False).
    Retorna True si la operación fue exitosa, False en caso contrario.
    """
    conexion = obtenerConexion()
    if not conexion:
        return False, "Error de conexión a la base de datos."

    try:
        with conexion.cursor() as cursor:
            sql = f"""
                UPDATE `{tabla}`
                SET `vigencia` = %s
                WHERE `{columna_id}` = %s
            """
            cursor.execute(sql, (vigencia, id_item))
            conexion.commit()

            if cursor.rowcount == 0:
                return False, "No se encontró el ítem para actualizar o los datos eran idénticos."

            return True, "Ítem dado de baja exitosamente."

    except Exception as e:
        print(f"Error al actualizar en {tabla}: {e}", file=sys.stderr)
        return False, f"Error al actualizar el ítem: {e}"

    finally:
        conexion.close()

def eliminar_item(tabla, id_item, columna_id):
    """
    Elimina un item (accesorio o skin) de la base de datos por su ID.
    Retorna True si la eliminación fue exitosa, False en caso contrario.
    """
    conexion = obtenerConexion()
    if not conexion:
        return False, "Error de conexión a la base de datos."

    try:
        with conexion.cursor() as cursor:
            # Construimos la consulta SQL usando el nombre de la tabla y la columna ID
            sql = f"DELETE FROM `{tabla}` WHERE `{columna_id}` = %s"
            cursor.execute(sql, (id_item,))
            conexion.commit()

            if cursor.rowcount == 0:
                return False, "No se encontró el ítem para eliminar."

            return True, "Ítem eliminado exitosamente."

    except Exception as e:
        print(f"Error al eliminar en {tabla}: {e}", file=sys.stderr)
        return False, f"Error al eliminar el ítem: {e}"


def obtener_item_por_id(tabla, id_item, columna_id):
    """
    Obtiene los detalles completos de un item por su ID.
    Retorna un diccionario con los datos o None si no se encuentra.
    """
    conexion = obtenerConexion()
    if not conexion:
        return None

    try:
        with conexion.cursor() as cursor:
            # Usamos %s para el nombre de la columna para la consulta, pero %s para el ID en el execute.
            # Nota: El nombre de la tabla y la columna ID DEBEN ser insertados directamente (f-string)
            # ya que no pueden ser placeholders (%s) en MySQL.
            sql = f"SELECT {columna_id} AS id, nombre, url_imagen, precio FROM `{tabla}` WHERE `{columna_id}` = %s"
            cursor.execute(sql, (id_item,))
            resultado = cursor.fetchone()
            return resultado

    except Exception as e:
        print(f"Error al obtener ítem por ID de {tabla}: {e}", file=sys.stderr)
        return None

    


# ... Esto es para el CRUD de accesorio

@app.route('/api/tienda/accesorios/crear', methods=['POST'])
@login_required
@gestor_required # Solo un gestor puede crear ítems
def crear_accesorio_api():
    """
    Ruta API para crear un nuevo accesorio.
    Recibe los datos del formulario (JSON o form-data) y los inserta en la BD.
    """
    # Preferimos leer de request.form porque el JS del frontend lo envía así.
    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    # 1. Validaciones
    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
             return jsonify({'success': False, 'message': 'El precio debe ser un número positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'El precio debe ser un número entero válido.'}), 400

    # 2. Inserción en BD
    # Usamos la nueva función genérica: tabla 'accesorios', columna ID 'accesorio_id'
    exito, resultado_o_error = insertar_item('accesorios', nombre, url_imagen, precio, 'accesorio_id')

    # 3. Respuesta
    if exito:
        return jsonify({
            'success': True,
            'message': 'Accesorio creado exitosamente.',
            'accesorio_id': resultado_o_error
        }), 201
    else:
        return jsonify({'success': False, 'message': resultado_o_error}), 500

@app.route('/api/tienda/accesorios/editar/<int:accesorio_id>', methods=['POST'])
@login_required
@gestor_required
def editar_accesorio_api(accesorio_id):
    """
    Ruta API para actualizar un accesorio existente.
    Recibe los datos del formulario (JSON o form-data) y el ID en la URL.
    """
    # Preferimos leer de request.form
    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    # 1. Validaciones
    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
             return jsonify({'success': False, 'message': 'El precio debe ser un número positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'El precio debe ser un número entero válido.'}), 400

    # 2. Actualización en BD
    exito, mensaje = actualizar_item('accesorios', accesorio_id, nombre, url_imagen, precio, 'accesorio_id')

    # 3. Respuesta
    if exito:
        return jsonify({
            'success': True,
            'message': mensaje,
            'accesorio_id': accesorio_id
        }), 200
    else:
        # 404 si no lo encuentra o 500 si es otro error de BD
        status_code = 404 if 'No se encontró el ítem' in mensaje else 500
        return jsonify({'success': False, 'message': mensaje}), status_code

@app.route('/api/tienda/accesorios/eliminar/<int:accesorio_id>', methods=['POST'])
@login_required
@gestor_required
def eliminar_accesorio_api(accesorio_id):
    """
    Ruta API para dar de baja (eliminación lógica) de un skin por su ID.
    """
    exito, mensaje = darbaja_item('accesorios', accesorio_id, False, 'accesorio_id')

    if exito:
        return jsonify({
            'success': True,
            'message': mensaje,
            'skin_id': accesorio_id
        }), 200
    else:
        status_code = 404 if 'No se encontró el ítem' in mensaje else 500
        return jsonify({'success': False, 'message': mensaje}), status_code

@app.route('/api/tienda/accesorios/<int:accesorio_id>', methods=['GET'])
@login_required
@gestor_required
def obtener_accesorio_api(accesorio_id):
    """
    Ruta API para obtener los detalles de un accesorio por su ID.
    """
    item = obtener_item_por_id('accesorios', accesorio_id, 'accesorio_id')

    if item:
        # Convertir el resultado a un diccionario serializable si es necesario
        return jsonify(item), 200
    else:
        return jsonify({'success': False, 'message': 'Accesorio no encontrado.'}), 404


# ... Esto es para el CRUD de skins

@app.route('/api/tienda/skin/crear', methods=['POST'])
@login_required
@gestor_required # Solo un gestor puede crear ítems
def crear_skin_api():
    """
    Ruta API para crear un nuevo accesorio.
    Recibe los datos del formulario (JSON o form-data) y los inserta en la BD.
    """
    # Preferimos leer de request.form porque el JS del frontend lo envía así.
    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    # 1. Validaciones
    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
             return jsonify({'success': False, 'message': 'El precio debe ser un número positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'El precio debe ser un número entero válido.'}), 400

    # 2. Inserción en BD
    # Usamos la nueva función genérica: tabla 'accesorios', columna ID 'accesorio_id'
    exito, resultado_o_error = insertar_item('skins', nombre, url_imagen, precio, 'skin_id')

    # 3. Respuesta
    if exito:
        return jsonify({
            'success': True,
            'message': 'Accesorio creado exitosamente.',
            'skin_id': resultado_o_error
        }), 201
    else:
        return jsonify({'success': False, 'message': resultado_o_error}), 500

@app.route('/api/tienda/skin/editar/<int:skin_id>', methods=['POST'])
@login_required
@gestor_required
def editar_skin_api(skin_id):
    """
    Ruta API para actualizar un accesorio existente.
    Recibe los datos del formulario (JSON o form-data) y el ID en la URL.
    """
    # Preferimos leer de request.form
    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    # 1. Validaciones
    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
             return jsonify({'success': False, 'message': 'El precio debe ser un número positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'El precio debe ser un número entero válido.'}), 400

    # 2. Actualización en BD
    exito, mensaje = actualizar_item('skins', skin_id, nombre, url_imagen, precio, 'skin_id')

    # 3. Respuesta
    if exito:
        return jsonify({
            'success': True,
            'message': mensaje,
            'skin_id': skin_id
        }), 200
    else:
        # 404 si no lo encuentra o 500 si es otro error de BD
        status_code = 404 if 'No se encontró el ítem' in mensaje else 500
        return jsonify({'success': False, 'message': mensaje}), status_code

@app.route('/api/tienda/skin/eliminar/<int:skin_id>', methods=['POST'])
@login_required
@gestor_required
def eliminar_skin_api(skin_id):
    """
    Ruta API para dar de baja (eliminación lógica) de un skin por su ID.
    """
    exito, mensaje = darbaja_item('skins', skin_id, False, 'skin_id')

    if exito:
        return jsonify({
            'success': True,
            'message': mensaje,
            'skin_id': skin_id
        }), 200
    else:
        status_code = 404 if 'No se encontró el ítem' in mensaje else 500
        return jsonify({'success': False, 'message': mensaje}), status_code



@app.route('/api/tienda/skin/<int:skin_id>', methods=['GET'])
@login_required
@gestor_required
def obtener_skin_api(skin_id):
    """
    Ruta API para obtener los detalles de un accesorio por su ID.
    """
    item = obtener_item_por_id('skins', skin_id, 'skin_id')

    if item:
        # Convertir el resultado a un diccionario serializable si es necesario
        return jsonify(item), 200
    else:
        return jsonify({'success': False, 'message': 'Accesorio no encontrado.'}), 404
# -----------------------------------


# ------------------------------------------------------------------
# Registrar blueprints modulares (controllers)
# ------------------------------------------------------------------
try:
    # Imports locales para evitar ciclos al migrar gradualmente
    from controllers.tienda import tienda_bp
    from controllers.usuarios import usuarios_bp
    from controllers.cuestionarios import cuestionarios_bp
    from controllers.auth import auth_bp
    from controllers.partidas import partidas_bp

    app.register_blueprint(tienda_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(cuestionarios_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(partidas_bp)
except Exception as e:
    # Si hay algún error al registrar (por ejemplo durante la refactorización), lo registramos
    print(f"[DEBUG] No se pudieron registrar todos los blueprints: {e}")


# --- BLOQUE api_unirse_partida MIGRADO ---
# Migrado a controllers/partidas.partidas_bp
# -----------------------------------

# RUTA HTML PARA EL CRUD DE USUARIOS
@app.route("/crud-usuarios")
@gestor_required  # Usa el decorador gestor_required para la página HTML
def crud_usuarios():
    return render_template('crudUsuario.html')

@app.route("/logout")
def logout():
    # Elimina el user_id de la sesión si existe
    session.pop('user_id', None)

    # Redirige al usuario a la página de login
    flash("Has cerrado sesión exitosamente.", 'success')
    return redirect(url_for('frm_login'))


@app.route("/errorsistema")
def frm_error():
    return render_template('errorsistema.html')

# Ruta para procesar el registro de usuario (CON ENCRIPTACIÓN BCrypt)
@app.route("/procesarregistro", methods=['POST'])
def procesarregistro():
    tipo = request.form.get('tipo')
    dni = request.form.get('dni')
    email = request.form.get('email')
    contrasena_plana = request.form.get('contrasena') # Contraseña en texto plano
    confirmar = request.form.get('confirmarContrasena')

    # DEBUG: imprimir datos recibidos (no imprimir contraseñas en producción)
    print(f"[DEBUG] procesarregistro recibidos -> tipo: {tipo}, dni: {dni}, email: {email}")

    # Validaciones básicas de formulario
    if not tipo or not dni or not email or not contrasena_plana or not confirmar:
        flash("Faltan campos obligatorios.", 'error')
        return redirect(url_for('frm_registro'))

    if len(dni) != 8 or not dni.isdigit():
        flash("DNI inválido. Debe contener 8 dígitos.", 'error')
        return redirect(url_for('frm_registro'))

    if contrasena_plana != confirmar:
        flash("Las contraseñas no coinciden.", 'error')
        return redirect(url_for('frm_registro'))

    # --- Validación de contraseña fuerte (servidor) ---
    # Requisitos: mínimo 8 caracteres, al menos una mayúscula, una minúscula,
    # al menos un dígito y al menos un carácter especial.
    import re
    pwd = contrasena_plana
    pwd_errors = []
    if len(pwd) < 8:
        pwd_errors.append('al menos 8 caracteres')
    if not re.search(r'[A-Z]', pwd):
        pwd_errors.append('una letra mayúscula')
    if not re.search(r'[a-z]', pwd):
        pwd_errors.append('una letra minúscula')
    if not re.search(r'\d', pwd):
        pwd_errors.append('un número')
    if not re.search(r'[!@#$%^&*()_+\-=[\]{};:\\"\\|,.<>\/?`~]', pwd):
        pwd_errors.append('un carácter especial (ej: !@#$%)')

    if pwd_errors:
        # Construir mensaje legible para el usuario
        detalles = ', '.join(pwd_errors)
        flash(f"La contraseña es débil. Debe contener: {detalles}.", 'error')
        return redirect(url_for('frm_registro'))

    # Ajustar dominio de correo y definir tipo_usuario para la DB
    tipo_usuario = None
    if tipo == "Docente":
        if not email.endswith('@usat.edu.pe'):
             email = f"{email}@usat.edu.pe"
        tipo_usuario = 'P'
    elif tipo == "Alumno":
        if not email.endswith('@usat.pe'):
             email = f"{dni}@usat.pe"
        tipo_usuario = 'A'
    else:
        flash("Tipo de usuario inválido.", 'error')
        return redirect(url_for('frm_registro'))

    # Cifrar la contraseña
    hashed_password_bytes = bcrypt.generate_password_hash(contrasena_plana)
    contrasena_cifrada = hashed_password_bytes.decode('utf-8')

    # Generar username y nombre a partir del correo
    username = email.split('@')[0]
    nombre = username.replace('_', ' ').title()

    # Generar código de verificación de 6 dígitos
    verification_code = ''.join(str(random.randint(0,9)) for _ in range(6))

    # Intentar conexión
    conexion = obtenerConexion()
    if not conexion:
        print("No se pudo conectar a la base de datos")
        return redirect(url_for('frm_error'))

    try:
        # Guardar en tabla temporal registro_temp en vez de insertar inmediatamente en usuario
        with conexion:
            with conexion.cursor() as cursor:
                # Validar si ya existe usuario con mismo correo o dni en la tabla definitiva
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s"
                cursor.execute(sql_check, (email, dni))
                existe = cursor.fetchone()
                if existe:
                    flash("El DNI o correo ya está registrado.", 'error')
                    return redirect(url_for('frm_registro'))

                # Verificar si ya existe un registro temporal para este correo
                sql_temp = "SELECT temp_id FROM registro_temp WHERE correo=%s"
                cursor.execute(sql_temp, (email,))
                temp_row = cursor.fetchone()

                if temp_row:
                    # Actualizar código y datos (por si cambió algo)
                    sql_update = """
                        UPDATE registro_temp
                        SET username=%s, nombre=%s, contrasena=%s, dni=%s, tipo_usuario=%s, cant_monedas=%s, verification_code=%s, created_at=CURRENT_TIMESTAMP
                        WHERE temp_id=%s
                    """
                    cursor.execute(sql_update, (username, nombre, contrasena_cifrada, dni, tipo_usuario, 0, verification_code, temp_row['temp_id']))
                else:
                    # Insertar nuevo registro temporal
                    sql_insert_temp = """
                        INSERT INTO registro_temp
                            (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verification_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert_temp, (username, nombre, contrasena_cifrada, email, dni, tipo_usuario, 0, verification_code))

                conexion.commit()

        # DEBUG: imprimir el código en consola (solo en entorno de desarrollo)
        print(f"[DEBUG] Código de verificación generado para {email}: {verification_code}")

        # Intentar enviar el correo de verificación
        try:
            send_verification_email(email, verification_code)
            flash('Se envió un código de verificación a tu correo.', 'info')
        except Exception as e:
            print(f"Error enviando email: {e}")
            flash('No se pudo enviar el correo de verificación automáticamente. Contacta al administrador.', 'warning')

        # Mostrar la pantalla de verificación para que el usuario ingrese el código
        masked = mask_email(email)
        return render_template('verificar.html', email=email, email_masked=masked)

    except pymysql.err.IntegrityError:
        flash("Error de registro: El usuario ya existe o hay un problema con los datos.", 'error')
        return redirect(url_for('frm_registro'))

    except Exception as e:
        flash("Ocurrió un error en el sistema.", 'error')
        print(f"Error en el registro (sistema): {e}")
        return redirect(url_for('frm_error'))


# --- RUTA API PARA LISTAR USUARIOS (CONSUMIDA POR crudusuario.js) ---
@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios_api():
    """
    Ruta API para devolver la lista completa de usuarios.
    Verifica los permisos antes de consultar la BD.
    """
    # 1. Verificar autenticación
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado. Debes iniciar sesión.'}), 401

    user_id = session['user_id']

    # 2. Verificar si el usuario actual es un Gestor ('G')
    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'error': 'Error de conexión a la base de datos.'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Consulta directa para verificar el rol del usuario logueado
                sql_check_role = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
                cursor.execute(sql_check_role, (user_id,))
                user_role_data = cursor.fetchone()

                if not user_role_data or user_role_data.get('tipo_usuario') != 'G':
                    # Devolver un error 403 (Prohibido) si no tiene permiso de Gestor
                    return jsonify({'error': 'Acceso prohibido. No tienes permisos de administrador.'}), 403

        # 3. Si el rol es 'G', procede a obtener la lista completa de usuarios
        usuarios = obtener_todos_los_usuarios()

        return jsonify(usuarios)

    except Exception as e:
        print(f"Error al obtener usuarios: {e}", file=sys.stderr)
        return jsonify({'error': 'Error interno del servidor al obtener datos'}), 500

    


# Ruta para procesar el Login (CON VERIFICACIÓN BCrypt y VIGENCIA)
@app.route("/procesarlogin", methods=['POST'])
def procesarlogin():
    correo = request.form['correo']
    contrasena_plana = request.form['contrasena'] # Contraseña en texto plano
    conexion = obtenerConexion()

    if not conexion:
        print("No se pudo conectar a la base de datos (login)")
        return redirect(url_for('frm_error'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # 🔑 CAMBIO CLAVE: Solicitamos también el campo `vigencia`
                sql = "SELECT `usuario_id`, `contrasena`, `verificado`, `correo`, `vigencia` FROM `usuario` WHERE `correo`=%s"
                cursor.execute(sql, (correo,))
                result = cursor.fetchone()

            # Verificación
            if result:
                hashed_password = result['contrasena']
                verificado = result.get('verificado', 0)
                vigencia = result.get('vigencia', 0) # 🔑 Obtenemos el estado de vigencia (1=Vigente, 0=No Vigente)

                # 1. Verificar la contraseña
                if bcrypt.check_password_hash(hashed_password, contrasena_plana):

                    # 🔑 2. VERIFICAR VIGENCIA
                    if vigencia == 0:
                        flash('Tu cuenta ha sido dada de baja o se encuentra inactiva. Contacta con soporte.', 'error')
                        return redirect(url_for('frm_login'))

                    # 3. Verificar si necesita activación por correo
                    if verificado == 0:
                        # Cuenta no verificada: pedir código
                        flash('Tu cuenta aún no está verificada. Ingresa el código enviado a tu correo.', 'warning')
                        correo_val = result.get('correo')
                        return render_template('verificar.html', email=correo_val, email_masked=mask_email(correo_val or ''))

                    # 4. Login Exitoso (Contraseña correcta, Vigente y Verificado)
                    session['user_id'] = result['usuario_id']
                    return redirect(url_for('frm_home'))

                else:
                    # Contraseña incorrecta
                    flash("Credenciales incorrectas. Verifica tu correo y contraseña.", 'error')
                    return redirect(url_for('frm_login'))
            else:
                # El correo no existe
                flash("Credenciales incorrectas. Verifica tu correo y contraseña.", 'error')
                return redirect(url_for('frm_login'))

    except Exception as e:
        print(f"Error en el login: {e}")
        return redirect(url_for('frm_error'))


@app.route('/procesar_verificacion', methods=['POST'])
def procesar_verificacion():
    data = request.get_json(silent=True)
    if data:
        email = data.get('email')
        codigo = data.get('codigo')
        nombre_reniec = data.get('nombre_reniec')  # nombre real desde el front
    else:
        email = request.form.get('email')
        codigo = request.form.get('codigo')
        nombre_reniec = request.form.get('nombre_reniec')

    # 🔍 DEBUG: ver qué llega desde el front
    print("=== [DEBUG procesar_verificacion] ===")
    print(f"Email recibido: {email}")
    print(f"Nombre RENIEC recibido: {nombre_reniec}")
    print("===================================")

    if not email or not codigo:
        if data:
            return jsonify({'success': False, 'message': 'Faltan datos para verificar la cuenta.'}), 400
        flash('Faltan datos para verificar la cuenta.', 'error')
        return redirect(url_for('frm_registro'))

    conexion = obtenerConexion()
    if not conexion:
        return redirect(url_for('frm_error'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Buscar en la tabla temporal
                sql_temp = "SELECT * FROM registro_temp WHERE correo=%s"
                cursor.execute(sql_temp, (email,))
                temp = cursor.fetchone()

                if not temp:
                    # Verificar si ya está en la tabla usuario
                    cursor.execute("SELECT usuario_id, verificado FROM usuario WHERE correo=%s", (email,))
                    user_row = cursor.fetchone()
                    if user_row and user_row.get('verificado') == 1:
                        if data:
                            return jsonify({'success': False, 'message': 'Cuenta ya verificada. Puedes iniciar sesión.'}), 200
                        flash('Cuenta ya verificada. Puedes iniciar sesión.', 'info')
                        return redirect(url_for('frm_login'))

                    if data:
                        return jsonify({'success': False, 'message': 'Correo no encontrado en el registro temporal. Vuelve a registrarte.'}), 404
                    flash('Correo no encontrado en el registro temporal. Vuelve a registrarte.', 'error')
                    return redirect(url_for('frm_registro'))

                # Comparar código
                if temp.get('verification_code') == codigo:
                    dni = temp.get('dni')

                    # 🟢 Priorizar nombre real del RENIEC si vino desde el frontend
                    if nombre_reniec and len(nombre_reniec.strip()) > 0:
                        nombre_final = nombre_reniec.strip()
                        print(f"[DEBUG] ✅ Usando nombre RENIEC: {nombre_final}")
                    else:
                        nombre_final = temp.get('nombre')
                        if nombre_final and nombre_final.strip() == dni:
                            print("[DEBUG] 🚫 El nombre temporal es igual al DNI, dejando vacío.")
                            nombre_final = "(Sin nombre RENIEC)"
                        else:
                            print(f"[DEBUG] ⚙️ Usando nombre temporal: {nombre_final}")

                    # Insertar en tabla usuario
                    insert_sql = """
                        INSERT INTO usuario (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        temp['username'], nombre_final, temp['contrasena'],
                        temp['correo'], temp['dni'], temp['tipo_usuario'],
                        temp['cant_monedas'], 1
                    ))

                    # Borrar registro temporal
                    cursor.execute("DELETE FROM registro_temp WHERE temp_id=%s", (temp['temp_id'],))
                    conexion.commit()

                    if data:
                        return jsonify({
                            'success': True,
                            'message': 'Registro completado correctamente.',
                            'dni': dni,
                            'nombre': nombre_final
                        }), 200

                    flash('Registro completado correctamente. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('frm_login'))

                else:
                    if data:
                        return jsonify({'success': False, 'message': 'Código incorrecto. Intenta de nuevo.'}), 400
                    flash('Código incorrecto. Intenta de nuevo.', 'error')
                    return render_template('verificar.html', email=email, email_masked=mask_email(email))

    except Exception as e:
        print(f"❌ Error al verificar cuenta: {e}")
        if data:
            return jsonify({'success': False, 'message': 'Error interno del servidor.'}), 500
        return redirect(url_for('frm_error'))

@app.route('/api/get_dni', methods=['GET'])
def get_dni():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email requerido"}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"error": "No hay conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT dni FROM registro_temp WHERE correo=%s", (email,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Registro temporal no encontrado"}), 404
            return jsonify({"dni": row.get("dni")})
    except Exception as e:
        return jsonify({"error": "Error interno", "detail": str(e)}), 500

@app.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    data = request.get_json(silent=True)
    if data:
        email = data.get('email')
    else:
        email = request.form.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Falta el email'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Buscar en registro_temp primero
                cursor.execute("SELECT temp_id FROM registro_temp WHERE correo=%s", (email,))
                temp = cursor.fetchone()
                if temp:
                    new_code = ''.join(str(random.randint(0,9)) for _ in range(6))
                    cursor.execute("UPDATE registro_temp SET verification_code=%s, created_at=CURRENT_TIMESTAMP WHERE temp_id=%s", (new_code, temp['temp_id']))
                    conexion.commit()
                    try:
                        send_verification_email(email, new_code)
                    except Exception as e:
                        print(f"Error reenviando email a temp: {e}")
                        return jsonify({'success': False, 'message': 'No se pudo enviar el correo.'}), 500
                    return jsonify({'success': True, 'message': 'Código reenviado.', 'email_masked': mask_email(email)}), 200

                # Si no hay registro temporal, intentar con la tabla definitiva
                cursor.execute("SELECT usuario_id, username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado FROM usuario WHERE correo=%s", (email,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({'success': False, 'message': 'Email no encontrado'}), 404

                if row.get('verificado') == 1:
                    return jsonify({'success': False, 'message': 'Cuenta ya verificada.'}), 400

                # Crear o actualizar un registro temporal a partir de los datos del usuario
                new_code = ''.join(str(random.randint(0,9)) for _ in range(6))

                # Intentamos encontrar si ya existe un registro_temp por correo (por seguridad)
                cursor.execute("SELECT temp_id FROM registro_temp WHERE correo=%s", (email,))
                existing_temp = cursor.fetchone()
                if existing_temp:
                    cursor.execute("UPDATE registro_temp SET verification_code=%s, created_at=CURRENT_TIMESTAMP WHERE temp_id=%s", (new_code, existing_temp['temp_id']))
                else:
                    # Insertar una fila temporal con los datos actuales del usuario
                    insert_temp = """
                        INSERT INTO registro_temp (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verification_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_temp, (
                        row['username'], row['nombre'], row['contrasena'], row['correo'], row['dni'], row['tipo_usuario'], row.get('cant_monedas', 0), new_code
                    ))

                conexion.commit()
                try:
                    send_verification_email(email, new_code)
                except Exception as e:
                    print(f"Error reenviando email a temp (desde usuario): {e}")
                    return jsonify({'success': False, 'message': 'No se pudo enviar el correo.'}), 500
                return jsonify({'success': True, 'message': 'Código reenviado.', 'email_masked': mask_email(email)}), 200

    except Exception as e:
        print(f"Error en reenviar_codigo: {e}")
        return jsonify({'success': False, 'message': 'Error interno.'}), 500

# --- Apartado para cuestionarios ---
@app.route("/cuestionario")
@login_required
def frm_cuestionarios():
    return render_template('cuestionario.html')



@app.route("/crearcuestionario")
@login_required
def frm_editarcuestionarios():
    return render_template('crearcuestionario.html')





# =========================================================
# --- CRUD DE CUESTIONARIOS ---
# =========================================================

@app.route('/api/cuestionarios/<int:usuario_id>', methods=['GET'])
def listar_cuestionarios(usuario_id):
    """
    Devuelve todos los cuestionarios de un usuario con cantidad de preguntas.
    """
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas
            FROM cuestionario c
            WHERE c.usuario_id = %s and estado=1
        """, (usuario_id,))
        data = cursor.fetchall()
    return jsonify(data)

@app.route('/api/cuestionarios_publicos', methods=['GET'])
def listar_cuestionarios_publicos():
    """
    Devuelve todos los cuestionarios públicos (visibles para alumnos).
    """
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas
            FROM cuestionario c
            WHERE c.publico = 1 AND c.estado = 1
        """)
        data = cursor.fetchall()
    return jsonify(data)

@app.route('/api/cuestionarios/<int:cuestionario_id>', methods=['PUT'])
def eliminar_cuestionario(cuestionario_id):
    """
    Elimina un cuestionario y en cascada sus preguntas y respuestas.
    """
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("UPDATE cuestionario set estado=0 WHERE cuestionario_id=%s", (cuestionario_id,))
        conexion.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Cuestionario eliminado lógicamente'})

def generar_codigo_unico(cursor):
    """Genera un código aleatorio de 6 letras no repetido en la base de datos."""
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase, k=6))
        cursor.execute("SELECT 1 FROM cuestionario WHERE codigo_visualizacion = %s", (codigo,))
        if cursor.fetchone() is None:
            return codigo


#---Esto lo usaremos en el crear cuestionario---
@app.route("/api/cuestionario_completo", methods=["POST"])
def crear_cuestionario_completo():
    """
    Crea un cuestionario con sus preguntas y respuestas en una sola transacción.
    Espera un JSON con la estructura completa.
    """
    data = request.get_json()

    # Validación básica
    if not data or "nombre_cuestionario" not in data or "preguntas" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:

                # --- Generar código de visualización único ---
                codigo_visualizacion = generar_codigo_unico(cursor)

                # --- Subir imagen del cuestionario a Cloudinary si existe ---
                url_img_cuestionario_cloud = data.get("url_img_cuestionario") or "https://img.freepik.com/vector-premium/imagen-no-es-conjunto-iconos-disponibles-simbolo-vectorial-stock-fotos-faltante-defecto-estilo-relleno-delineado-negro-signo-no-encontro-imagen_268104-6708.jpg"
                # --- Crear el cuestionario ---
                sql_cuestionario = """
                    INSERT INTO cuestionario
                    (nombre_cuestionario, descripcion, publico, modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario, codigo_visualizacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_cuestionario, (
                    data.get("nombre_cuestionario"),
                    data.get("descripcion"),
                    data.get("publico", 0),
                    data.get("modo_juego", "C"),
                    data.get("tiempo_limite_pregunta", 30),
                    data.get("usuario_id"),
                    url_img_cuestionario_cloud,
                    codigo_visualizacion
                ))
                cuestionario_id = cursor.lastrowid

                # Crear las preguntas y sus respuestas
                for pregunta in data["preguntas"]:
                    sql_pregunta = """
                        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                        VALUES (%s, %s, %s, %s)
                    """
                    # Subir imagen a Cloudinary si existe
                    media_url = pregunta.get("media_url")

                    # Insertar pregunta usando la URL de Cloudinary
                    cursor.execute(sql_pregunta, (
                        pregunta.get("texto_pregunta"),
                        media_url,
                        pregunta.get("tiempo_limite"),
                        cuestionario_id
                    ))
                    pregunta_id = cursor.lastrowid

                    # Insertar respuestas
                    for resp in pregunta.get("respuestas", []):
                        sql_respuesta = """
                            INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id)
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(sql_respuesta, (
                            resp.get("texto_respuesta"),
                            resp.get("estado_respuesta", 0),
                            pregunta_id
                        ))

                # Confirmar toda la transacción
                conexion.commit()

        return jsonify({
            "mensaje": "Cuestionario completo creado exitosamente",
            "cuestionario_id": cuestionario_id,
            "codigo_visualizacion": codigo_visualizacion
        }), 201

    except Exception as e:
        print("Error al crear cuestionario completo:", e, file=sys.stderr)
        conexion.rollback()
        return jsonify({"error": str(e)}), 500



@app.route("/api/cuestionario_completo/<int:cuestionario_id>", methods=["GET"])
def obtener_cuestionario_completo(cuestionario_id):
    """
    Devuelve un cuestionario completo con sus preguntas y respuestas.
    """
    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        with conexion.cursor() as cursor:
            # --- Obtener cuestionario ---
            sql_cuestionario = """
                SELECT cuestionario_id, nombre_cuestionario, descripcion, publico,
                       modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario, codigo_visualizacion
                FROM cuestionario
                WHERE cuestionario_id = %s
            """
            cursor.execute(sql_cuestionario, (cuestionario_id,))
            cuestionario = cursor.fetchone()
            if not cuestionario:
                return jsonify({"error": "Cuestionario no encontrado"}), 404

            # --- Obtener preguntas ---
            sql_preguntas = """
                SELECT pregunta_id, texto_pregunta, media_url, tiempo_limite
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id ASC
            """
            cursor.execute(sql_preguntas, (cuestionario_id,))
            preguntas = cursor.fetchall()

            # --- Obtener respuestas de cada pregunta ---
            for pregunta in preguntas:
                sql_respuestas = """
                    SELECT respuesta_id, texto_respuesta, estado_respuesta
                    FROM respuesta
                    WHERE pregunta_id = %s
                    ORDER BY respuesta_id ASC
                """
                cursor.execute(sql_respuestas, (pregunta["pregunta_id"],))
                respuestas = cursor.fetchall()

                # Agregar índice de la respuesta correcta
                correcta_idx = next((i for i, r in enumerate(respuestas) if r['estado_respuesta'] == 1), 0)

                # Añadir lista de respuestas y correcta
                pregunta["respuestas"] = respuestas
                pregunta["correcta"] = correcta_idx

            # --- Estructura final ---
            cuestionario["preguntas"] = preguntas

        return jsonify(cuestionario), 200

    except Exception as e:
        print("Error al obtener cuestionario completo:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/cuestionario_completo/<int:cuestionario_id>", methods=["PUT"])
def actualizar_cuestionario_completo(cuestionario_id):
    """
    Actualiza un cuestionario completo. Se borran preguntas y respuestas previas
    y se insertan las nuevas.
    """
    data = request.get_json()

    if not data or "nombre_cuestionario" not in data or "preguntas" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # --- Subir imagen del cuestionario a Cloudinary si existe ---
                url_img_cuestionario_cloud = data.get("url_img_cuestionario") or "https://img.freepik.com/vector-premium/imagen-no-es-conjunto-iconos-disponibles-simbolo-vectorial-stock-fotos-faltante-defecto-estilo-relleno-delineado-negro-signo-no-encontro-imagen_268104-6708.jpg"

                # --- Actualizar datos generales del cuestionario ---
                sql_update_cuestionario = """
                    UPDATE cuestionario
                    SET nombre_cuestionario=%s,
                        descripcion=%s,
                        publico=%s,
                        modo_juego=%s,
                        tiempo_limite_pregunta=%s,
                        url_img_cuestionario=%s
                    WHERE cuestionario_id=%s
                """
                cursor.execute(sql_update_cuestionario, (
                    data.get("nombre_cuestionario"),
                    data.get("descripcion"),
                    data.get("publico", 0),
                    data.get("modo_juego", "C"),
                    data.get("tiempo_limite_pregunta", 30),
                    url_img_cuestionario_cloud,
                    cuestionario_id
                ))

                # --- Eliminar preguntas y respuestas existentes ---
                cursor.execute("DELETE FROM respuesta WHERE pregunta_id IN (SELECT pregunta_id FROM pregunta WHERE cuestionario_id=%s)", (cuestionario_id,))
                cursor.execute("DELETE FROM pregunta WHERE cuestionario_id=%s", (cuestionario_id,))

                # --- Insertar nuevas preguntas y respuestas ---
                for pregunta in data["preguntas"]:
                    # Subir imagen de la pregunta si existe
                    media_url = pregunta.get("media_url")

                    sql_insert_pregunta = """
                        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert_pregunta, (
                        pregunta.get("texto_pregunta"),
                        media_url,
                        pregunta.get("tiempo_limite"),
                        cuestionario_id
                    ))
                    pregunta_id = cursor.lastrowid

                    for resp in pregunta.get("respuestas", []):
                        sql_insert_respuesta = """
                            INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id)
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(sql_insert_respuesta, (
                            resp.get("texto_respuesta"),
                            resp.get("estado_respuesta", 0),
                            pregunta_id
                        ))

                conexion.commit()

        return jsonify({"mensaje": "Cuestionario actualizado exitosamente"}), 200

    except Exception as e:
        print("Error al actualizar cuestionario completo:", e, file=sys.stderr)
        conexion.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/verificar_codigo/<int:cuestionario_id>", methods=["POST"])
def verificar_codigo(cuestionario_id):
    """
    Verifica si el código de visualización ingresado por el alumno
    coincide con el del cuestionario.
    """
    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"valido": False, "mensaje": "No se pudo conectar a la base de datos"}), 500

    try:
        data = request.get_json()
        codigo_ingresado = (data.get("codigo") or "").strip()

        if not codigo_ingresado:
            return jsonify({"valido": False, "mensaje": "Código vacío"}), 400

        with conexion.cursor() as cursor:
            # --- Obtener el código real del cuestionario ---
            sql = """
                SELECT codigo_visualizacion
                FROM cuestionario
                WHERE cuestionario_id = %s AND estado = 1
            """
            cursor.execute(sql, (cuestionario_id,))
            resultado = cursor.fetchone()

            if not resultado:
                return jsonify({"valido": False, "mensaje": "Cuestionario no encontrado"}), 404

            codigo_real = resultado["codigo_visualizacion"]

            # --- Comparar códigos ---
            if codigo_real == codigo_ingresado:
                return jsonify({"valido": True}), 200
            else:
                return jsonify({"valido": False, "mensaje": "Código incorrecto"}), 200

    except Exception as e:
        print("Error al verificar código:", e)
        return jsonify({"valido": False, "mensaje": "Error interno del servidor"}), 500

    finally:
        conexion.close()


@app.route("/editar_cuestionario/<int:cuestionario_id>")
@login_required
def frm_edicioncuestionario(cuestionario_id):
    # Solo pasamos cuestionario_id; logged_in_user ya estará disponible en el template
    return render_template('editarcuestionario.html', cuestionario_id=cuestionario_id)

@app.route("/ver_cuestionario/<int:cuestionario_id>")
@login_required
def frm_ver_cuestionario(cuestionario_id):
    # Aquí podrías cargar los datos del cuestionario desde la base de datos
    # Por ejemplo:
    # cuestionario = obtener_cuestionario(cuestionario_id)

    return render_template('visualizarCuestionario.html', cuestionario_id=cuestionario_id)