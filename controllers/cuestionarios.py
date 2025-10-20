from flask import Blueprint, render_template, request, jsonify, session
import sys
import random
import string
import db as dbmod


def _get_logged_in_user():
    """Devuelve un dict con los datos del usuario logueado o {} si no hay sesión."""
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
        print(f"[cuestionarios] error obteniendo usuario: {e}", file=sys.stderr)
        return {}


cuestionarios_bp = Blueprint('cuestionarios', __name__, template_folder='../../templates')


@cuestionarios_bp.route('/cuestionario')
def frm_cuestionarios():
    logged = _get_logged_in_user()
    return render_template('cuestionario.html', logged_in_user=logged)


@cuestionarios_bp.route('/crearcuestionario')
def frm_editarcuestionarios():
    logged = _get_logged_in_user()
    return render_template('crearcuestionario.html', logged_in_user=logged)


@cuestionarios_bp.route('/api/cuestionarios/<int:usuario_id>', methods=['GET'])
def listar_cuestionarios(usuario_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify([])
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT c.*,
                       (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas
                FROM cuestionario c
                WHERE c.usuario_id = %s and estado=1
            """, (usuario_id,))
            data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        print(f"Error listar cuestionarios: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/api/cuestionarios_publicos', methods=['GET'])
def listar_cuestionarios_publicos():
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify([])
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT c.*,
                       (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas
                FROM cuestionario c
                WHERE c.publico = 1 AND c.estado = 1
            """)
            data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        print(f"Error listar cuestionarios publicos: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/api/cuestionarios/<int:cuestionario_id>', methods=['PUT'])
def eliminar_cuestionario(cuestionario_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la BD.'}), 500
    try:
        with conexion.cursor() as cursor:
            cursor.execute('UPDATE cuestionario set estado=0 WHERE cuestionario_id=%s', (cuestionario_id,))
            conexion.commit()
        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario eliminado lógicamente'})
    except Exception as e:
        print(f"Error eliminando cuestionario: {e}", file=sys.stderr)
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


def generar_codigo_unico(cursor):
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase, k=6))
        cursor.execute('SELECT 1 FROM cuestionario WHERE codigo_visualizacion = %s', (codigo,))
        if cursor.fetchone() is None:
            return codigo


@cuestionarios_bp.route('/api/cuestionario_completo', methods=['POST'])
def crear_cuestionario_completo():
    data = request.get_json()
    if not data or 'nombre_cuestionario' not in data or 'preguntas' not in data:
        return jsonify({'error': 'Faltan datos requeridos'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                codigo_visualizacion = generar_codigo_unico(cursor)
                url_img_cuestionario_cloud = data.get('url_img_cuestionario') or ''
                sql_cuestionario = """
                    INSERT INTO cuestionario
                    (nombre_cuestionario, descripcion, publico, modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario, codigo_visualizacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_cuestionario, (
                    data.get('nombre_cuestionario'),
                    data.get('descripcion'),
                    data.get('publico', 0),
                    data.get('modo_juego', 'C'),
                    data.get('tiempo_limite_pregunta', 30),
                    data.get('usuario_id'),
                    url_img_cuestionario_cloud,
                    codigo_visualizacion
                ))
                cuestionario_id = cursor.lastrowid

                for pregunta in data['preguntas']:
                    sql_pregunta = """
                        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                        VALUES (%s, %s, %s, %s)
                    """
                    media_url = pregunta.get('media_url')
                    cursor.execute(sql_pregunta, (
                        pregunta.get('texto_pregunta'),
                        media_url,
                        pregunta.get('tiempo_limite'),
                        cuestionario_id
                    ))
                    pregunta_id = cursor.lastrowid

                    for resp in pregunta.get('respuestas', []):
                        sql_respuesta = """
                            INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id)
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(sql_respuesta, (
                            resp.get('texto_respuesta'),
                            resp.get('estado_respuesta', 0),
                            pregunta_id
                        ))

                conexion.commit()

        return jsonify({
            'mensaje': 'Cuestionario completo creado exitosamente',
            'cuestionario_id': cuestionario_id,
            'codigo_visualizacion': codigo_visualizacion
        }), 201

    except Exception as e:
        print('Error al crear cuestionario completo:', e, file=sys.stderr)
        try:
            conexion.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/api/cuestionario_completo/<int:cuestionario_id>', methods=['GET'])
def obtener_cuestionario_completo(cuestionario_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    try:
        with conexion.cursor() as cursor:
            sql_cuestionario = """
                SELECT cuestionario_id, nombre_cuestionario, descripcion, publico,
                       modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario, codigo_visualizacion
                FROM cuestionario
                WHERE cuestionario_id = %s
            """
            cursor.execute(sql_cuestionario, (cuestionario_id,))
            cuestionario = cursor.fetchone()
            if not cuestionario:
                return jsonify({'error': 'Cuestionario no encontrado'}), 404

            sql_preguntas = """
                SELECT pregunta_id, texto_pregunta, media_url, tiempo_limite
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id ASC
            """
            cursor.execute(sql_preguntas, (cuestionario_id,))
            preguntas = cursor.fetchall()

            for pregunta in preguntas:
                sql_respuestas = """
                    SELECT respuesta_id, texto_respuesta, estado_respuesta
                    FROM respuesta
                    WHERE pregunta_id = %s
                    ORDER BY respuesta_id ASC
                """
                cursor.execute(sql_respuestas, (pregunta['pregunta_id'],))
                respuestas = cursor.fetchall()
                pregunta['respuestas'] = respuestas

        cuestionario['preguntas'] = preguntas
        return jsonify(cuestionario)
    except Exception as e:
        print(f'Error al obtener cuestionario completo: {e}', file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/verificar_codigo/<int:cuestionario_id>', methods=['POST'])
def verificar_codigo(cuestionario_id):
    """Verifica que el código enviado coincide con el código_visualizacion del cuestionario.

    Devuelve JSON {'valido': True|False} o un objeto error en caso de fallo.
    """
    data = request.get_json(silent=True)
    if not data or 'codigo' not in data:
        return jsonify({'error': 'Falta el campo "codigo" en el cuerpo'}), 400

    codigo = str(data.get('codigo', '')).strip().upper()

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute('SELECT codigo_visualizacion FROM cuestionario WHERE cuestionario_id=%s AND estado=1', (cuestionario_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Cuestionario no encontrado'}), 404

            actual = row.get('codigo_visualizacion')
            valido = False
            if actual is not None:
                valido = str(actual).strip().upper() == codigo

        return jsonify({'valido': bool(valido)})
    except Exception as e:
        print(f"Error verificar_codigo: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500
    


@cuestionarios_bp.route("/api/cuestionario_completo/<int:cuestionario_id>", methods=["PUT"])
def actualizar_cuestionario_completo(cuestionario_id):
    data = request.get_json()

    if not data or "nombre_cuestionario" not in data or "preguntas" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                url_img_cuestionario_cloud = data.get("url_img_cuestionario") or "https://img.freepik.com/vector-premium/imagen-no-es-conjunto-iconos-disponibles-simbolo-vectorial-stock-fotos-faltante-defecto-estilo-relleno-delineado-negro-signo-no-encontro-imagen_268104-6708.jpg"

                # Actualizar cuestionario
                sql_update_cuestionario = """
                    UPDATE cuestionario
                    SET nombre_cuestionario=%s,
                        descripcion=%s,
                        publico=%s,
                        modo_juego=%s,
                        tiempo_limite_pregunta=%s,
                        url_img_cuestionario=%s
                    WHERE cuestionario_id=%s
                """
                cursor.execute(sql_update_cuestionario, (
                    data.get("nombre_cuestionario"),
                    data.get("descripcion"),
                    data.get("publico", 0),
                    data.get("modo_juego", "C"),
                    data.get("tiempo_limite_pregunta", 30),
                    url_img_cuestionario_cloud,
                    cuestionario_id
                ))

                # Eliminar preguntas y respuestas previas
                cursor.execute("""
                    DELETE FROM respuesta
                    WHERE pregunta_id IN (SELECT pregunta_id FROM pregunta WHERE cuestionario_id=%s)
                """, (cuestionario_id,))
                cursor.execute("DELETE FROM pregunta WHERE cuestionario_id=%s", (cuestionario_id,))

                # Insertar nuevas preguntas
                for pregunta in data["preguntas"]:
                    cursor.execute("""
                        INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        pregunta.get("texto_pregunta"),
                        pregunta.get("media_url"),
                        pregunta.get("tiempo_limite"),
                        cuestionario_id
                    ))
                    pregunta_id = cursor.lastrowid

                    for resp in pregunta.get("respuestas", []):
                        cursor.execute("""
                            INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id)
                            VALUES (%s, %s, %s)
                        """, (
                            resp.get("texto_respuesta"),
                            resp.get("estado_respuesta", 0),
                            pregunta_id
                        ))

                conexion.commit()

        return jsonify({"mensaje": "Cuestionario actualizado exitosamente"}), 200

    except Exception as e:
        print("Error al actualizar cuestionario completo:", e, file=sys.stderr)
        conexion.rollback()
        return jsonify({"error": str(e)}), 500
