from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import sys
import db as dbmod


def _get_logged_in_user():
    """Devuelve un dict con los datos del usuario logueado o {} si no hay sesión.
    Evita importar el context_processor de main.py y previene ciclos de import.
    """
    if 'user_id' not in session:
        return {}
    user_id = session['user_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return {}
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT usuario_id AS usuario_id, nombre, cant_monedas, tipo_usuario FROM usuario WHERE usuario_id=%s"
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return row or {}
    except Exception as e:
        print(f"[partidas] error obteniendo usuario: {e}", file=sys.stderr)
        return {}

partidas_bp = Blueprint('partidas', __name__, template_folder='../../templates')


@partidas_bp.route('/partidas')
def frm_partidas():
    logged = _get_logged_in_user()
    return render_template('partidas.html', logged_in_user=logged)


@partidas_bp.route('/jugar/<string:codigo_partida>')
def frm_jugar(codigo_partida):
    flash(f"Te has unido a la partida con código: {codigo_partida}. (Vista de juego por implementar)", 'success')
    logged = _get_logged_in_user()
    return render_template('jugar.html', codigo_partida=codigo_partida, logged_in_user=logged)


def validar_y_unir(codigo_partida, usuario_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("Error: No se pudo conectar a la base de datos (validar_y_unir)", file=sys.stderr)
        return False

    try:
        with conexion.cursor() as cursor:
            sql_partida = "SELECT partida_id, estado, max_jugadores FROM partida WHERE codigo_partida = %s"
            cursor.execute(sql_partida, (codigo_partida,))
            partida = cursor.fetchone()

            if not partida or partida.get('estado') != 'espera':
                print(f"Error: Partida '{codigo_partida}' no encontrada o no está en estado de espera.")
                return False

            partida_id = partida['partida_id']
            max_jugadores = partida['max_jugadores']

            sql_contar = "SELECT COUNT(*) AS total_jugadores, SUM(CASE WHEN usuario_id = %s THEN 1 ELSE 0 END) AS usuario_existe FROM participante_partida WHERE partida_id = %s"
            cursor.execute(sql_contar, (usuario_id, partida_id))
            count_row = cursor.fetchone()
            total = count_row.get('total_jugadores', 0)
            usuario_existe = count_row.get('usuario_existe', 0)

            if usuario_existe and usuario_existe > 0:
                print(f"Advertencia: Usuario {usuario_id} ya está en la partida {codigo_partida}.")
                return True

            if total >= max_jugadores:
                print(f"Error: La partida '{codigo_partida}' está llena. (Max: {max_jugadores})")
                return False

            sql_unir = "INSERT INTO participante_partida (partida_id, usuario_id) VALUES (%s, %s)"
            cursor.execute(sql_unir, (partida_id, usuario_id))
            conexion.commit()
            print(f"Éxito: Usuario {usuario_id} unido a partida {codigo_partida}.")
            return True

    except Exception as e:
        print(f"Error validar_y_unir: {e}", file=sys.stderr)
        return False


@partidas_bp.route('/api/partida/unirse', methods=['POST'])
def api_unirse_partida():
    data = request.get_json() or {}
    usuario_id = session.get('user_id')
    codigo_partida = data.get('codigo')

    if not codigo_partida or not usuario_id:
        return jsonify({"success": False, "message": "Faltan el código de partida o el ID de usuario."}), 400

    if validar_y_unir(codigo_partida, usuario_id):
        return jsonify({
            "success": True,
            "message": "¡Te has unido a la partida!",
            "redirect_url": url_for('partidas.frm_jugar', codigo_partida=codigo_partida)
        }), 200

    return jsonify({"success": False, "message": "Código de partida inválido o partida llena."}), 400


@partidas_bp.route('/partidas_profesor')
def frm_partidas_profesor():
    logged = _get_logged_in_user()
    return render_template('partidas_profesor.html', logged_in_user=logged)


@partidas_bp.route('/crear_partida')
def frm_crear_partida():
    flash("Aquí se creará una nueva partida (Vista en desarrollo)", 'info')
    logged = _get_logged_in_user()
    return render_template('crear_partida.html', logged_in_user=logged)


@partidas_bp.route('/resultados_partida/<int:partida_id>')
def frm_resultados_partida(partida_id):
    # Implementación mínima: pasar datos de ejemplo a la plantilla
    partida_info = {
        'titulo': 'Resultados de Partida',
        'partida_id': partida_id
    }
    logged = _get_logged_in_user()
    return render_template('resultados_partida.html', partida_info=partida_info, partida_id=partida_id, logged_in_user=logged)


@partidas_bp.route('/exportar_resultados/<int:partida_id>')
def frm_exportar_resultados(partida_id):
    partida_info = {'partida_id': partida_id}
    logged = _get_logged_in_user()
    return render_template('exportar_resultados.html', partida_id=partida_id, partida_info=partida_info, logged_in_user=logged)


@partidas_bp.route('/api/exportar_partida/<int:partida_id>', methods=['POST'])
def api_exportar_partida(partida_id):
    data = request.get_json() or {}
    formato = data.get('formato', 'csv')
    campos = data.get('campos', [])
    # Aquí se exportaría la partida; por ahora devolvemos éxito simulado.
    print(f"Exportando partida #{partida_id} a {formato} con campos: {campos}")
    return jsonify({'success': True, 'message': f'Partida {partida_id} exportada como {formato}.'})
