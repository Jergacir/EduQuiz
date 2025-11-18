from flask import Blueprint, render_template, request, jsonify, session
import sys
import random
import string
from auth_utils import jwt_required_api_enhanced, get_user_from_jwt_or_session
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
            sql = "SELECT usuario_id AS usuario_id, username, nombre, cant_monedas, tipo_usuario FROM usuario WHERE usuario_id=%s"
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
@jwt_required_api_enhanced
def listar_cuestionarios(usuario_id):
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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
@jwt_required_api_enhanced
def listar_cuestionarios_publicos():
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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
@jwt_required_api_enhanced
def eliminar_cuestionario(cuestionario_id):
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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
@jwt_required_api_enhanced
def crear_cuestionario_completo():
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

    data = request.get_json()
    if not data or 'nombre_cuestionario' not in data or 'preguntas' not in data:
        return jsonify({'error': 'Faltan datos requeridos'}), 400

    # 1. Obtener el ID del usuario antes de conectar
    usuario_id = data.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'Falta el ID de usuario'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                codigo_visualizacion = generar_codigo_unico(cursor)
                url_img_cuestionario_cloud = data.get('url_img_cuestionario') or ''

                # 2. Inserción del Cuestionario
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
                    usuario_id, # Usamos el usuario_id extraído
                    url_img_cuestionario_cloud,
                    codigo_visualizacion
                ))
                cuestionario_id = cursor.lastrowid

                # 3. Inserción de Preguntas y Respuestas (código original)
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

                # 🎯 4. LÓGICA AGREGADA: Sumar 5000 monedas al usuario
                sql_update_monedas = """
                    UPDATE usuario
                    SET cant_monedas = cant_monedas + 5000
                    WHERE usuario_id = %s
                """
                cursor.execute(sql_update_monedas, (usuario_id,))

                # 5. Confirmar la transacción (cuestionario e incremento de monedas)
                conexion.commit()

        return jsonify({
            'mensaje': 'Cuestionario completo creado exitosamente',
            'cuestionario_id': cuestionario_id,
            'codigo_visualizacion': codigo_visualizacion,
            'monedas_otorgadas': 5000 # Opcional: para confirmación en el frontend
        }), 201

    except Exception as e:
        print('Error al crear cuestionario completo:', e, file=sys.stderr)
        try:
            conexion.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/api/cuestionario_completo/<int:cuestionario_id>', methods=['GET'])
@jwt_required_api_enhanced
def obtener_cuestionario_completo(cuestionario_id):
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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


@cuestionarios_bp.route('/api/cuestionarios/clone/<int:cuestionario_id>', methods=['POST'])
@jwt_required_api_enhanced
def clonar_cuestionario(cuestionario_id):
    """Clona un cuestionario (estructura completa de preguntas y respuestas)
    y lo asigna al usuario logueado (session['user_id']). Devuelve el nuevo id creado.
    """
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    usuario_id = session['user_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la BD'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Obtener cuestionario original
                cursor.execute("SELECT * FROM cuestionario WHERE cuestionario_id=%s AND estado=1", (cuestionario_id,))
                origen = cursor.fetchone()
                if not origen:
                    return jsonify({'error': 'Cuestionario origen no encontrado'}), 404

                # Crear nuevo cuestionario con los mismos campos (pero nuevo codigo_visualizacion)
                codigo_visualizacion = generar_codigo_unico(cursor)
                # Inserta el cuestionario clonado. Guardamos además el id de origen
                # en la columna `origen_cuestionario_id` para poder contar clones.
                sql_insert = '''
                    INSERT INTO cuestionario (nombre_cuestionario, descripcion, publico, modo_juego, tiempo_limite_pregunta, usuario_id, url_img_cuestionario, codigo_visualizacion, origen_cuestionario_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                '''
                # Nombre como string (sin coma accidental)
                nombreCuestionario = origen.get('nombre_cuestionario') + " (Copiado)"
                cursor.execute(sql_insert, (
                    nombreCuestionario,
                    origen.get('descripcion'),
                    0,  # por seguridad clonado como privado
                    origen.get('modo_juego'),
                    origen.get('tiempo_limite_pregunta'),
                    usuario_id,
                    origen.get('url_img_cuestionario'),
                    codigo_visualizacion,
                    cuestionario_id  # referencia al origen
                ))
                nuevo_id = cursor.lastrowid

                # Clonar preguntas y respuestas
                cursor.execute('SELECT * FROM pregunta WHERE cuestionario_id=%s', (cuestionario_id,))
                preguntas = cursor.fetchall()
                for p in preguntas:
                    cursor.execute('INSERT INTO pregunta (texto_pregunta, media_url, tiempo_limite, cuestionario_id) VALUES (%s,%s,%s,%s)',
                                   (p.get('texto_pregunta'), p.get('media_url'), p.get('tiempo_limite'), nuevo_id))
                    new_preg_id = cursor.lastrowid
                    cursor.execute('SELECT * FROM respuesta WHERE pregunta_id=%s', (p.get('pregunta_id'),))
                    respuestas = cursor.fetchall()
                    for r in respuestas:
                        cursor.execute('INSERT INTO respuesta (texto_respuesta, estado_respuesta, pregunta_id) VALUES (%s,%s,%s)',
                                       (r.get('texto_respuesta'), r.get('estado_respuesta'), new_preg_id))

            conexion.commit()

        return jsonify({'status': 'ok', 'mensaje': 'Cuestionario clonado', 'nuevo_id': nuevo_id}), 201

    except Exception as e:
        print(f"Error al clonar cuestionario: {e}", file=sys.stderr)
        try:
            conexion.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500


@cuestionarios_bp.route('/verificar_codigo/<int:cuestionario_id>', methods=['POST'])
@jwt_required_api_enhanced
def verificar_codigo(cuestionario_id):
    """Verifica que el código enviado coincide con el código_visualizacion del cuestionario.

    Devuelve JSON {'valido': True|False} o un objeto error en caso de fallo.
    """
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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


@cuestionarios_bp.route('/api/cuestionario/por_codigo/<codigo>', methods=['GET'])
@jwt_required_api_enhanced
def buscar_cuestionario_por_codigo(codigo):
    """Buscar un cuestionario por su codigo_visualizacion. Devuelve {'cuestionario_id': id} o 404."""

    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    try:
        codigo_norm = str(codigo or '').strip().upper()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT cuestionario_id FROM cuestionario WHERE UPPER(TRIM(codigo_visualizacion)) = %s AND estado = 1', (codigo_norm,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Cuestionario no encontrado'}), 404
            return jsonify({'cuestionario_id': row.get('cuestionario_id')})
    except Exception as e:
        print(f"Error buscar_cuestionario_por_codigo: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500



@cuestionarios_bp.route("/api/cuestionario_completo/<int:cuestionario_id>", methods=["PUT"])
@jwt_required_api_enhanced
def actualizar_cuestionario_completo(cuestionario_id):
    # ✅ Obtener usuario (funciona tanto para Postman como navegador)
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

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
