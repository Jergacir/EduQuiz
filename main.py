from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql.cursors
from functools import wraps
from flask_bcrypt import Bcrypt 
import sys 

# pip install Flask-Bcrypt
# Si no quieres usar la extensión de Flask, puedes usar solo la librería bcrypt:


app = Flask(__name__)
app.secret_key = 'supersecreto123' # Importante para la autenticación
#IMPORTANTE: cambiar el puerto porfavor
bcrypt = Bcrypt(app) # Inicializar Bcrypt con tu aplicación Flask

# --- FUNCIÓN DE CONEXIÓN A LA BASE DE DATOS ---
def obtenerConexion():
    try:
        connection = pymysql.connect(host='localhost',
                                     port=3306, 
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
                    sql = "SELECT nombre, cant_monedas, tipo_usuario FROM usuario WHERE usuario_id=%s"
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
