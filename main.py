from flask import Flask, render_template, request, redirect, url_for
import pymysql.cursors

app = Flask(__name__)

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

def frm_home():
    return render_template('home.html')

# Ruta para procesar el registro de usuario
@app.route("/procesarregistro", methods=['POST'])
def procesarregistro():
    tipo = request.form.get('tipo')
    dni = request.form.get('dni')
    email = request.form.get('email')
    contrasena = request.form.get('contrasena')
    confirmar = request.form.get('confirmarContrasena')
    if contrasena != confirmar:
        return redirect(url_for('frm_registro'))
    if not email.endswith('@usat.edu.pe'):
        email = f"{email}@usat.edu.pe"
    conexion = obtenerConexion()
    if conexion:
        with conexion:
            with conexion.cursor() as cursor:
                sql = "INSERT INTO usuario (username, nombre, contrasena, correo, tipo_usuario, cant_monedas) VALUES (%s, %s, %s, %s, %s, %s)"
                username = email.split('@')[0]
                nombre = username.replace('_', ' ').title()
                tipo_usuario = 'A' if tipo == 'Alumno' else 'P'
                try:
                    cursor.execute(sql, (username, nombre, contrasena, email, tipo_usuario, 0))
                    conexion.commit()
                except Exception as e:
                    print(f"Error al registrar usuario: {e}")
                    return redirect(url_for('frm_registro'))
        return redirect(url_for('frm_login'))
    return redirect(url_for('frm_registro'))

@app.route("/procesarlogin", methods=['POST'])
def procesarlogin():
    correo = request.form['correo']
    contrasena = request.form['contrasena']
    conexion = obtenerConexion()
    if conexion:
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