from flask import Blueprint, request, jsonify
import sys
import db as dbmod

apiv1_bp = Blueprint('APIv1', __name__)

# ============================================================
# 1. GET api_obtenercuestionarios  → Lista todos los cuestionarios activos
# ============================================================
@apiv1_bp.route('/api_obtenercuestionarios', methods=['GET'])
def api_obtener_cuestionarios():
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM cuestionario
                WHERE estado = 1
            """)
            data = cursor.fetchall()

        return jsonify({'status': 'ok', 'data': data})

    except Exception as e:
        print("[api_obtenercuestionarios] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# 2. GET api_obtenercuestionarioporid  → Obtiene un solo cuestionario
# ============================================================
@apiv1_bp.route('/api_obtenercuestionarioporid/<int:cuestionario_id>', methods=['GET'])
def api_obtener_cuestionario_por_id(cuestionario_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM cuestionario
                WHERE cuestionario_id = %s AND estado = 1
            """, (cuestionario_id,))
            data = cursor.fetchone()

        return jsonify({'status': 'ok', 'data': data})

    except Exception as e:
        print("[api_obtenercuestionarioporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


# ============================================================
# 3. POST api_registrarcuestionario  → Insertar nuevo cuestionario
# ============================================================
@apiv1_bp.route('/api_registrarcuestionario', methods=['POST'])
def api_registrar_cuestionario():
    body = request.get_json()

    campos_requeridos = [
        'nombre_cuestionario',
        'descripcion',
        'publico',
        'modo_juego',
        'tiempo_limite_pregunta',
        'usuario_id',
        'url_img_cuestionario',
        'codigo_visualizacion'
    ]

    # Validación básica
    for campo in campos_requeridos:
        if campo not in body:
            return jsonify({'status': 'error', 'mensaje': f'Falta el campo {campo}'}), 400

    conexion = dbmod.obtenerConexion()
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
                body['nombre_cuestionario'],
                body.get('descripcion'),
                body['publico'],
                body['modo_juego'],
                body['tiempo_limite_pregunta'],
                body['usuario_id'],
                body.get('url_img_cuestionario'),
                body['codigo_visualizacion']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario registrado correctamente'})

    except Exception as e:
        print("[api_registrarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 4. POST api_actualizarcuestionario  → Modificar un cuestionario existente
# ============================================================
@apiv1_bp.route('/api_actualizarcuestionario', methods=['POST'])
def api_actualizar_cuestionario():
    body = request.get_json()

    if 'cuestionario_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'cuestionario_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE cuestionario
                SET nombre_cuestionario=%s,
                    descripcion=%s,
                    publico=%s,
                    modo_juego=%s,
                    tiempo_limite_pregunta=%s,
                    url_img_cuestionario=%s
                WHERE cuestionario_id=%s AND estado=1
            """, (
                body.get('nombre_cuestionario'),
                body.get('descripcion'),
                body.get('publico'),
                body.get('modo_juego'),
                body.get('tiempo_limite_pregunta'),
                body.get('url_img_cuestionario'),
                body['cuestionario_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario actualizado correctamente'})

    except Exception as e:
        print("[api_actualizarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 5. POST api_eliminarcuestionario  → Eliminación lógica (estado=0)
# ============================================================
@apiv1_bp.route('/api_eliminarcuestionario', methods=['POST'])
def api_eliminar_cuestionario():
    body = request.get_json()

    if 'cuestionario_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'cuestionario_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE cuestionario
                SET estado = 0
                WHERE cuestionario_id = %s
            """, (body['cuestionario_id'],))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario eliminado correctamente'})

    except Exception as e:
        print("[api_eliminarcuestionario] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

#Pregunta
# ============================================================
# 1. GET api_obtenerpreguntas → Lista todas las preguntas
# ============================================================
@apiv1_bp.route('/api_obtenerpreguntas', methods=['GET'])
def api_obtener_preguntas():
    conexion = dbmod.obtenerConexion()
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



# ============================================================
# 2. GET api_obtenerpreguntaporid/<id> → Obtener una pregunta
# ============================================================
@apiv1_bp.route('/api_obtenerpreguntaporid/<int:pregunta_id>', methods=['GET'])
def api_obtener_pregunta_por_id(pregunta_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM pregunta
                WHERE pregunta_id = %s
            """, (pregunta_id,))
            data = cursor.fetchone()

        return jsonify({'status': 'ok', 'data': data})

    except Exception as e:
        print("[api_obtenerpreguntaporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 3. POST api_registrarpregunta → Insertar nueva pregunta
# ============================================================
@apiv1_bp.route('/api_registrarpregunta', methods=['POST'])
def api_registrar_pregunta():
    body = request.get_json()

    campos_requeridos = [
        'texto_pregunta',
        'cuestionario_id'
    ]

    for campo in campos_requeridos:
        if campo not in body:
            return jsonify({'status': 'error', 'mensaje': f'Falta el campo {campo}'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                INSERT INTO pregunta (
                    texto_pregunta,
                    media_url,
                    tiempo_limite,
                    cuestionario_id
                )
                VALUES (%s, %s, %s, %s)
            """, (
                body['texto_pregunta'],
                body.get('media_url'),
                body.get('tiempo_limite'),
                body['cuestionario_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Pregunta registrada correctamente'})

    except Exception as e:
        print("[api_registrarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 4. POST api_actualizarpregunta → Actualiza datos de una pregunta
# ============================================================
@apiv1_bp.route('/api_actualizarpregunta', methods=['POST'])
def api_actualizar_pregunta():
    body = request.get_json()

    if 'pregunta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'pregunta_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                UPDATE pregunta
                SET texto_pregunta = %s,
                    media_url = %s,
                    tiempo_limite = %s,
                    cuestionario_id = %s
                WHERE pregunta_id = %s
            """, (
                body.get('texto_pregunta'),
                body.get('media_url'),
                body.get('tiempo_limite'),
                body.get('cuestionario_id'),
                body['pregunta_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Pregunta actualizada correctamente'})

    except Exception as e:
        print("[api_actualizarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 5. POST api_eliminarpregunta → Eliminación física (DELETE)
# ============================================================
@apiv1_bp.route('/api_eliminarpregunta', methods=['POST'])
def api_eliminar_pregunta():
    body = request.get_json()

    if 'pregunta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'pregunta_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                DELETE FROM pregunta
                WHERE pregunta_id = %s
            """, (body['pregunta_id'],))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Pregunta eliminada correctamente'})

    except Exception as e:
        print("[api_eliminarpregunta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500
    
#Respuesta
# ============================================================
# 1. GET api_obtenerrespuestas → Listar todas las respuestas
# ============================================================
@apiv1_bp.route('/api_obtenerrespuestas', methods=['GET'])
def api_obtener_respuestas():
    conexion = dbmod.obtenerConexion()
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



# ============================================================
# 2. GET api_obtenerrespuestaporid/<id> → Obtener respuesta por ID
# ============================================================
@apiv1_bp.route('/api_obtenerrespuestaporid/<int:respuesta_id>', methods=['GET'])
def api_obtener_respuesta_por_id(respuesta_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM respuesta
                WHERE respuesta_id = %s
            """, (respuesta_id,))
            data = cursor.fetchone()

        return jsonify({'status': 'ok', 'data': data})

    except Exception as e:
        print("[api_obtenerrespuestaporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 3. POST api_registrarrespuesta → Insertar nueva respuesta
# ============================================================
@apiv1_bp.route('/api_registrarrespuesta', methods=['POST'])
def api_registrar_respuesta():
    body = request.get_json()

    campos_requeridos = [
        'texto_respuesta',
        'estado_respuesta',
        'pregunta_id'
    ]

    for campo in campos_requeridos:
        if campo not in body:
            return jsonify({'status': 'error', 'mensaje': f'Falta el campo {campo}'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                INSERT INTO respuesta (
                    texto_respuesta,
                    estado_respuesta,
                    pregunta_id
                )
                VALUES (%s, %s, %s)
            """, (
                body['texto_respuesta'],
                body['estado_respuesta'],
                body['pregunta_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Respuesta registrada correctamente'})

    except Exception as e:
        print("[api_registrarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 4. POST api_actualizarrespuesta → Actualizar una respuesta
# ============================================================
@apiv1_bp.route('/api_actualizarrespuesta', methods=['POST'])
def api_actualizar_respuesta():
    body = request.get_json()

    if 'respuesta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'respuesta_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                UPDATE respuesta
                SET texto_respuesta = %s,
                    estado_respuesta = %s,
                    pregunta_id = %s
                WHERE respuesta_id = %s
            """, (
                body.get('texto_respuesta'),
                body.get('estado_respuesta'),
                body.get('pregunta_id'),
                body['respuesta_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Respuesta actualizada correctamente'})

    except Exception as e:
        print("[api_actualizarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 5. POST api_eliminarrespuesta → Eliminación FÍSICA
# ============================================================
@apiv1_bp.route('/api_eliminarrespuesta', methods=['POST'])
def api_eliminar_respuesta():
    body = request.get_json()

    if 'respuesta_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'respuesta_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                DELETE FROM respuesta
                WHERE respuesta_id = %s
            """, (body['respuesta_id'],))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Respuesta eliminada correctamente'})

    except Exception as e:
        print("[api_eliminarrespuesta] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500
    
#participante
# ============================================================
# 1. GET api_obtenerparticipantes → Lista todos los participantes
# ============================================================
@apiv1_bp.route('/api_obtenerparticipantes', methods=['GET'])
def api_obtener_participantes():
    conexion = dbmod.obtenerConexion()
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



# ============================================================
# 2. GET api_obtenerparticipanteporid/<id> → Obtener un participante
# ============================================================
@apiv1_bp.route('/api_obtenerparticipanteporid/<int:participante_id>', methods=['GET'])
def api_obtener_participante_por_id(participante_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM participante
                WHERE participante_id = %s
            """, (participante_id,))
            data = cursor.fetchone()

        return jsonify({'status': 'ok', 'data': data})

    except Exception as e:
        print("[api_obtenerparticipanteporid] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 3. POST api_registrarparticipante → Insertar nuevo participante
# ============================================================
@apiv1_bp.route('/api_registrarparticipante', methods=['POST'])
def api_registrar_participante():
    body = request.get_json()

    campos_requeridos = [
        'usuario_id',
        'partida_id'
    ]

    # Lo mínimo obligatorio según la tabla
    for campo in campos_requeridos:
        if campo not in body:
            return jsonify({'status': 'error', 'mensaje': f'Falta el campo {campo}'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                INSERT INTO participante (
                    puntuacion_total,
                    cant_preguntas_correctas,
                    cant_preguntas_incorrectas,
                    lider_id,
                    usuario_id,
                    partida_id,
                    grupo_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                body.get('puntuacion_total', 0.00),
                body.get('cant_preguntas_correctas', 0),
                body.get('cant_preguntas_incorrectas', 0),
                body.get('lider_id'),
                body['usuario_id'],
                body['partida_id'],
                body.get('grupo_id')
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Participante registrado correctamente'})

    except Exception as e:
        print("[api_registrarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 4. POST api_actualizarparticipante → Actualizar datos
# ============================================================
@apiv1_bp.route('/api_actualizarparticipante', methods=['POST'])
def api_actualizar_participante():
    body = request.get_json()

    if 'participante_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'participante_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                UPDATE participante
                SET puntuacion_total = %s,
                    cant_preguntas_correctas = %s,
                    cant_preguntas_incorrectas = %s,
                    lider_id = %s,
                    usuario_id = %s,
                    partida_id = %s,
                    grupo_id = %s
                WHERE participante_id = %s
            """, (
                body.get('puntuacion_total'),
                body.get('cant_preguntas_correctas'),
                body.get('cant_preguntas_incorrectas'),
                body.get('lider_id'),
                body.get('usuario_id'),
                body.get('partida_id'),
                body.get('grupo_id'),
                body['participante_id']
            ))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Participante actualizado correctamente'})

    except Exception as e:
        print("[api_actualizarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500



# ============================================================
# 5. POST api_eliminarparticipante → Eliminación FÍSICA
# ============================================================
@apiv1_bp.route('/api_eliminarparticipante', methods=['POST'])
def api_eliminar_participante():
    body = request.get_json()

    if 'participante_id' not in body:
        return jsonify({'status': 'error', 'mensaje': 'participante_id es requerido'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                DELETE FROM participante
                WHERE participante_id = %s
            """, (body['participante_id'],))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Participante eliminado correctamente'})

    except Exception as e:
        print("[api_eliminarparticipante] ERROR:", e, file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500