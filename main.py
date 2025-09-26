from flask import Flask, render_template, request, redirect, url_for
import pymysql.cursors

app = Flask(__name__)
#IMPORTANTE: cambiar el puerto porfavor
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

@app.route("/probarconexion")
def probarconexion():
    connection = obtenerConexion()
    if connection is None:
        return "<p>Error al conectar a la base de datos</p>"
    else:
        return "<p>Conexión exitosa</p>"

@app.route("/")
def frm_login():
    return render_template('login.html')

@app.route("/registro")
def frm_registro():
    return render_template('registro.html')


@app.route("/home")
def frm_home():
    return render_template('home.html')

@app.route("/errorsistema")
def frm_error():
    return render_template('errorsistema.html')
    
# Ruta para procesar el registro de usuario
@app.route("/procesarregistro", methods=['POST'])
def procesarregistro():
    tipo = request.form.get('tipo')
    dni = request.form.get('dni')
    email = request.form.get('email')
    contrasena = request.form.get('contrasena')
    confirmar = request.form.get('confirmarContrasena')

    # Validaciones básicas de formulario
    if not tipo or not dni or not email or not contrasena or not confirmar:
        print("Faltan campos obligatorios")
        return redirect(url_for('frm_registro'))
    
    # Solo validar longitud DNI si es Alumno o Docente (en ambos debe ser 8 dígitos)
    if len(dni) != 8 or not dni.isdigit():
        print("DNI inválido")
        return redirect(url_for('frm_registro'))
    
    if contrasena != confirmar:
        print("Las contraseñas no coinciden")
        return redirect(url_for('frm_registro'))

    # Ajustar dominio de correo según tipo
    if tipo == "Docente" and not email.endswith('@usat.edu.pe'):
        email = f"{email}@usat.edu.pe"
    elif tipo == "Alumno" and not email.endswith('@usat.pe'):
        email = f"{dni}@usat.pe"

    # Intentar conexión
    conexion = obtenerConexion()
    if not conexion:
        print("No se pudo conectar a la base de datos")
        return redirect(url_for('frm_error'))  # Error real de sistema

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Validar si ya existe usuario con mismo correo, username o dni
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR username=%s OR dni=%s"
                username = email.split('@')[0]
                cursor.execute(sql_check, (email, username, dni))
                existe = cursor.fetchone()
                if existe:
                    print("Usuario ya registrado (correo o dni)")
                    return redirect(url_for('frm_registro'))

                # Insertar nuevo usuario
                sql = """INSERT INTO usuario
                         (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                nombre = username.replace('_', ' ').title()
                tipo_usuario = 'A' if tipo == 'Alumno' else 'P'
                cursor.execute(sql, (username, nombre, contrasena, email, dni, tipo_usuario, 0))
                conexion.commit()

        return redirect(url_for('frm_login'))

    except pymysql.err.IntegrityError as ie:
        # Error de negocio (duplicado de clave única)
        print(f"Error de negocio: {ie}")
        return redirect(url_for('frm_registro'))

    except Exception as e:
        # Error REAL de sistema (SQL mal, tabla no existe, etc.)
        print(f"Error en el registro (sistema): {e}")
        return redirect(url_for('frm_error'))



@app.route("/procesarlogin", methods=['POST'])
def procesarlogin():
    correo = request.form['correo']
    contrasena = request.form['contrasena']
    conexion = obtenerConexion()
    if not conexion:
        print("No se pudo conectar a la base de datos (login)")
        return redirect(url_for('frm_error'))
    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT `usuario_id` FROM `usuario` WHERE `correo`=%s AND `contrasena`=%s"
                cursor.execute(sql, (correo, contrasena))
                result = cursor.fetchone()
            if result:
                #Redireccionar a bienvenida
                return redirect(url_for('frm_home'))
            else:
                #Cargar nuevamente el login
                return redirect(url_for('frm_login'))
    except Exception as e:
        print(f"Error en el login: {e}")
        return redirect(url_for('frm_error'))