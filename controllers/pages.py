from flask import Blueprint, render_template, redirect, url_for, session, flash

pages_bp = Blueprint('pages', __name__, template_folder='../../templates')


@pages_bp.route('/')
def frm_bienvenido():
    return render_template('bienvenido.html')


@pages_bp.route('/home')
def frm_home():
    return render_template('home.html')


@pages_bp.route('/probarconexion')
def probarconexion():
    from main import obtenerConexion
    connection = obtenerConexion()
    if connection is None:
        return "<p>Error al conectar a la base de datos</p>"
    else:
        return "<p>Conexión exitosa</p>"


@pages_bp.route('/errorsistema')
def frm_error():
    return render_template('errorsistema.html')


@pages_bp.route('/editar_cuestionario/<int:cuestionario_id>')
def frm_edicioncuestionario(cuestionario_id):
    return render_template('editarcuestionario.html', cuestionario_id=cuestionario_id)


@pages_bp.route('/ver_cuestionario/<int:cuestionario_id>')
def frm_ver_cuestionario(cuestionario_id):
    return render_template('visualizarCuestionario.html', cuestionario_id=cuestionario_id)
