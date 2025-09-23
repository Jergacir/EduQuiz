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


@app.route("/")
def frm_login():
    return render_template('login.html')

@app.route("/registro")
def frm_registro():
    return render_template('registro.html')
