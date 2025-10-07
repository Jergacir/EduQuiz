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

# port zamora: 3306
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
        print("Error al obtener la conexión: %s" % (repr(e)))
        return None

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

# =========================================================
# >>> CÓDIGO FALTANTE 1: DECORADOR PARA RESTRINGIR ACCESO <<<
# =========================================================
def gestor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar si está logueado
        if 'user_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página.", 'warning')
            return redirect(url_for('frm_login'))

        # 2. Obtener los datos del usuario (que ya contiene tipo_usuario gracias al context_processor)
        # Usamos la misma función que inyecta los datos a las plantillas
        user_data = inject_user_data().get('logged_in_user')

        # 3. Verificar el tipo de usuario
        if not user_data or user_data.get('tipo_usuario') != 'G':
            flash("No tienes permiso para acceder a esta sección de administración.", 'error')
            return redirect(url_for('frm_home')) # Redirige al home si no es gestor
        
        return f(*args, **kwargs)
    return decorated_function
# =========================================================


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
                    # =========================================================
                    # >>> CÓDIGO FALTANTE 2: AGREGAR tipo_usuario a la consulta SQL <<<
                    # =========================================================
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

# ESTA RUTA YA ESTABA DEFINIDA CORRECTAMENTE, APLICAMOS EL DECORADOR FALTANTE
@app.route("/crud-usuarios")
@gestor_required  # ¡Ahora se usa el decorador gestor_required!
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
                # 1. CAMBIO CLAVE: Solo buscamos por correo y traemos la contraseña cifrada y el tipo_usuario
                # Es crucial traer el tipo_usuario aquí si no queremos depender del context_processor
                # Pero para simplicidad, con el user_id ya basta, pues el context_processor lo traerá.
                sql = "SELECT `usuario_id`, `contrasena` FROM `usuario` WHERE `correo`=%s"
                cursor.execute(sql, (correo,))
                result = cursor.fetchone() 
            
            # Verificación
            if result:
                hashed_password = result['contrasena']
                
                # 2. Usar check_password_hash para comparar la plana (usuario) con la cifrada (DB)
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
