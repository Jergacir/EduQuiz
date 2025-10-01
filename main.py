from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql.cursors
from functools import wraps
from flask_bcrypt import Bcrypt # <-- Importar Bcrypt

# pip install Flask-Bcrypt
# Si no quieres usar la extensión de Flask, puedes usar solo la librería bcrypt:


app = Flask(__name__)
app.secret_key = 'supersecreto123' # Importante para la autenticación
#IMPORTANTE: cambiar el puerto porfavor
bcrypt = Bcrypt(app) # <-- Inicializar Bcrypt con tu aplicación Flask

# port zamora: 3306
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
                    # Traemos los datos que necesitamos en el frontend
                    sql = "SELECT nombre, cant_monedas FROM usuario WHERE usuario_id=%s"
                    cursor.execute(sql, (user_id,))
                    user_data = cursor.fetchone()
                    
            if user_data:
                # Retornamos el diccionario que se inyectará en las plantillas
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

    # Ajustar dominio de correo según tipo
    if tipo == "Docente" and not email.endswith('@usat.edu.pe'):
        email = f"{email}@usat.edu.pe"
    elif tipo == "Alumno" and not email.endswith('@usat.pe'):
        email = f"{dni}@usat.pe"
        
    # --- INICIO CAMBIO BCrypt ---
    # 1. Cifrar la contraseña ANTES de guardarla
    hashed_password_bytes = bcrypt.generate_password_hash(contrasena_plana) 
    
    # 2. Decodificar a string para guardarlo en la base de datos (VARCHAR)
    contrasena_cifrada = hashed_password_bytes.decode('utf-8') 
    # --- FIN CAMBIO BCrypt ---

    # Intentar conexión
    conexion = obtenerConexion()
    if not conexion:
        print("No se pudo conectar a la base de datos")
        return redirect(url_for('frm_error')) 

    try:
        with conexion: 
            with conexion.cursor() as cursor:
                # Validar si ya existe usuario con mismo correo, username o dni
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s"
                username = email.split('@')[0]
                cursor.execute(sql_check, (email, dni))
                existe = cursor.fetchone()
                if existe:
                    flash("El DNI o correo ya está registrado.", 'error')
                    return redirect(url_for('frm_registro'))

                # Insertar nuevo usuario
                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                nombre = username.replace('_', ' ').title()
                tipo_usuario = 'A' if tipo == 'Alumno' else 'P'
                
                # 3. Usar la contraseña CIFRADA en la inserción
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
                # 1. CAMBIO CLAVE: Solo buscamos por correo y traemos la contraseña cifrada
                sql = "SELECT `usuario_id`, `contrasena` AS hashed_password FROM `usuario` WHERE `correo`=%s"
                cursor.execute(sql, (correo,))
                result = cursor.fetchone() # Trae el usuario si existe
            
            # Verificación
            if result:
                hashed_password = result['hashed_password']
                
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