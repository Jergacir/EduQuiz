from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql.cursors
from functools import wraps
from flask_bcrypt import Bcrypt 
import sys 
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader  # <-- importante
import cloudinary.api 
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = Flask(__name__)
app.secret_key = 'supersecreto123' # Importante para la autenticación
#IMPORTANTE: cambiar el puerto porfavor
bcrypt = Bcrypt(app) # Inicializar Bcrypt con tu aplicación Flask

# --- FUNCIÓN DE CONEXIÓN A LA BASE DE DATOS ---
def obtenerConexion():
    try:
        connection = pymysql.connect(host='localhost',
                                     port=3339, 
                                     user='root',
                                     password='',
                                     database='bd_eduquiz',
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except Exception as e:
        # Se imprime el error en la salida de errores
        print("Error al obtener la conexión: %s" % (repr(e)), file=sys.stderr)
        return None

# --- FUNCIÓN PARA OBTENER TODOS LOS USUARIOS DE LA BD (NUEVA IMPLEMENTACIÓN) ---
def obtener_todos_los_usuarios():
    """
    Consulta la base de datos y devuelve una lista de todos los usuarios
    con los campos necesarios para el CRUD (excluyendo la contraseña).
    """
    conexion = obtenerConexion()
    if not conexion:
        return []

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Selecciona solo los campos necesarios y seguros para mostrar en el CRUD
                sql = "SELECT usuario_id, username, nombre, correo, tipo_usuario, cant_monedas FROM usuario"
                cursor.execute(sql)
                # Debido a DictCursor, esto ya retorna una lista de diccionarios
                usuarios = cursor.fetchall() 
                return usuarios
    except Exception as e:
        print(f"Error al obtener usuarios de la BD: {e}", file=sys.stderr)
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

@app.route("/home")
@login_required
def frm_home():
    return render_template('home.html')

# --- RUTA DE LA TIENDA ---
@app.route("/tienda")
@login_required
def frm_tienda():
    # Inicializamos las listas en caso de que haya un error
    lista_skins = []
    lista_accesorios = []
    
    # 1. Obtenemos la conexión a la BD
    conexion = obtenerConexion()
    if conexion:
        try:
            with conexion.cursor() as cursor:
                # 2. Consultamos todos los skins
                sql_skins = "SELECT skin_id, nombre, url_imagen, precio FROM skins WHERE vigencia = 1  ORDER BY precio ASC"
                cursor.execute(sql_skins)
                lista_skins = cursor.fetchall()
                
                # 3. Consultamos todos los accesorios
                sql_accesorios = "SELECT accesorio_id, nombre, url_imagen, precio FROM accesorios WHERE vigencia = 1 ORDER BY precio ASC"
                cursor.execute(sql_accesorios)
                lista_accesorios = cursor.fetchall()
        except Exception as e:
            print(f"Error al consultar la tienda: {e}")
        finally:
            # La conexión se cierra automáticamente gracias al 'with'
            pass
            
    # 4. Pasamos las listas a la plantilla HTML
    return render_template('tienda.html', skins=lista_skins, accesorios=lista_accesorios)

# --- RUTAS API PARA CRUD DE TIENDA (Skins y Accesorios) ---

def obtener_items_crud(tabla, id_columna):
    """Función genérica para obtener todos los items de una tabla."""
    conexion = obtenerConexion()
    if not conexion:
        return []

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql = f"SELECT {id_columna} AS id, nombre, precio FROM {tabla}  WHERE vigencia = 1 ORDER BY {id_columna} ASC"
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

    # Intentar conexión
    conexion = obtenerConexion()
    if not conexion:
        print("No se pudo conectar a la base de datos")
        return redirect(url_for('frm_error')) 

    try:
        with conexion: 
            with conexion.cursor() as cursor:
                # Validar si ya existe usuario con mismo correo o dni
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s"
                cursor.execute(sql_check, (email, dni))
                existe = cursor.fetchone()
                if existe:
                    flash("El DNI o correo ya está registrado.", 'error')
                    return redirect(url_for('frm_registro'))

                # Insertar nuevo usuario
                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                
                # Usar la contraseña CIFRADA en la inserción
                cursor.execute(sql, (username, nombre, contrasena_cifrada, email, dni, tipo_usuario, 0))
                conexion.commit()

        flash("Registro exitoso. ¡Ya puedes iniciar sesión!", 'success')
        return redirect(url_for('frm_login'))

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

# Registrar GESTORES/ADMINISTRADORES
# ==================================
@app.route("/api/register-gestor", methods=['POST'])
def register_gestor_api():
    """
    Registra un usuario de tipo 'G' (Gestor) de forma segura.
    Esta ruta está diseñada para ser llamada por herramientas como Postman o cURL 
    en lugar de un formulario web.
    """
    # Usar request.get_json() para leer el cuerpo de la petición como JSON
    data = request.get_json()

    if not data or any(key not in data for key in ['username', 'nombre', 'contrasena', 'correo', 'dni']):
        return jsonify({"success": False, "message": "Faltan campos obligatorios: username, nombre, contrasena, correo, dni."}), 400

    username = data['username']
    nombre = data['nombre']
    contrasena_plana = data['contrasena']
    correo = data['correo']
    dni = data['dni']
    
    # Validaciones básicas
    if len(dni) != 8 or not dni.isdigit():
        return jsonify({"success": False, "message": "DNI inválido. Debe contener 8 dígitos."}), 400

    # 1. Cifrar la contraseña
    try:
        hashed_password_bytes = bcrypt.generate_password_hash(contrasena_plana) 
        contrasena_cifrada = hashed_password_bytes.decode('utf-8') 
    except Exception:
        return jsonify({"success": False, "message": "Error al cifrar la contraseña."}), 500

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión a la base de datos."}), 500

    try:
        with conexion: 
            with conexion.cursor() as cursor:
                # 2. Validar unicidad (correo/dni)
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s"
                cursor.execute(sql_check, (correo, dni))
                if cursor.fetchone():
                    return jsonify({"success": False, "message": "El DNI o correo ya está registrado."}), 409

                # 3. Insertar nuevo usuario GESTOR ('G')
                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                
                # FORZAMOS 'G'
                tipo_usuario = 'G'
                
                cursor.execute(sql, (username, nombre, contrasena_cifrada, correo, dni, tipo_usuario, 0))
                conexion.commit()

        return jsonify({"success": True, "message": f"Gestor '{nombre}' ({username}) creado exitosamente."}), 201

    except pymysql.err.IntegrityError:
        return jsonify({"success": False, "message": "Error de integridad: El usuario ya existe o hay un problema con los datos."}), 409
    except Exception as e:
        print(f"Error en el registro de gestor (API): {e}")
        return jsonify({"success": False, "message": "Ocurrió un error en el sistema."}), 500

# --- RUTA API PARA ELIMINAR USUARIO (CONSUMIDA POR crudusuario.js) ---
@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario_api(usuario_id):
    """
    Ruta API para eliminar un usuario por su ID.
    Requiere que el usuario logueado sea un Gestor ('G').
    """
    # 1. Verificar autenticación
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado.'}), 401
    
    user_id_logueado = session['user_id']
    
    # 2. Verificar Permiso de Gestor ('G')
    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'error': 'Error de conexión a la base de datos.'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Consulta para verificar el rol del usuario logueado
                sql_check_role = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
                cursor.execute(sql_check_role, (user_id_logueado,))
                user_role_data = cursor.fetchone()

                if not user_role_data or user_role_data.get('tipo_usuario') != 'G':
                    return jsonify({'error': 'Acceso prohibido. No tienes permisos de gestor.'}), 403
                
                # 3. Restricción de auto-eliminación
                if usuario_id == user_id_logueado:
                    return jsonify({'error': 'No puedes eliminar tu propia cuenta de Gestor a través de esta interfaz.'}), 403

                # 4. Ejecutar la Eliminación
                sql_delete = "DELETE FROM usuario WHERE usuario_id=%s"
                filas_afectadas = cursor.execute(sql_delete, (usuario_id,))
                
                conexion.commit()

                if filas_afectadas == 0:
                    return jsonify({'error': f'Usuario con ID {usuario_id} no encontrado.'}), 404
                
                return jsonify({'success': True, 'message': f'Usuario con ID {usuario_id} eliminado exitosamente.'}), 200

    except Exception as e:
        print(f"Error al eliminar usuario: {e}", file=sys.stderr)
        return jsonify({'error': 'Error interno del servidor al eliminar datos.'}), 500


# RUTA API PARA CREAR UN NUEVO USUARIO DESDE LA ADMINISTRACIÓN (Gestor)
# ==============================================================================
@app.route("/api/usuarios", methods=['POST'])
def crear_usuario_api():
    """
    Ruta API para crear un nuevo usuario (A, P, G, E) desde el panel de gestión.
    Se corrige para incluir la validación e inserción del campo DNI.
    """
    # 1. VERIFICACIÓN DE PERMISOS (¡CLAVE!)
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado.'}), 401
    
    # --- LÓGICA DE VERIFICACIÓN DE ROL FALTANTE AQUÍ ---
    # *EJEMPLO* de cómo se haría la verificación de rol:
    # if obtener_rol_usuario(session['user_id']) != 'G': 
    #     return jsonify({'error': 'Acceso prohibido. No tienes permisos de gestor.'}), 403 
    
    data = request.get_json()

    # 2. VALIDACIÓN DE CAMPOS OBLIGATORIOS (AHORA INCLUYE 'dni')
    required_fields = ['username', 'nombre', 'contrasena', 'correo', 'tipo_usuario', 'dni']
    if not data or any(key not in data or not data[key] for key in required_fields):
        # El DNI se requiere, ya que el formulario de gestión lo requiere o tu DB lo requiere.
        return jsonify({"success": False, "error": "Faltan campos obligatorios: nombre, username, contrasena, correo, tipo_usuario, DNI."}), 400

    username = data['username']
    nombre = data['nombre']
    contrasena_plana = data['contrasena']
    correo = data['correo']
    tipo_usuario = data['tipo_usuario'].upper()
    dni = data['dni'] # <--- AHORA LEEMOS EL DNI DEL JSON

    # 3. VALIDACIÓN ADICIONAL DEL DNI Y TIPO DE USUARIO
    if len(dni) != 8 or not dni.isdigit():
         return jsonify({"success": False, "error": "DNI inválido. Debe contener 8 dígitos."}), 400
         
    if tipo_usuario not in ['A', 'P', 'G', 'E']:
         return jsonify({"success": False, "error": "Tipo de usuario inválido (solo A, P, G, E permitidos)."}), 400


    # 4. CIFRADO DE CONTRASEÑA
    try:
        hashed_password_bytes = bcrypt.generate_password_hash(contrasena_plana)
        contrasena_cifrada = hashed_password_bytes.decode('utf-8')
    except Exception:
        return jsonify({"success": False, "error": "Error al cifrar la contraseña."}), 500

    # 5. CONEXIÓN E INSERCIÓN
    conexion = obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "error": "Error de conexión a la base de datos."}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # 6. VALIDACIÓN DE UNICIDAD (Correo, DNI y/o Username)
                # Tu registro normal valida por Correo Y DNI. Mantenemos esa lógica.
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s OR username=%s"
                cursor.execute(sql_check, (correo, dni, username))
                if cursor.fetchone():
                    return jsonify({"success": False, "error": "El DNI, correo o username ya está registrado."}), 409

                # 7. Insertar nuevo usuario (AHORA INCLUYE DNI)
                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                
                # LA TUPLA DE VALORES DEBE COINCIDIR CON LA CONSULTA
                cursor.execute(sql, (username, nombre, contrasena_cifrada, correo, dni, tipo_usuario, 0))
                conexion.commit()

        return jsonify({"success": True, "message": f"Usuario '{username}' creado exitosamente."}), 201

    except Exception as e:
        # Imprime el error real en tu terminal de Flask para la depuración
        print(f"Error al crear usuario (API): {e}") 
        return jsonify({"success": False, "error": "Ocurrió un error en el sistema."}), 500

# Ruta para procesar el Login (CON VERIFICACIÓN BCrypt)
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
                # Solo buscamos por correo y traemos la contraseña cifrada
                sql = "SELECT `usuario_id`, `contrasena` FROM `usuario` WHERE `correo`=%s"
                cursor.execute(sql, (correo,))
                result = cursor.fetchone() 
            
            # Verificación
            if result:
                hashed_password = result['contrasena']
                
                # Usar check_password_hash para comparar la plana (usuario) con la cifrada (DB)
                if bcrypt.check_password_hash(hashed_password, contrasena_plana):
                    # Login Exitoso
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
            WHERE c.usuario_id = %s
        """, (usuario_id,))
        data = cursor.fetchall()
    return jsonify(data)


@app.route('/api/cuestionarios', methods=['POST'])
def crear_cuestionario():
    """
    Crea un nuevo cuestionario.
    """
    data = request.get_json()
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        sql = """
        INSERT INTO cuestionario (nombre_cuestionario, descripcion, publico, modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            data['nombre_cuestionario'],
            data.get('descripcion', ''),
            data.get('publico', 0),
            data['modo_juego'],
            data['tiempo_limite_pregunta'],
            data['usuario_id'],
            data.get('url_img_cuestionario', None)
        ))
        conexion.commit()
        nuevo_id = cursor.lastrowid
    return jsonify({'status': 'ok', 'cuestionario_id': nuevo_id})


@app.route('/api/cuestionarios/<int:cuestionario_id>', methods=['PUT'])
def actualizar_cuestionario(cuestionario_id):
    """
    Actualiza un cuestionario existente.
    """
    data = request.get_json()
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        sql = """
        UPDATE cuestionario 
        SET nombre_cuestionario=%s, descripcion=%s, publico=%s, modo_juego=%s, tiempo_limite_pregunta=%s, url_img_cuestionario=%s
        WHERE cuestionario_id=%s
        """
        cursor.execute(sql, (
            data['nombre_cuestionario'],
            data.get('descripcion', ''),
            data.get('publico', 0),
            data['modo_juego'],
            data['tiempo_limite_pregunta'],
            data.get('url_img_cuestionario', None),
            cuestionario_id
        ))
        conexion.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Cuestionario actualizado'})


@app.route('/api/cuestionarios/<int:cuestionario_id>', methods=['DELETE'])
def eliminar_cuestionario(cuestionario_id):
    """
    Elimina un cuestionario y en cascada sus preguntas y respuestas.
    """
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM cuestionario WHERE cuestionario_id=%s", (cuestionario_id,))
        conexion.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Cuestionario eliminado'})

# =========================================================
# --- CRUD DE PREGUNTAS ---
# =========================================================

@app.route('/api/preguntas/<int:cuestionario_id>', methods=['GET'])
def listar_preguntas(cuestionario_id):
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM pregunta WHERE cuestionario_id=%s", (cuestionario_id,))
        data = cursor.fetchall()
    return jsonify(data)


@app.route('/api/preguntas', methods=['POST'])
def crear_pregunta():
    data = request.get_json()
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        sql = """
        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data['texto_pregunta'],
            data.get('media_url', None),
            data.get('tiempo_limite', None),
            data['cuestionario_id']
        ))
        conexion.commit()
        nueva_id = cursor.lastrowid
    return jsonify({'status': 'ok', 'pregunta_id': nueva_id})


@app.route('/api/preguntas/<int:pregunta_id>', methods=['PUT'])
def actualizar_pregunta(pregunta_id):
    data = request.get_json()
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        sql = """
        UPDATE pregunta 
        SET texto_pregunta=%s, media_url=%s, tiempo_limite=%s
        WHERE pregunta_id=%s
        """
        cursor.execute(sql, (
            data['texto_pregunta'],
            data.get('media_url', None),
            data.get('tiempo_limite', None),
            pregunta_id
        ))
        conexion.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Pregunta actualizada'})


@app.route('/api/preguntas/<int:pregunta_id>', methods=['DELETE'])
def eliminar_pregunta(pregunta_id):
    conexion = obtenerConexion()
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM pregunta WHERE pregunta_id=%s", (pregunta_id,))
        conexion.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Pregunta eliminada'})


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
                # --- Subir imagen del cuestionario a Cloudinary si existe ---
                url_img_cuestionario = data.get("url_img_cuestionario")
                if url_img_cuestionario:
                    upload_result = cloudinary.uploader.upload(url_img_cuestionario)
                    url_img_cuestionario_cloud = upload_result["secure_url"]
                else:
                    url_img_cuestionario_cloud = None

                # Crear el cuestionario
                sql_cuestionario = """
                    INSERT INTO cuestionario 
                    (nombre_cuestionario, descripcion, publico, modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_cuestionario, (
                    data.get("nombre_cuestionario"),
                    data.get("descripcion"),
                    data.get("publico", 0),
                    data.get("modo_juego", "C"),
                    data.get("tiempo_limite_pregunta", 30),
                    data.get("usuario_id"),
                    url_img_cuestionario_cloud
                ))
                cuestionario_id = cursor.lastrowid

                # Crear las preguntas y sus respuestas
                for pregunta in data["preguntas"]:
                    sql_pregunta = """
                        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                        VALUES (%s, %s, %s, %s)
                    """
                    # Subir imagen a Cloudinary si existe
                    if pregunta.get("media_url"):
                        upload_result = cloudinary.uploader.upload(pregunta["media_url"])
                        media_url = upload_result["secure_url"]
                    else:
                        media_url = None

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
            "cuestionario_id": cuestionario_id
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
                       modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario
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
                url_img_cuestionario = data.get("url_img_cuestionario")
                if url_img_cuestionario:
                    upload_result = cloudinary.uploader.upload(url_img_cuestionario)
                    url_img_cuestionario_cloud = upload_result["secure_url"]
                else:
                    url_img_cuestionario_cloud = None

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
                    if pregunta.get("media_url"):
                        upload_result = cloudinary.uploader.upload(pregunta["media_url"])
                        media_url = upload_result["secure_url"]
                    else:
                        media_url = None

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


@app.route("/editar_cuestionario/<int:cuestionario_id>")
@login_required
def frm_edicioncuestionario(cuestionario_id):
    # Solo pasamos cuestionario_id; logged_in_user ya estará disponible en el template
    return render_template('editarcuestionario.html', cuestionario_id=cuestionario_id)