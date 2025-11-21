from flask import Blueprint, request, jsonify
import sys
import db as dbmod
from datetime import datetime
import random
import string

# ✅ Importar funciones de autenticación
from auth_utils import jwt_required_api_enhanced, get_user_from_jwt_or_session

# Intentar importar bcrypt si existe, sino None (para evitar rupturas)
try:
    from extensions import bcrypt
except Exception:
    bcrypt = None

# ============================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ============================================================
# Usamos un solo Blueprint para todo. El prefijo es "/"
# por lo que las rutas serán: /api_obtenercuestionarios, /api/api_obtenerusuarios, etc.
apiv1_bp = Blueprint('apiv1', __name__, url_prefix="/")

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtenerConexion():
    """Intenta obtener conexión desde main o usa dbmod directamente."""
    try:
        import main as mainmod
        if hasattr(mainmod, 'obtenerConexion'):
            return mainmod.obtenerConexion()
    except Exception:
        pass
    return dbmod.obtenerConexion()

def _json_error(message, status=400, **extra):
    resp = {"ok": False, "error": message}
    if extra:
        resp.update(extra)
    return jsonify(resp), status

def _json_ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    if extra:
        payload.update(extra)
    return jsonify(payload)

def _codigo_random(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


# ============================================================
# BLOQUE 1: CUESTIONARIOS
# ============================================================

@apiv1_bp.route('/api_obtenercuestionarios', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_cuestionarios():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM cuestionario WHERE estado = 1")
            data = cursor.fetchall()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenercuestionarios] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_obtenercuestionarioporid/<int:cuestionario_id>', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_cuestionario_por_id(cuestionario_id):
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM cuestionario WHERE cuestionario_id = %s AND estado = 1", (cuestionario_id,))
            data = cursor.fetchone()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenercuestionarioporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_registrarcuestionario', methods=['POST'])
@jwt_required_api_enhanced
def api_registrar_cuestionario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    campos_requeridos = ['nombre_cuestionario', 'descripcion', 'publico', 'modo_juego', 
                         'tiempo_limite_pregunta', 'usuario_id', 'url_img_cuestionario', 'codigo_visualizacion']

    for campo in campos_requeridos:
        if campo not in body:
            return jsonify({'status': 'error', 'mensaje': f'Falta el campo {campo}'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO cuestionario (
                    nombre_cuestionario, descripcion, publico,
                    modo_juego, tiempo_limite_pregunta,
                    usuario_id, url_img_cuestionario, estado, codigo_visualizacion
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,1,%s)
            """, (
                body['nombre_cuestionario'], body.get('descripcion'), body['publico'],
                body['modo_juego'], body['tiempo_limite_pregunta'], body['usuario_id'],
                body.get('url_img_cuestionario'), body['codigo_visualizacion']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario registrado correctamente'})
    except Exception as e:
        print("[api_registrarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_actualizarcuestionario', methods=['POST'])
@jwt_required_api_enhanced
def api_actualizar_cuestionario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'cuestionario_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'cuestionario_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE cuestionario
                SET nombre_cuestionario=%s, descripcion=%s, publico=%s,
                    modo_juego=%s, tiempo_limite_pregunta=%s, url_img_cuestionario=%s
                WHERE cuestionario_id=%s AND estado=1
            """, (
                body.get('nombre_cuestionario'), body.get('descripcion'), body.get('publico'),
                body.get('modo_juego'), body.get('tiempo_limite_pregunta'),
                body.get('url_img_cuestionario'), body['cuestionario_id']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario actualizado correctamente'})
    except Exception as e:
        print("[api_actualizarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_eliminarcuestionario', methods=['POST'])
@jwt_required_api_enhanced
def api_eliminar_cuestionario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'cuestionario_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'cuestionario_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE cuestionario SET estado = 0 WHERE cuestionario_id = %s", (body['cuestionario_id'],))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario eliminado correctamente'})
    except Exception as e:
        print("[api_eliminarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# BLOQUE 2: PREGUNTAS
# ============================================================

@apiv1_bp.route('/api_obtenerpreguntas', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_preguntas():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM pregunta")
            data = cursor.fetchall()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerpreguntas] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_obtenerpreguntaporid/<int:pregunta_id>', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_pregunta_por_id(pregunta_id):
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM pregunta WHERE pregunta_id = %s", (pregunta_id,))
            data = cursor.fetchone()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerpreguntaporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_registrarpregunta', methods=['POST'])
@jwt_required_api_enhanced
def api_registrar_pregunta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'texto_pregunta' not in body or 'cuestionario_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'Faltan campos obligatorios'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                VALUES (%s, %s, %s, %s)
            """, (
                body['texto_pregunta'], body.get('media_url'),
                body.get('tiempo_limite'), body['cuestionario_id']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Pregunta registrada correctamente'})
    except Exception as e:
        print("[api_registrarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_actualizarpregunta', methods=['POST'])
@jwt_required_api_enhanced
def api_actualizar_pregunta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'pregunta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'pregunta_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE pregunta
                SET texto_pregunta = %s, media_url = %s, tiempo_limite = %s, cuestionario_id = %s
                WHERE pregunta_id = %s
            """, (
                body.get('texto_pregunta'), body.get('media_url'),
                body.get('tiempo_limite'), body.get('cuestionario_id'), body['pregunta_id']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Pregunta actualizada correctamente'})
    except Exception as e:
        print("[api_actualizarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_eliminarpregunta', methods=['POST'])
@jwt_required_api_enhanced
def api_eliminar_pregunta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'pregunta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'pregunta_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM pregunta WHERE pregunta_id = %s", (body['pregunta_id'],))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Pregunta eliminada correctamente'})
    except Exception as e:
        print("[api_eliminarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# BLOQUE 3: RESPUESTAS
# ============================================================

@apiv1_bp.route('/api_obtenerrespuestas', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_respuestas():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM respuesta")
            data = cursor.fetchall()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerrespuestas] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_obtenerrespuestaporid/<int:respuesta_id>', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_respuesta_por_id(respuesta_id):
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM respuesta WHERE respuesta_id = %s", (respuesta_id,))
            data = cursor.fetchone()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerrespuestaporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_registrarrespuesta', methods=['POST'])
@jwt_required_api_enhanced
def api_registrar_respuesta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'texto_respuesta' not in body or 'estado_respuesta' not in body or 'pregunta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'Faltan campos'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id)
                VALUES (%s, %s, %s)
            """, (body['texto_respuesta'], body['estado_respuesta'], body['pregunta_id']))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Respuesta registrada correctamente'})
    except Exception as e:
        print("[api_registrarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_actualizarrespuesta', methods=['POST'])
@jwt_required_api_enhanced
def api_actualizar_respuesta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'respuesta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'respuesta_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE respuesta
                SET texto_respuesta = %s, estado_respuesta = %s, pregunta_id = %s
                WHERE respuesta_id = %s
            """, (
                body.get('texto_respuesta'), body.get('estado_respuesta'),
                body.get('pregunta_id'), body['respuesta_id']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Respuesta actualizada correctamente'})
    except Exception as e:
        print("[api_actualizarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_eliminarrespuesta', methods=['POST'])
@jwt_required_api_enhanced
def api_eliminar_respuesta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'respuesta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'respuesta_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM respuesta WHERE respuesta_id = %s", (body['respuesta_id'],))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Respuesta eliminada correctamente'})
    except Exception as e:
        print("[api_eliminarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# BLOQUE 4: PARTICIPANTES
# ============================================================

@apiv1_bp.route('/api_obtenerparticipantes', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_participantes():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM participante")
            data = cursor.fetchall()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerparticipantes] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_obtenerparticipanteporid/<int:participante_id>', methods=['GET'])
@jwt_required_api_enhanced
def api_obtener_participante_por_id(participante_id):
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM participante WHERE participante_id = %s", (participante_id,))
            data = cursor.fetchone()
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        print("[api_obtenerparticipanteporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_registrarparticipante', methods=['POST'])
@jwt_required_api_enhanced
def api_registrar_participante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'usuario_id' not in body or 'partida_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'Faltan campos'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO participante (
                    puntuacion_total, cant_preguntas_correctas, cant_preguntas_incorrectas,
                    lider_id, usuario_id, partida_id, grupo_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                body.get('puntuacion_total', 0.00), body.get('cant_preguntas_correctas', 0),
                body.get('cant_preguntas_incorrectas', 0), body.get('lider_id'),
                body['usuario_id'], body['partida_id'], body.get('grupo_id')
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Participante registrado correctamente'})
    except Exception as e:
        print("[api_registrarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_actualizarparticipante', methods=['POST'])
@jwt_required_api_enhanced
def api_actualizar_participante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'participante_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'participante_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE participante
                SET puntuacion_total = %s, cant_preguntas_correctas = %s, cant_preguntas_incorrectas = %s,
                    lider_id = %s, usuario_id = %s, partida_id = %s, grupo_id = %s
                WHERE participante_id = %s
            """, (
                body.get('puntuacion_total'), body.get('cant_preguntas_correctas'),
                body.get('cant_preguntas_incorrectas'), body.get('lider_id'),
                body.get('usuario_id'), body.get('partida_id'),
                body.get('grupo_id'), body['participante_id']
            ))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Participante actualizado correctamente'})
    except Exception as e:
        print("[api_actualizarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@apiv1_bp.route('/api_eliminarparticipante', methods=['POST'])
@jwt_required_api_enhanced
def api_eliminar_participante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json()
    if 'participante_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'participante_id es requerido'}), 400

    conexion = obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM participante WHERE participante_id = %s", (body['participante_id'],))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Participante eliminado correctamente'})
    except Exception as e:
        print("[api_eliminarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# BLOQUE 5: USUARIOS
# ============================================================

@apiv1_bp.get('/api_obtenerusuarios')
@jwt_required_api_enhanced
def api_obtenerusuarios():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    vigencia = request.args.get('vigencia')
    conexion = obtenerConexion()

    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = "SELECT usuario_id, username, nombre, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia, url_foto_perfil, url_avatar FROM usuario"
                params = []
                if vigencia is not None:
                    sql += " WHERE vigencia=%s"
                    params.append(int(vigencia))
                sql += " ORDER BY usuario_id ASC"
                c.execute(sql, params)
                rows = c.fetchall()
        return _json_ok(rows)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerusuarioporid')
@jwt_required_api_enhanced
def api_obtenerusuarioporid():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    usuario_id = request.args.get('usuario_id', type=int)
    if not usuario_id:
        return _json_error('usuario_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)
    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT usuario_id, username, nombre, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia, url_foto_perfil, url_avatar FROM usuario WHERE usuario_id=%s", (usuario_id,))
                row = c.fetchone()
        if not row:
            return _json_error('Usuario no encontrado', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_registrarusuario')
@jwt_required_api_enhanced
def api_registrarusuario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    required = ['username', 'nombre', 'contrasena', 'correo', 'dni', 'tipo_usuario']
    faltantes = [k for k in required if not body.get(k)]
    if faltantes:
        return _json_error(f"Faltan campos: {', '.join(faltantes)}")

    contrasena = body['contrasena']
    contrasena_hash = contrasena
    if bcrypt:
        try:
            contrasena_hash = bcrypt.generate_password_hash(contrasena).decode('utf-8')
        except Exception:
            pass

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT 1 FROM usuario WHERE username=%s OR correo=%s OR dni=%s", (body['username'], body['correo'], body['dni']))
                if c.fetchone():
                    return _json_error('Username/correo/DNI ya existe', 409)
                sql = ("INSERT INTO usuario (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado, vigencia, url_foto_perfil, url_avatar) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                params = (
                    body['username'], body['nombre'], contrasena_hash, body['correo'], body['dni'], body['tipo_usuario'],
                    int(body.get('cant_monedas') or 0), int(body.get('verificado') or 0), int(body.get('vigencia') or 1),
                    body.get('url_foto_perfil'), body.get('url_avatar')
                )
                c.execute(sql, params)
                conexion.commit()
                nuevo_id = c.lastrowid
        return _json_ok({"usuario_id": nuevo_id})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_actualizarusuario')
@jwt_required_api_enhanced
def api_actualizarusuario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    usuario_id = body.get('usuario_id')
    if not usuario_id:
        return _json_error('usuario_id requerido')

    campos = ['username', 'nombre', 'correo', 'dni', 'tipo_usuario', 'cant_monedas', 'verificado', 'vigencia', 'url_foto_perfil', 'url_avatar']
    sets = []
    params = []
    for k in campos:
        if k in body:
            sets.append(f"{k}=%s")
            params.append(body[k])
    if 'contrasena' in body and body['contrasena']:
        if bcrypt:
            try:
                hashed = bcrypt.generate_password_hash(body['contrasena']).decode('utf-8')
            except Exception:
                hashed = body['contrasena']
        else:
            hashed = body['contrasena']
        sets.append("contrasena=%s")
        params.append(hashed)
    if not sets:
        return _json_error('Nada para actualizar')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)
    try:
        with conexion:
            with conexion.cursor() as c:
                sql = f"UPDATE usuario SET {', '.join(sets)} WHERE usuario_id=%s"
                params.append(usuario_id)
                c.execute(sql, params)
                conexion.commit()
        return _json_ok({"usuario_id": usuario_id, "actualizado": True})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_eliminarusuario')
@jwt_required_api_enhanced
def api_eliminarusuario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    usuario_id = body.get('usuario_id')
    if not usuario_id:
        return _json_error('usuario_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)
    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("UPDATE usuario SET vigencia=0 WHERE usuario_id=%s", (usuario_id,))
                conexion.commit()
        return _json_ok({"usuario_id": usuario_id, "vigencia": 0})
    except Exception as e:
        return _json_error(str(e), 500)


# ============================================================
# BLOQUE 6: SKINS
# ============================================================

@apiv1_bp.get('/api_obtenerskins')
@jwt_required_api_enhanced
def api_obtenerskins():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    vigencia = request.args.get('vigencia')
    categoria = request.args.get('categoria')
    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = "SELECT skin_id, nombre, url_imagen, precio, vigencia, skinDefault, categoria FROM skin WHERE 1=1"
                params = []
                if vigencia is not None:
                    sql += " AND vigencia=%s"
                    params.append(int(vigencia))
                if categoria:
                    sql += " AND categoria=%s"
                    params.append(categoria)
                sql += " ORDER BY skin_id ASC"
                c.execute(sql, params)
                rows = c.fetchall()
        return _json_ok(rows)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerskinporid')
@jwt_required_api_enhanced
def api_obtenerskinporid():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    skin_id = request.args.get('skin_id', type=int)
    if not skin_id:
        return _json_error('skin_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT skin_id, nombre, url_imagen, precio, vigencia, skinDefault, categoria FROM skin WHERE skin_id=%s", (skin_id,))
                row = c.fetchone()
        if not row:
            return _json_error('Skin no encontrada', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_registrarskin')
@jwt_required_api_enhanced
def api_registrarskin():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    required = ['nombre', 'url_imagen', 'precio', 'categoria']
    falt = [k for k in required if not b.get(k)]
    if falt:
        return _json_error(f"Faltan campos: {', '.join(falt)}")

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = ("INSERT INTO skin (nombre, url_imagen, precio, vigencia, skinDefault, categoria) "
                       "VALUES (%s,%s,%s,%s,%s,%s)")
                params = (b['nombre'], b['url_imagen'], int(b['precio']), int(b.get('vigencia') or 1), int(b.get('skinDefault') or 0), b['categoria'])
                c.execute(sql, params)
                conexion.commit()
                skin_id = c.lastrowid
        return _json_ok({"skin_id": skin_id})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_actualizarskin')
@jwt_required_api_enhanced
def api_actualizarskin():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    skin_id = b.get('skin_id')
    if not skin_id:
        return _json_error('skin_id requerido')

    campos = ['nombre', 'url_imagen', 'precio', 'vigencia', 'skinDefault', 'categoria']
    sets, params = [], []
    for k in campos:
        if k in b:
            sets.append(f"{k}=%s")
            params.append(b[k])
    if not sets:
        return _json_error('Nada para actualizar')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = f"UPDATE skin SET {', '.join(sets)} WHERE skin_id=%s"
                params.append(skin_id)
                c.execute(sql, params)
                conexion.commit()
        return _json_ok({"skin_id": skin_id, "actualizado": True})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_eliminarskin')
@jwt_required_api_enhanced
def api_eliminarskin():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    skin_id = b.get('skin_id')
    if not skin_id:
        return _json_error('skin_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("UPDATE skin SET vigencia=0 WHERE skin_id=%s", (skin_id,))
                conexion.commit()
        return _json_ok({"skin_id": skin_id, "vigencia": 0})
    except Exception as e:
        return _json_error(str(e), 500)


# ============================================================
# BLOQUE 7: INVENTARIO
# ============================================================

@apiv1_bp.get('/api_obtenerinventarios')
@jwt_required_api_enhanced
def api_obtenerinventarios():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    usuario_id = request.args.get('usuario_id', type=int)
    tipo_item = request.args.get('tipo_item')
    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = "SELECT id_inventario, usuario_id, equipada, fecha_adquisicion, id_item, tipo_item FROM inventario WHERE 1=1"
                params = []
                if usuario_id:
                    sql += " AND usuario_id=%s"
                    params.append(usuario_id)
                if tipo_item:
                    sql += " AND tipo_item=%s"
                    params.append(tipo_item)
                sql += " ORDER BY id_inventario DESC"
                c.execute(sql, params)
                rows = c.fetchall()
        return _json_ok(rows)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerinventarioporid')
@jwt_required_api_enhanced
def api_obtenerinventarioporid():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    inv_id = request.args.get('id_inventario', type=int)
    if not inv_id:
        return _json_error('id_inventario requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT id_inventario, usuario_id, equipada, fecha_adquisicion, id_item, tipo_item FROM inventario WHERE id_inventario=%s", (inv_id,))
                row = c.fetchone()
        if not row:
            return _json_error('Inventario no encontrado', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_registrarinventario')
@jwt_required_api_enhanced
def api_registrarinventario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    req = ['usuario_id', 'id_item', 'tipo_item']
    falt = [k for k in req if not b.get(k)]
    if falt:
        return _json_error(f"Faltan campos: {', '.join(falt)}")

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = ("INSERT INTO inventario (usuario_id, equipada, fecha_adquisicion, id_item, tipo_item) "
                       "VALUES (%s,%s,%s,%s,%s)")
                params = (int(b['usuario_id']), int(b.get('equipada') or 0), datetime.utcnow().date(), int(b['id_item']), b['tipo_item'])
                c.execute(sql, params)
                conexion.commit()
                inv_id = c.lastrowid
        return _json_ok({"id_inventario": inv_id})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_actualizarinventario')
@jwt_required_api_enhanced
def api_actualizarinventario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    inv_id = b.get('id_inventario')
    if not inv_id:
        return _json_error('id_inventario requerido')

    campos = ['equipada', 'id_item', 'tipo_item']
    sets, params = [], []
    for k in campos:
        if k in b:
            sets.append(f"{k}=%s")
            params.append(b[k])
    if not sets:
        return _json_error('Nada para actualizar')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = f"UPDATE inventario SET {', '.join(sets)} WHERE id_inventario=%s"
                params.append(inv_id)
                c.execute(sql, params)
                conexion.commit()
        return _json_ok({"id_inventario": inv_id, "actualizado": True})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_eliminarinventario')
@jwt_required_api_enhanced
def api_eliminarinventario():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    inv_id = b.get('id_inventario')
    if not inv_id:
        return _json_error('id_inventario requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("DELETE FROM inventario WHERE id_inventario=%s", (inv_id,))
                conexion.commit()
        return _json_ok({"id_inventario": inv_id, "eliminado": True})
    except Exception as e:
        return _json_error(str(e), 500)


# ============================================================
# BLOQUE 8: PARTIDAS
# ============================================================

@apiv1_bp.get('/api_obtenerpartidas')
@jwt_required_api_enhanced
def api_obtenerpartidas():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    estado = request.args.get('estado')
    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = "SELECT partida_id, codigo_partida, cuestionario_id, usuario_creador_id, estado, fecha_creacion, num_grupos, tipo_partida, pregunta_actual_index, tiempo_inicio_pregunta, respuestas_recibidas, updated_at FROM partida WHERE 1=1"
                params = []
                if estado:
                    sql += " AND estado=%s"
                    params.append(estado)
                sql += " ORDER BY partida_id DESC"
                c.execute(sql, params)
                rows = c.fetchall()
        return _json_ok(rows)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerpartidaporid')
@jwt_required_api_enhanced
def api_obtenerpartidaporid():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    partida_id = request.args.get('partida_id', type=int)
    if not partida_id:
        return _json_error('partida_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT partida_id, codigo_partida, cuestionario_id, usuario_creador_id, estado, fecha_creacion, num_grupos, tipo_partida, pregunta_actual_index, tiempo_inicio_pregunta, respuestas_recibidas, updated_at FROM partida WHERE partida_id=%s", (partida_id,))
                row = c.fetchone()
        if not row:
            return _json_error('Partida no encontrada', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerpartidaporcodigo')
@jwt_required_api_enhanced
def api_obtenerpartidaporcodigo():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    codigo = request.args.get('codigo_partida')
    if not codigo:
        return _json_error('codigo_partida requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT partida_id, codigo_partida, cuestionario_id, usuario_creador_id, estado, fecha_creacion, num_grupos, tipo_partida, pregunta_actual_index, tiempo_inicio_pregunta, respuestas_recibidas, updated_at FROM partida WHERE codigo_partida=%s", (codigo,))
                row = c.fetchone()
        if not row:
            return _json_error('Partida no encontrada', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_registrarpartida')
@jwt_required_api_enhanced
def api_registrarpartida():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    req = ['cuestionario_id', 'usuario_creador_id']
    falt = [k for k in req if not b.get(k)]
    if falt:
        return _json_error(f"Faltan campos: {', '.join(falt)}")

    codigo = b.get('codigo_partida') or _codigo_random(6)
    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT 1 FROM partida WHERE codigo_partida=%s", (codigo,))
                if c.fetchone():
                    codigo = _codigo_random(6)
                sql = ("INSERT INTO partida (codigo_partida, cuestionario_id, usuario_creador_id, estado, fecha_creacion, num_grupos, tipo_partida, pregunta_actual_index) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")
                params = (
                    codigo, int(b['cuestionario_id']), int(b['usuario_creador_id']), b.get('estado') or 'creada', datetime.utcnow(),
                    int(b.get('num_grupos') or 0), (b.get('tipo_partida') or 'I'), int(b.get('pregunta_actual_index') or 0)
                )
                c.execute(sql, params)
                conexion.commit()
                partida_id = c.lastrowid
        return _json_ok({"partida_id": partida_id, "codigo_partida": codigo})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_actualizarpartida')
@jwt_required_api_enhanced
def api_actualizarpartida():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    partida_id = b.get('partida_id')
    if not partida_id:
        return _json_error('partida_id requerido')

    campos = ['estado', 'num_grupos', 'tipo_partida', 'pregunta_actual_index', 'respuestas_recibidas']
    sets, params = [], []
    for k in campos:
        if k in b:
            sets.append(f"{k}=%s")
            params.append(b[k])
    if 'tiempo_inicio_pregunta' in b:
        sets.append("tiempo_inicio_pregunta=%s")
        params.append(b['tiempo_inicio_pregunta'])
    if not sets:
        return _json_error('Nada para actualizar')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = f"UPDATE partida SET {', '.join(sets)} WHERE partida_id=%s"
                params.append(partida_id)
                c.execute(sql, params)
                conexion.commit()
        return _json_ok({"partida_id": partida_id, "actualizado": True})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_eliminarpartida')
@jwt_required_api_enhanced
def api_eliminarpartida():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    partida_id = b.get('partida_id')
    if not partida_id:
        return _json_error('partida_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT participante_id FROM participante WHERE partida_id=%s", (partida_id,))
                participantes = [row['participante_id'] for row in c.fetchall() or []]
                if participantes:
                    format_ids = ','.join(['%s'] * len(participantes))
                    c.execute(f"DELETE FROM pregunta_participante WHERE participante_id IN ({format_ids})", participantes)
                    c.execute(f"DELETE FROM participante WHERE participante_id IN ({format_ids})", participantes)
                
                c.execute("DELETE FROM partida WHERE partida_id=%s", (partida_id,))
                if c.rowcount == 0:
                    return _json_error('Partida no encontrada', 404)
                conexion.commit()
        return _json_ok({"partida_id": partida_id, "eliminado": True})
    except Exception as e:
        try:
            with conexion:
                with conexion.cursor() as c:
                    c.execute("UPDATE partida SET estado='eliminada' WHERE partida_id=%s", (partida_id,))
                    conexion.commit()
            return _json_ok({"partida_id": partida_id, "eliminado": False, "estado": "eliminada", "detalle_error": str(e)})
        except Exception:
            return _json_error(str(e), 500)


@apiv1_bp.post('/api_avanzarpregunta')
@jwt_required_api_enhanced
def api_avanzarpregunta():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    b = request.get_json(silent=True) or {}
    codigo = b.get('codigo_partida')
    if not codigo:
        return _json_error('codigo_partida requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("CALL avanzar_pregunta(%s)", (codigo,))
                conexion.commit()
        return _json_ok({"codigo_partida": codigo, "avanzado": True})
    except Exception as e:
        return _json_error(str(e), 500)


# ============================================================
# BLOQUE 9: PREGUNTA_PARTICIPANTE
# ============================================================

@apiv1_bp.get('/api_obtenerpreguntaparticipantes')
@jwt_required_api_enhanced
def api_obtenerpreguntaparticipantes():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    participante_id = request.args.get('participante_id', type=int)
    pregunta_id = request.args.get('pregunta_id', type=int)

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = (
                    "SELECT pregunta_participante_id, participante_id, pregunta_id, respuesta_seleccionada_id, "
                    "texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta "
                    "FROM pregunta_participante WHERE 1=1"
                )
                params = []
                if participante_id is not None:
                    sql += " AND participante_id=%s"
                    params.append(participante_id)
                if pregunta_id is not None:
                    sql += " AND pregunta_id=%s"
                    params.append(pregunta_id)

                sql += " ORDER BY pregunta_participante_id DESC"
                c.execute(sql, params)
                rows = c.fetchall()
        return _json_ok(rows)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.get('/api_obtenerpreguntaparticipanteporid')
@jwt_required_api_enhanced
def api_obtenerpreguntaparticipanteporid():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    id_reg = request.args.get('pregunta_participante_id', type=int)
    if not id_reg:
        return _json_error('pregunta_participante_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("SELECT pregunta_participante_id, participante_id, pregunta_id, respuesta_seleccionada_id, texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta FROM pregunta_participante WHERE pregunta_participante_id=%s", (id_reg,))
                row = c.fetchone()
        if not row:
            return _json_error('Registro no encontrado', 404)
        return _json_ok(row)
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_registrarpreguntaparticipante')
@jwt_required_api_enhanced
def api_registrarpreguntaparticipante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    required = ['participante_id', 'pregunta_id', 'texto_pregunta', 'correcta', 'tiempo_pregunta', 'tiempo_maximo_pregunta']

    falt = [k for k in required if body.get(k) is None or body.get(k) == '']
    if falt:
        return _json_error(f"Faltan campos: {', '.join(falt)}")

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = (
                    "INSERT INTO pregunta_participante (participante_id, pregunta_id, respuesta_seleccionada_id, texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)"
                )
                params = (
                    int(body['participante_id']),
                    int(body['pregunta_id']),
                    body.get('respuesta_seleccionada_id'),
                    body['texto_pregunta'],
                    int(body['correcta']),
                    int(body['tiempo_pregunta']),
                    int(body['tiempo_maximo_pregunta'])
                )
                c.execute(sql, params)
                conexion.commit()
                new_id = c.lastrowid
        return _json_ok({"pregunta_participante_id": new_id})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_actualizarpreguntaparticipante')
@jwt_required_api_enhanced
def api_actualizarpreguntaparticipante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    id_reg = body.get('pregunta_participante_id')
    if not id_reg:
        return _json_error('pregunta_participante_id requerido')

    campos = ['respuesta_seleccionada_id', 'correcta', 'tiempo_pregunta', 'tiempo_maximo_pregunta', 'texto_pregunta']
    sets, params = [], []

    for k in campos:
        if k in body:
            val = body[k]
            # CORRECCIÓN: Forzar NULL si el ID de respuesta es 0 o vacío
            if k == 'respuesta_seleccionada_id' and (val == 0 or val == ""):
                val = None
            sets.append(f"{k}=%s")
            params.append(val)

    if not sets:
        return _json_error('Nada para actualizar')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                sql = f"UPDATE pregunta_participante SET {', '.join(sets)} WHERE pregunta_participante_id=%s"
                params.append(id_reg)
                c.execute(sql, params)
                conexion.commit()
        return _json_ok({"pregunta_participante_id": id_reg, "actualizado": True})
    except Exception as e:
        return _json_error(str(e), 500)


@apiv1_bp.post('/api_eliminarpreguntaparticipante')
@jwt_required_api_enhanced
def api_eliminarpreguntaparticipante():
    user_data = get_user_from_jwt_or_session()
    if not user_data:
        return jsonify({'status': 'error', 'mensaje': 'No autenticado'}), 401

    body = request.get_json(silent=True) or {}
    id_reg = body.get('pregunta_participante_id')
    if not id_reg:
        return _json_error('pregunta_participante_id requerido')

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                c.execute("DELETE FROM pregunta_participante WHERE pregunta_participante_id=%s", (id_reg,))
                if c.rowcount == 0:
                    return _json_error('Registro no encontrado', 404)
                conexion.commit()
        return _json_ok({"pregunta_participante_id": id_reg, "eliminado": True})
    except Exception as e:
        return _json_error(str(e), 500)