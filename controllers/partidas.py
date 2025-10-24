from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, abort
import sys
import db as dbmod
from datetime import datetime
import random
import string
import json
from enum import Enum

class EstadoPartida(Enum):
    """Estados posibles de una partida"""
    ESPERA = 'espera'           # Esperando jugadores
    CUENTA_REGRESIVA = 'cuenta_regresiva'  # 3, 2, 1... Let's go
    EN_CURSO = 'en_curso'       # Jugando
    ENTRE_PREGUNTAS = 'entre_preguntas'  # Mostrando resultados de pregunta
    FINALIZADA = 'finalizada'   # Juego terminado

partidas_bp = Blueprint('partidas', __name__, template_folder='../../templates')

# ====================================================================
# CACHE EN MEMORIA PARA ESTADO DE PARTIDAS (Compatible con PythonAnywhere)
# En producción real, considera usar Redis o cache de base de datos
# ====================================================================
partidas_cache = {}

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
            sql = "SELECT usuario_id, username, nombre, cant_monedas, tipo_usuario FROM usuario WHERE usuario_id=%s"
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return row or {}
    except Exception as e:
        print(f"[partidas] error obteniendo usuario: {e}", file=sys.stderr)
        return {}
    finally:
        conexion.close()


def obtener_participantes(codigo_partida):
    """Devuelve lista de participantes de una partida específica, incluyendo grupo y líder."""
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return []

    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT 
                    p.participante_id,
                    u.usuario_id,
                    u.nombre,
                    u.url_avatar,
                    p.grupo_id,
                    p.lider_id
                FROM participante p
                JOIN usuario u ON u.usuario_id = p.usuario_id
                JOIN partida pa ON pa.partida_id = p.partida_id
                WHERE pa.codigo_partida = %s
                ORDER BY p.grupo_id, u.nombre
            """
            cursor.execute(sql, (codigo_partida,))
            participantes = cursor.fetchall()
            return participantes or []
    except Exception as e:
        print(f"[partidas] Error obteniendo participantes: {e}", file=sys.stderr)
        return []
    finally:
        conexion.close()


def actualizar_timestamp_partida(codigo_partida):
    """Actualiza el timestamp de última modificación de una partida"""
    if codigo_partida not in partidas_cache:
        partidas_cache[codigo_partida] = {}
    partidas_cache[codigo_partida]['last_update'] = datetime.now().timestamp()
    partidas_cache[codigo_partida]['last_update_str'] = datetime.now().isoformat()


def validar_y_unir(codigo_partida, usuario_id):
    """
    Valida si el usuario puede unirse a la partida y lo inserta únicamente en
    la tabla participante. Retorna True si se unió o ya estaba.
    """
    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("Error: No se pudo conectar a la base de datos (validar_y_unir)", file=sys.stderr)
        return False

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT partida_id, estado FROM partida WHERE codigo_partida = %s",
                (codigo_partida,)
            )
            partida = cursor.fetchone()
            if not partida:
                return False
            if partida.get('estado') != 'espera':
                return False

            partida_id = partida['partida_id']

            cursor.execute(
                "SELECT 1 FROM participante WHERE partida_id = %s AND usuario_id = %s",
                (partida_id, usuario_id)
            )
            if cursor.fetchone():
                return True

            cursor.execute(
                "INSERT INTO participante (usuario_id, partida_id) VALUES (%s, %s)",
                (usuario_id, partida_id)
            )

            conexion.commit()
            actualizar_timestamp_partida(codigo_partida)
            return True

    except Exception as e:
        print(f"Error validar_y_unir: {e}", file=sys.stderr)
        conexion.rollback()
        return False
    finally:
        conexion.close()


# ====================================================================
# RUTAS PRINCIPALES
# ====================================================================

@partidas_bp.route('/partidas')
def frm_partidas():
    logged = _get_logged_in_user()
    return render_template('partidas.html', logged_in_user=logged)


@partidas_bp.route('/partidas_profesor')
def frm_partidas_profesor():
    logged = _get_logged_in_user()
    return render_template('partidas_profesor.html', logged_in_user=logged)


@partidas_bp.route('/jugar/<string:codigo_partida>')
def frm_jugar(codigo_partida):
    flash(f"Te has unido a la partida con código: {codigo_partida}.", 'success')
    logged = _get_logged_in_user()
    return render_template('jugar.html', codigo_partida=codigo_partida, logged_in_user=logged)


@partidas_bp.route('/previapartida/<codigo_partida>')
def vista_previa_partida(codigo_partida):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "No se pudo conectar a la base de datos")
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT p.partida_id, p.codigo_partida, p.estado, p.tipo_partida, p.num_grupos,
                       c.nombre_cuestionario, c.descripcion, c.url_img_cuestionario
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.codigo_partida = %s
            """
            cursor.execute(sql, (codigo_partida,))
            partida = cursor.fetchone()

            if not partida:
                abort(404, "Partida no encontrada")

        logged = _get_logged_in_user()
        return render_template('previapartida.html', partida=partida, logged_in_user=logged,
                             codigo_partida=partida['codigo_partida'], 
                             tipo_partida=partida['tipo_partida'], 
                             num_grupos=partida['num_grupos'])
    finally:
        conexion.close()


@partidas_bp.route('/salaespera/<string:codigo_partida>')
def frm_sala_espera(codigo_partida):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "No se pudo conectar a la base de datos")
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT partida_id, codigo_partida, tipo_partida, estado, num_grupos
                FROM partida
                WHERE codigo_partida = %s
            """
            cursor.execute(sql, (codigo_partida,))
            partida = cursor.fetchone()

            if not partida:
                abort(404, "Partida no encontrada")

        logged = _get_logged_in_user()
        return render_template(
            'salaespera.html',
            logged_in_user=logged,
            codigo_partida=codigo_partida,
            tipo_partida=partida.get('tipo_partida', 'I'),
            num_grupos=partida.get('num_grupos', 0)
        )
    finally:
        conexion.close()

# En partidas_bp.py (ruta frm_cuenta_regresiva)
@partidas_bp.route('/cuentaregresiva/<string:codigo_partida>')
def frm_cuenta_regresiva(codigo_partida):
    logged = _get_logged_in_user() # Asegúrate de que esta función devuelve el objeto de usuario completo
    return render_template(
        'cuentaregresiva.html', 
        codigo_partida=codigo_partida, 
        logged_in_user=logged # logged_in_user DEBE contener 'tipo_usuario'
    )


@partidas_bp.route('/api/partida/<string:codigo_partida>/estado')
def api_estado_partida(codigo_partida):
    logged = _get_logged_in_user()
    if not logged or not logged.get('usuario_id'):
        return {"success": False, "message": "Usuario no logueado"}, 401

    usuario_id = logged['usuario_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return {"success": False, "message": "No se pudo conectar a la base de datos"}, 500

    try:
        with conexion.cursor() as cursor:
            # Obtenemos info de participante y partida
            sql = """
                SELECT par.participante_id, par.lider_id, par.partida_id,
                       part.pregunta_actual_index, part.estado
                FROM participante par
                JOIN partida part ON par.partida_id = part.partida_id
                WHERE par.usuario_id = %s AND part.codigo_partida = %s
            """
            cursor.execute(sql, (usuario_id, codigo_partida))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "No estás en esta partida"}, 404

            # Solo devolver info necesaria al cliente
            return {
                "success": True,
                "pregunta_actual_index": row['pregunta_actual_index'],
                "es_lider": row['participante_id'] == row['lider_id'],
                "estado_partida": row['estado']
            }
    finally:
        conexion.close()

@partidas_bp.route('/api/partida/<string:codigo_partida>/estado_usuario', methods=['GET'])
def api_estado_usuario(codigo_partida):
    """
    Retorna información sobre el estado de un usuario dentro de una partida:
    - participante_id
    - grupo_id
    - es_lider (bool)
    - estado_partida
    - tipo_partida ('I' o 'G')
    - pregunta_actual_index
    - tiempo_inicio_pregunta
    """
    logged = _get_logged_in_user()
    if not logged or not logged.get('usuario_id'):
        return {"success": False, "message": "Usuario no logueado"}, 401

    usuario_id = logged['usuario_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return {"success": False, "message": "No se pudo conectar a la base de datos"}, 500

    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT 
                    part.partida_id,
                    part.estado AS estado_partida,
                    part.pregunta_actual_index,
                    part.tiempo_inicio_pregunta,
                    part.tipo_partida,          
                    par.participante_id,
                    par.grupo_id,
                    par.lider_id
                FROM participante par
                JOIN partida part ON par.partida_id = part.partida_id
                WHERE par.usuario_id = %s AND part.codigo_partida = %s
            """
            cursor.execute(sql, (usuario_id, codigo_partida))
            row = cursor.fetchone()

            if not row:
                return {"success": False, "message": "Usuario no está en la partida"}, 404

            es_lider = row['participante_id'] == row['lider_id']

            # Convertimos tipo_partida a algo más claro para el frontend
            modalidad = 'grupal' if row['tipo_partida'] == 'G' else 'individual'

            return {
                "success": True,
                "participante_id": row['participante_id'],
                "grupo_id": row['grupo_id'],
                "es_lider": es_lider,
                "estado_partida": row['estado_partida'],
                "pregunta_actual_index": row['pregunta_actual_index'],
                "modalidad": modalidad,  
                "tiempo_inicio_pregunta": (
                    row['tiempo_inicio_pregunta'].isoformat()
                    if row['tiempo_inicio_pregunta'] else None
                )
            }

    except Exception as e:
        print(f"[api_estado_usuario] Error: {e}")
        return {"success": False, "message": "Error interno"}, 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/<string:codigo_partida>/avanzar', methods=['POST'])
def api_avanzar_pregunta(codigo_partida):
    logged = _get_logged_in_user()
    if not logged or not logged.get('usuario_id'):
        return {"success": False, "message": "Usuario no logueado"}, 401

    usuario_id = logged['usuario_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return {"success": False, "message": "No se pudo conectar a la base de datos"}, 500

    try:
        with conexion.cursor() as cursor:
            # Verificar si el usuario es participante (líder o no)
            sql = """
                SELECT par.participante_id, par.lider_id, part.partida_id, part.pregunta_actual_index, part.usuario_creador_id
                FROM participante par
                JOIN partida part ON par.partida_id = part.partida_id
                WHERE par.usuario_id = %s AND part.codigo_partida = %s
            """
            cursor.execute(sql, (usuario_id, codigo_partida))
            row = cursor.fetchone()

            # Si no es participante, verificar si es el profesor creador
            if not row:
                sql_partida = """
                    SELECT partida_id, usuario_creador_id, usuario_creador_id, pregunta_actual_index
                    FROM partida
                    WHERE codigo_partida = %s
                """
                cursor.execute(sql_partida, (codigo_partida,))
                partida = cursor.fetchone()

                if not partida:
                    return {"success": False, "message": "Partida no encontrada"}, 404

                # Si es el creador, también puede avanzar
                if partida['usuario_creador_id'] == usuario_id:
                    nueva_index = partida['pregunta_actual_index'] + 1
                    sql_update = "UPDATE partida SET pregunta_actual_index = %s WHERE partida_id = %s"
                    cursor.execute(sql_update, (nueva_index, partida['partida_id']))
                    conexion.commit()
                    return {"success": True, "nueva_pregunta_index": nueva_index}
                else:
                    return {"success": False, "message": "Usuario no está en la partida"}, 404

            # Si sí es participante, verificar que sea líder
            participante_id, lider_id, partida_id, pregunta_actual_index, usuario_creador_id = row

            if participante_id != lider_id:
                return {"success": False, "message": "Solo el líder puede avanzar"}, 403

            # Avanzar la pregunta
            nueva_index = pregunta_actual_index + 1
            sql_update = "UPDATE partida SET pregunta_actual_index = %s WHERE partida_id = %s"
            cursor.execute(sql_update, (nueva_index, partida_id))
            conexion.commit()

            return {"success": True, "nueva_pregunta_index": nueva_index}

    except Exception as e:
        print(f"[api_avanzar_pregunta] Error: {e}")
        return {"success": False, "message": "Error interno"}, 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/<string:codigo_partida>/marcar_no_respondidas', methods=['POST'])
def api_marcar_no_respondidas(codigo_partida):
    logged = _get_logged_in_user()
    if not logged or not logged.get('usuario_id'):
        return {"success": False, "message": "Usuario no logueado"}, 401

    usuario_id = logged['usuario_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return {"success": False, "message": "No se pudo conectar a la base de datos"}, 500

    try:
        with conexion.cursor() as cursor:
            # 1️⃣ Obtener partida y cuestionario
            sql = """
                SELECT partida_id, cuestionario_id
                FROM partida
                WHERE codigo_partida = %s
            """
            cursor.execute(sql, (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                return {"success": False, "message": "Partida no encontrada"}, 404

            partida_id = partida['partida_id']
            cuestionario_id = partida['cuestionario_id']
            print(f"➡️ Partida encontrada: partida_id={partida_id}, cuestionario_id={cuestionario_id}")

            # 2️⃣ Obtener participantes
            cursor.execute("""
                SELECT participante_id, cant_preguntas_incorrectas
                FROM participante
                WHERE partida_id = %s
            """, (partida_id,))
            participantes = cursor.fetchall()
            print(f"➡️ Participantes encontrados: {participantes}")

            if not participantes:
                print("⚠️ No hay participantes en esta partida.")
                return {"success": False, "message": "No hay participantes en la partida"}, 404

            # 3️⃣ Obtener todas las preguntas del cuestionario
            cursor.execute("""
                SELECT pregunta_id, texto_pregunta, tiempo_limite
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id ASC
            """, (cuestionario_id,))
            preguntas = cursor.fetchall()
            print(f"➡️ Preguntas encontradas: {preguntas}")

            if not preguntas:
                print("⚠️ No hay preguntas en este cuestionario.")
                return {"success": False, "message": "No hay preguntas en el cuestionario"}, 404

            # 4️⃣ Recorrer cada participante y marcar pregunta como no respondida si no existe
            for participante in participantes:
                participante_id = participante['participante_id']
                cant_incorrectas = participante['cant_preguntas_incorrectas']

                for pregunta in preguntas:
                    pregunta_id = pregunta['pregunta_id']
                    texto_pregunta = pregunta['texto_pregunta']
                    tiempo_maximo = pregunta['tiempo_limite'] or 30  # valor por defecto si es NULL

                    # Verificar si ya existe
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM pregunta_participante
                        WHERE participante_id = %s AND pregunta_id = %s
                    """, (participante_id, pregunta_id))
                    existe = cursor.fetchone()['total']
                    print(f"participante_id={participante_id}, pregunta_id={pregunta_id}, existe={existe}")

                    if existe == 0:
                        # Insertar como no respondida
                        cursor.execute("""
                            INSERT INTO pregunta_participante (
                                participante_id, pregunta_id, respuesta_seleccionada_id,
                                texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta
                            ) VALUES (%s, %s, NULL, %s, 0, %s, %s)
                        """, (participante_id, pregunta_id, texto_pregunta, tiempo_maximo, tiempo_maximo))
                        print(f"✅ Insertado pregunta_participante para participante {participante_id}, pregunta {pregunta_id}")

                        # Actualizar participante: incrementar cant_preguntas_incorrectas
                        cursor.execute("""
                            UPDATE participante
                            SET cant_preguntas_incorrectas = cant_preguntas_incorrectas + 1
                            WHERE participante_id = %s
                        """, (participante_id,))
                        print(f"🔺 Actualizado participante {participante_id}: cant_preguntas_incorrectas +1")

            conexion.commit()
            return {"success": True, "message": "Preguntas no respondidas marcadas correctamente"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "Error interno del servidor"}, 500
    finally:
        conexion.close()

# ====================================================================
# API ENDPOINTS PARA AJAX POLLING
# ====================================================================
def obtener_pregunta_actual(codigo_partida):
    """
    Obtiene la pregunta que se está jugando actualmente.
    Retorna None si no hay pregunta activa.
    """
    # Esto requiere agregar un campo en la tabla partida:
    # ALTER TABLE partida ADD COLUMN pregunta_actual_index INT DEFAULT 0;
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return None
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.pregunta_actual_index,
                    c.cuestionario_id
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.codigo_partida = %s
            """, (codigo_partida,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Obtener preguntas del cuestionario
            cursor.execute("""
                SELECT pregunta_id, texto_pregunta, tiempo_limite
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id
            """, (result['cuestionario_id'],))
            
            preguntas = cursor.fetchall()
            index = result['pregunta_actual_index']
            
            if 0 <= index < len(preguntas):
                return preguntas[index]
            
            return None
            
    except Exception as e:
        print(f"[ERROR] obtener_pregunta_actual: {e}", file=sys.stderr)
        return None
    finally:
        conexion.close()
# ====================================================================
# MEJORADO: Endpoint de polling incluye estado de partida
# ====================================================================
@partidas_bp.route('/api/partida/<codigo_partida>/poll', methods=['GET'])
def api_poll_participantes(codigo_partida):
    """
    Polling mejorado que incluye:
    - Participantes
    - Estado de la partida
    - Pregunta actual (si está en curso)
    - Timestamp
    """
    try:
        conexion = dbmod.obtenerConexion()
        if not conexion:
            return jsonify({'success': False, 'error': 'Error de conexión'}), 500
        
        with conexion.cursor() as cursor:
            # Obtener datos de la partida (incluye índice de pregunta actual si existe)
            cursor.execute("""
                SELECT estado, cuestionario_id, COALESCE(pregunta_actual_index, 0) as pregunta_actual_index
                FROM partida 
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            partida_info = cursor.fetchone()
            print(f"[DEBUG] partida_info cruda: {partida_info}")  # <-- debug

            if not partida_info:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404
            
            # Obtener participantes
            participantes = obtener_participantes(codigo_partida)
            print(f"[DEBUG] Total participantes: {len(participantes)}")  # <-- debug
            
            # Timestamp
            timestamp = partidas_cache.get(codigo_partida, {}).get('last_update', datetime.now().timestamp())
            
            response_data = {
                'success': True,
                'participantes': participantes,
                'estado_partida': partida_info['estado'],
                'timestamp': timestamp,
                'total': len(participantes)
            }
            
            # Incluir índice de pregunta actual
            pregunta_actual_index = partida_info.get('pregunta_actual_index', 0)
            response_data['pregunta_actual'] = pregunta_actual_index
            print(f"[DEBUG] pregunta_actual_index enviado: {pregunta_actual_index}")  # <-- debug

            # Si está en curso, incluir además el objeto pregunta
            estados_en_curso = {EstadoPartida.EN_CURSO.value, 'en_juego', EstadoPartida.CUENTA_REGRESIVA.value}
            if partida_info['estado'] in estados_en_curso:
                pregunta_obj = obtener_pregunta_actual(codigo_partida)
                print(f"[DEBUG] pregunta_obj obtenido: {pregunta_obj}")  # <-- debug
                if pregunta_obj:
                    response_data['pregunta_obj'] = pregunta_obj
            
            return jsonify(response_data), 200
        
    except Exception as e:
        print(f"[ERROR] api_poll_participantes: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conexion:
            conexion.close()


@partidas_bp.route('/api/partida/<codigo_partida>/participantes')
def api_participantes(codigo_partida):
    """Endpoint legacy - redirige al endpoint de polling"""
    return api_poll_participantes(codigo_partida)


@partidas_bp.route('/api/partida/<codigo_partida>/info')
def api_info_partida(codigo_partida):
    """Devuelve información de la partida y del cuestionario asociado (para fallback del profesor)."""
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT p.partida_id, p.codigo_partida, p.estado, p.cuestionario_id, c.nombre_cuestionario, c.descripcion
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.codigo_partida = %s
            """, (codigo_partida,))
            partida = cursor.fetchone()

            if not partida:
                return jsonify({'success': False, 'message': 'Partida no encontrada'}), 404

            # Obtener preguntas y respuestas básicas
            cursor.execute("""
                SELECT preg.pregunta_id, preg.texto_pregunta, preg.media_url, preg.tiempo_limite,
                       (SELECT COUNT(*) FROM respuesta r WHERE r.pregunta_id = preg.pregunta_id) as total_respuestas
                FROM pregunta preg
                WHERE preg.cuestionario_id = %s
                ORDER BY preg.pregunta_id
            """, (partida['cuestionario_id'],))
            preguntas = cursor.fetchall() or []

            preguntas_list = []
            for preg in preguntas:
                cursor.execute("SELECT respuesta_id, texto_respuesta FROM respuesta WHERE pregunta_id = %s ORDER BY respuesta_id", (preg['pregunta_id'],))
                respuestas = cursor.fetchall() or []
                preguntas_list.append({
                    'pregunta_id': preg['pregunta_id'],
                    'texto_pregunta': preg['texto_pregunta'],
                    'media_url': preg.get('media_url'),
                    'tiempo_limite': preg.get('tiempo_limite'),
                    'respuestas': respuestas
                })

            return jsonify({
                'success': True,
                'partida': partida,
                'cuestionario': {
                    'cuestionario_id': partida['cuestionario_id'],
                    'nombre_cuestionario': partida['nombre_cuestionario'],
                    'descripcion': partida.get('descripcion'),
                    'preguntas': preguntas_list
                }
            }), 200

    except Exception as e:
        print(f"[ERROR] api_info_partida: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/unirse', methods=['POST'])
def api_unirse_partida():
    """Endpoint para que un usuario se una a una partida"""
    data = request.get_json() or {}
    usuario_id = session.get('user_id')
    codigo_partida = data.get('codigo')

    if not codigo_partida or not usuario_id:
        return jsonify({
            "success": False, 
            "message": "Faltan el código de partida o el ID de usuario."
        }), 400

    if validar_y_unir(codigo_partida, usuario_id):
        return jsonify({
            "success": True,
            "message": "¡Te has unido a la partida!",
            "redirect_url": url_for('partidas.frm_sala_espera', codigo_partida=codigo_partida)
        }), 200

    return jsonify({
        "success": False, 
        "message": "Código de partida inválido o partida llena."
    }), 400


@partidas_bp.route('/api/partida/salir', methods=['POST'])
def api_salir_partida():
    """Endpoint para que un usuario salga de una partida"""
    data = request.get_json() or {}
    codigo_partida = data.get('codigo_partida')
    usuario_id = data.get('usuario_id')

    if not codigo_partida or not usuario_id:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT partida_id, usuario_creador_id FROM partida WHERE codigo_partida=%s", 
                (codigo_partida,)
            )
            partida = cursor.fetchone()
            
            if not partida:
                return jsonify({"success": False, "message": "Partida no encontrada"}), 404
                
            # No eliminar al creador
            if int(usuario_id) != int(partida.get('usuario_creador_id')):
                cursor.execute(
                    "DELETE FROM participante WHERE partida_id=%s AND usuario_id=%s",
                    (partida['partida_id'], usuario_id)
                )
                conexion.commit()
                actualizar_timestamp_partida(codigo_partida)
                
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"[ERROR] api_salir_partida: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/<codigo_partida>/unirse_grupo', methods=['POST'])
def api_unirse_grupo(codigo_partida):
    """Endpoint para que un alumno se una a un grupo específico"""
    data = request.get_json() or {}
    usuario_id = data.get('usuario_id')
    grupo_id = data.get('grupo_id')

    if not usuario_id or not grupo_id:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            # Obtener partida_id
            cursor.execute("SELECT partida_id FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                return jsonify({"success": False, "message": "Partida no encontrada"}), 404

            partida_id = partida["partida_id"]

            # Actualizar grupo del participante y quitar líder anterior
            cursor.execute("""
                UPDATE participante
                SET grupo_id = %s, lider_id = NULL
                WHERE partida_id = %s AND usuario_id = %s
            """, (grupo_id, partida_id, usuario_id))

            # Verificar si el grupo ya tiene un líder
            cursor.execute("""
                SELECT DISTINCT lider_id 
                FROM participante 
                WHERE partida_id = %s AND grupo_id = %s AND lider_id IS NOT NULL
                LIMIT 1
            """, (partida_id, grupo_id))
            lider_existente = cursor.fetchone()

            # Si hay líder, asignarlo al nuevo participante
            if lider_existente and lider_existente["lider_id"]:
                cursor.execute("""
                    UPDATE participante
                    SET lider_id = %s
                    WHERE partida_id = %s AND usuario_id = %s
                """, (lider_existente["lider_id"], partida_id, usuario_id))

            conexion.commit()
            actualizar_timestamp_partida(codigo_partida)

            return jsonify({"success": True, "message": "Te has unido al grupo"}), 200

    except Exception as e:
        print(f"[ERROR] api_unirse_grupo: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/<codigo_partida>/designar_lider', methods=['POST'])
def api_designar_lider(codigo_partida):
    """Endpoint para que el profesor designe un líder de grupo"""
    data = request.get_json() or {}
    grupo_id = data.get("grupo_id")
    lider_participante_id = data.get("lider_participante_id")

    if not grupo_id or not lider_participante_id:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT partida_id FROM partida WHERE codigo_partida = %s",
                (codigo_partida,)
            )
            partida = cursor.fetchone()
            if not partida:
                return jsonify({"success": False, "message": "Partida no encontrada"}), 404

            partida_id = partida["partida_id"]

            # Actualizar líder para todos los miembros del grupo
            cursor.execute("""
                UPDATE participante
                SET lider_id = %s
                WHERE partida_id = %s AND grupo_id = %s
            """, (lider_participante_id, partida_id, grupo_id))
            
            conexion.commit()
            actualizar_timestamp_partida(codigo_partida)

            return jsonify({"success": True, "message": "Líder designado correctamente"}), 200

    except Exception as e:
        print(f"[ERROR] api_designar_lider: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conexion.close()


# CAMBIAR ES ESTADO DE LA PARTIDA: esperando -> iniciar
@partidas_bp.route('/api/partida/iniciar', methods=['POST'])
def api_iniciar_partida():
    """
    Endpoint para que el profesor cambie el estado de la partida a 'en_juego'.
    """
    data = request.get_json() or {}
    codigo_partida = data.get('codigo_partida')
    usuario = _get_logged_in_user()

    if not codigo_partida or not usuario:
        return jsonify({"success": False, "message": "Datos o autenticación incompletos"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            # 1. Verificar que el usuario sea el creador de la partida
            cursor.execute(
                "SELECT partida_id, usuario_creador_id FROM partida WHERE codigo_partida = %s",
                (codigo_partida,)
            )
            partida_info = cursor.fetchone()

            if not partida_info:
                return jsonify({"success": False, "message": "Partida no encontrada"}), 404

            if partida_info['usuario_creador_id'] != usuario['usuario_id']:
                return jsonify({"success": False, "message": "Solo el creador puede iniciar la partida"}), 403

            # 2. Actualizar el estado a 'cuenta_regresiva' para que alumnos vean la pantalla de "Prepárate..."
            cursor.execute(
                "UPDATE partida SET estado = %s WHERE codigo_partida = %s",
                (EstadoPartida.CUENTA_REGRESIVA.value, codigo_partida)
            )
            conexion.commit()
            actualizar_timestamp_partida(codigo_partida) # Notificar a los participantes (polling)

            return jsonify({"success": True, "message": "Partida iniciada"}), 200

    except Exception as e:
        print(f"[ERROR] api_iniciar_partida: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conexion.close()


# ====================================================================
# CREAR PARTIDA
# ====================================================================

def generar_codigo_unico(cursor, longitud=6):
    """Genera un código aleatorio de 6 dígitos único"""
    while True:
        codigo = ''.join(random.choices(string.digits, k=longitud))
        cursor.execute("SELECT 1 FROM partida WHERE codigo_partida = %s", (codigo,))
        if not cursor.fetchone():
            return codigo


@partidas_bp.route('/api/partidas/crear', methods=['POST'])
def crear_partida():
    """Endpoint para crear una nueva partida"""
    data = request.get_json()
    usuario = _get_logged_in_user()
    
    if not usuario:
        return jsonify({'status': 'error', 'mensaje': 'Usuario no autenticado'}), 401

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la base de datos'}), 500

    try:
        with conexion.cursor() as cursor:
            # Generar o validar código
            codigo_partida = data.get('pin')
            if not codigo_partida:
                codigo_partida = generar_codigo_unico(cursor)
            else:
                cursor.execute("SELECT 1 FROM partida WHERE codigo_partida = %s", (codigo_partida,))
                if cursor.fetchone():
                    return jsonify({'status': 'error', 'mensaje': 'El código ya existe'}), 400

            # Determinar tipo de partida
            modalidad = data.get('modalidad', 'I').upper()
            tipo_partida = 'G' if modalidad == 'G' else 'I'
            num_grupos = int(data.get('num_grupos', 0))

            # Insertar partida
            sql_insert = """
                INSERT INTO partida 
                (codigo_partida, cuestionario_id, usuario_creador_id, estado, tipo_partida, fecha_creacion, num_grupos)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql_insert, (
                codigo_partida,
                data.get('cuestionario_id'),
                usuario['usuario_id'],
                'espera',
                tipo_partida,
                num_grupos
            ))
            conexion.commit()
            partida_id = cursor.lastrowid
            
            # Inicializar cache
            actualizar_timestamp_partida(codigo_partida)

        return jsonify({
            'status': 'ok',
            'mensaje': 'Partida creada exitosamente',
            'codigo_partida': codigo_partida,
            'partida_id': partida_id
        }), 201
        
    except Exception as e:
        print(f"[ERROR] crear_partida: {e}", file=sys.stderr)
        try:
            conexion.rollback()
        except:
            pass
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500
    finally:
        conexion.close()


# ====================================================================
# RESULTADOS Y EXPORTACIÓN
# ====================================================================

@partidas_bp.route('/resultados_partida/<int:partida_id>')
def frm_resultados_partida(partida_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "No se pudo conectar a la base de datos")

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT p.partida_id, p.codigo_partida, p.estado, p.tipo_partida, 
                       c.nombre_cuestionario, c.descripcion
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.partida_id = %s
            """, (partida_id,))
            partida_info = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    u.nombre AS jugador,
                    u.url_avatar AS avatar,
                    pa.puntuacion_total,
                    pa.cant_preguntas_correctas,
                    pa.cant_preguntas_incorrectas
                FROM participante pa
                JOIN usuario u ON u.usuario_id = pa.usuario_id
                WHERE pa.partida_id = %s
                ORDER BY pa.puntuacion_total DESC
            """, (partida_id,))
            ranking = cursor.fetchall() or []

        logged = _get_logged_in_user()

        return render_template(
            'resultados_partida.html',
            partida_info=partida_info,
            partida_id=partida_id,
            ranking=ranking,
            logged_in_user=logged
        )
    finally:
        conexion.close()


@partidas_bp.route('/podio/<string:codigo_partida>')
def frm_podio_partida(codigo_partida):
    """
    Renderiza la pantalla del podio final para una partida dada.
    El frontend (`templates/podio.html`) se encargará de obtener el ranking real
    mediante `/api/partida/<codigo_partida>/ranking` si necesita datos.
    """
    logged = _get_logged_in_user()
    # No hacemos consultas complejas aquí; el template puede pedir los datos via AJAX
    return render_template('podio.html', codigo_partida=codigo_partida, logged_in_user=logged)


@partidas_bp.route('/exportar_resultados/<int:partida_id>')
def frm_exportar_resultados(partida_id):
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "No se pudo conectar a la base de datos")

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT p.partida_id, c.nombre_cuestionario
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.partida_id = %s
            """, (partida_id,))
            partida_info = cursor.fetchone()

        campos_disponibles = [
            {"nombre": "Nombre del Jugador", "valor": "nombre"},
            {"nombre": "Puntaje Total", "valor": "puntuacion_total"},
            {"nombre": "Preguntas Correctas", "valor": "cant_preguntas_correctas"},
            {"nombre": "Preguntas Incorrectas", "valor": "cant_preguntas_incorrectas"},
            {"nombre": "Código de Partida", "valor": "codigo_partida"},
        ]

        logged = _get_logged_in_user()

        return render_template(
            'exportar_resultados.html',
            partida_id=partida_id,
            partida_info=partida_info,
            campos_disponibles=campos_disponibles,
            logged_in_user=logged
        )
    finally:
        conexion.close()

# En partidas_bp.py (o donde manejes tus rutas)

@partidas_bp.route('/preguntasprofesor/<string:codigo_partida>')
def frm_preguntas_profesor(codigo_partida):
    """Renderiza la vista principal de juego para el profesor."""
    # Aquí puedes añadir lógica de carga de la primera pregunta
    return render_template(
        'preguntasprofesor.html', 
        codigo_partida=codigo_partida, 
        # ... datos adicionales ...
    )

@partidas_bp.route('/preguntasalumno/<string:codigo_partida>')
def frm_preguntas_alumno(codigo_partida):
    """Renderiza la vista de juego para el alumno"""
    usuario_id = session.get('user_id')
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "Error de conexión")
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT pa.participante_id
                FROM participante pa
                JOIN partida p ON pa.partida_id = p.partida_id
                WHERE p.codigo_partida = %s AND pa.usuario_id = %s
            """, (codigo_partida, usuario_id))
            
            result = cursor.fetchone()
            participante_id = result['participante_id'] if result else None
            
            if not participante_id:
                abort(404, "No eres participante de esta partida")
        
        logged = _get_logged_in_user()
        
        return render_template(
            'preguntasalumno.html',
            codigo_partida=codigo_partida,
            participante_id=participante_id,
            logged_in_user=logged
        )
    finally:
        conexion.close()


@partidas_bp.route('/respuesta_alumno/<string:codigo_partida>')
def frm_respuesta_alumno(codigo_partida):
    """Renderiza la pantalla de feedback individual del alumno (respuesta correcta/incorrecta)."""
    usuario_id = session.get('user_id')
    if not usuario_id:
        abort(403, "Usuario no autenticado")

    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "Error de conexión")

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT pa.participante_id, pa.puntuacion_total, pa.cant_preguntas_correctas, pa.cant_preguntas_incorrectas,
                       u.nombre AS usuario_nombre, u.url_avatar
                FROM participante pa
                JOIN usuario u ON pa.usuario_id = u.usuario_id
                JOIN partida p ON pa.partida_id = p.partida_id
                WHERE p.codigo_partida = %s AND pa.usuario_id = %s
            """, (codigo_partida, usuario_id))

            info = cursor.fetchone()
            if not info:
                abort(404, "No eres participante de esta partida")

            # Obtener índice de pregunta actual para mostrar número de pregunta
            cursor.execute("""
                SELECT COALESCE(pregunta_actual_index, 0) as pregunta_actual_index, p.partida_id, p.cuestionario_id
                FROM partida p
                WHERE p.codigo_partida = %s
            """, (codigo_partida,))
            partida_row = cursor.fetchone() or {}
            pregunta_index = partida_row.get('pregunta_actual_index', 0)

            # Obtener pregunta_id correspondiente al índice
            pregunta_id = None
            if partida_row.get('cuestionario_id') is not None:
                cursor.execute("""
                    SELECT pregunta_id
                    FROM pregunta
                    WHERE cuestionario_id = %s
                    ORDER BY pregunta_id
                    LIMIT 1 OFFSET %s
                """, (partida_row['cuestionario_id'], pregunta_index))
                preg_row = cursor.fetchone()
                if preg_row:
                    pregunta_id = preg_row.get('pregunta_id')

            # Obtener la respuesta del participante para esa pregunta (si existe)
            ultima_correcta = None
            if pregunta_id and info.get('participante_id'):
                cursor.execute("""
                    SELECT correcta
                    FROM pregunta_participante
                    WHERE participante_id = %s AND pregunta_id = %s
                    LIMIT 1
                """, (info['participante_id'], pregunta_id))
                pp = cursor.fetchone()
                if pp is not None:
                    ultima_correcta = bool(pp.get('correcta'))

            # Construir valores para la plantilla
            last_correct = True if ultima_correcta else False
            streak = info.get('cant_preguntas_correctas', 0)
            # Puntos por acierto (usar 900 para coincidir con el diseño; ajusta si tu lógica es distinta)
            points_earned = 900 if ultima_correcta else 0
            question_number = pregunta_index + 1

        logged = _get_logged_in_user()

        return render_template(
            'respuesta_alumno.html',
            codigo_partida=codigo_partida,
            participante_id=info.get('participante_id'),
            usuario_nombre=info.get('usuario_nombre'),
            usuario_avatar=info.get('url_avatar') or '/static/img/default.png',
            puntuacion_total=info.get('puntuacion_total') or 0,
            cant_correctas=info.get('cant_preguntas_correctas') or 0,
            cant_incorrectas=info.get('cant_preguntas_incorrectas') or 0,
            question_number=question_number,
            points_earned=points_earned,
            last_correct=last_correct,
            streak=streak,
            logged_in_user=logged
        )

    finally:
        conexion.close()


@partidas_bp.route('/ranking/<string:codigo_partida>')
def frm_ranking_partida(codigo_partida):
    """Renderiza la pantalla de ranking para la partida. Profesor ve el botón 'Continuar'."""
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "Error de conexión")

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT partida_id, codigo_partida, usuario_creador_id, estado, tipo_partida
                FROM partida
                WHERE codigo_partida = %s
            """, (codigo_partida,))

            partida = cursor.fetchone()
            if not partida:
                abort(404, "Partida no encontrada")

        logged = _get_logged_in_user()
        es_profesor = False
        
        try:
            if logged and partida and int(logged.get('usuario_id', 0)) == int(partida.get('usuario_creador_id', 0)):
                es_profesor = True
        except Exception:
            es_profesor = False
        # Determinar si la partida es grupal
        es_grupal = partida.get('tipo_partida', 'I') == 'G'

        return render_template('ranking.html', codigo_partida=codigo_partida, es_profesor=es_profesor, es_grupal=es_grupal,logged_in_user=logged)
    finally:
        conexion.close()


@partidas_bp.route('/api/exportar_partida/<int:partida_id>', methods=['POST'])
def api_exportar_partida(partida_id):
    data = request.get_json() or {}
    formato = data.get('formato', 'csv')
    campos = data.get('campos', [])
    print(f"Exportando partida #{partida_id} a {formato} con campos: {campos}")
    return jsonify({'success': True, 'message': f'Partida {partida_id} exportada como {formato}.'})


# ====================================================================
# NUEVO: Endpoint para cambiar estado de partida
# ====================================================================
@partidas_bp.route('/api/partida/<codigo_partida>/estado', methods=['POST'])
def api_cambiar_estado_partida(codigo_partida):
    """
    Cambia el estado de la partida (solo profesor).
    Body: { "nuevo_estado": "cuenta_regresiva" | "en_curso" | "finalizada" }
    """
    data = request.get_json() or {}
    nuevo_estado = data.get('nuevo_estado')
    
    # Validar usuario
    usuario = _get_logged_in_user()
    if not usuario or usuario['tipo_usuario'] != 'P':
        return jsonify({'success': False, 'message': 'Solo profesores pueden cambiar el estado'}), 403
    
    # Validar estado
    estados_validos = [e.value for e in EstadoPartida]
    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        with conexion.cursor() as cursor:
            # Verificar que la partida existe y el profesor es el creador
            cursor.execute("""
                SELECT partida_id, usuario_creador_id, estado 
                FROM partida 
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'message': 'Partida no encontrada'}), 404
            
            if partida['usuario_creador_id'] != usuario['usuario_id']:
                return jsonify({'success': False, 'message': 'No eres el creador de esta partida'}), 403
            
            # Actualizar estado
            cursor.execute("""
                UPDATE partida 
                SET estado = %s 
                WHERE codigo_partida = %s
            """, (nuevo_estado, codigo_partida))
            
            conexion.commit()
            
            # Actualizar timestamp para polling
            actualizar_timestamp_partida(codigo_partida)
            
            return jsonify({
                'success': True, 
                'estado_anterior': partida['estado'],
                'nuevo_estado': nuevo_estado,
                'timestamp': datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        print(f"[ERROR] api_cambiar_estado_partida: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conexion.close()

# controllers/partidas.py (añadir estos endpoints)

@partidas_bp.route('/api/partida/<codigo_partida>/respuestas_recibidas', methods=['GET'])
def api_obtener_respuestas_recibidas(codigo_partida):
    """
    Obtiene la cantidad de respuestas recibidas en la pregunta actual
    """
    pregunta_index = request.args.get('pregunta_index', 0, type=int)
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500
    
    try:
        with conexion.cursor() as cursor:
            # Obtener partida
            cursor.execute("""
                SELECT partida_id, pregunta_actual_index, cuestionario_id
                FROM partida
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404
            
            # Obtener pregunta actual según índice
            cursor.execute("""
                SELECT pregunta_id
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id
                LIMIT 1 OFFSET %s
            """, (partida['cuestionario_id'], pregunta_index))
            
            pregunta = cursor.fetchone()
            if not pregunta:
                return jsonify({'success': False, 'error': 'Pregunta no encontrada'}), 404
            
            # Contar solo respuestas que realmente se enviaron
            cursor.execute("""
                SELECT COUNT(DISTINCT pp.participante_id) as total
                FROM pregunta_participante pp
                JOIN participante p ON pp.participante_id = p.participante_id
                WHERE p.partida_id = %s
                  AND pp.pregunta_id = %s
                  AND pp.respuesta_seleccionada_id IS NOT NULL
            """, (partida['partida_id'], pregunta['pregunta_id']))
            
            result = cursor.fetchone()
            respuestas_recibidas = result['total'] if result else 0
            
            return jsonify({
                'success': True,
                'respuestas_recibidas': respuestas_recibidas
            }), 200
            
    except Exception as e:
        print(f"[ERROR] api_obtener_respuestas_recibidas: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conexion.close()



# =========================================================================
# NUEVO ENDPOINT: Obtener pregunta actual
# =========================================================================
@partidas_bp.route('/api/partida/<codigo_partida>/pregunta_actual', methods=['GET'])
def api_obtener_pregunta_actual(codigo_partida):
    """
    Obtiene la pregunta que se está mostrando actualmente en la partida.
    Retorna la pregunta con sus respuestas.
    """
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500
    
    try:
        with conexion.cursor() as cursor:
            # Obtener datos de la partida
            cursor.execute("""
                SELECT 
                    p.pregunta_actual_index,
                    p.cuestionario_id,
                    p.tiempo_inicio_pregunta
                FROM partida p
                WHERE p.codigo_partida = %s
            """, (codigo_partida,))
            
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404
            
            pregunta_index = partida['pregunta_actual_index']
            cuestionario_id = partida['cuestionario_id']
            
            # Obtener todas las preguntas del cuestionario
            cursor.execute("""
                SELECT 
                    pregunta_id, 
                    texto_pregunta, 
                    media_url, 
                    tiempo_limite
                FROM pregunta
                WHERE cuestionario_id = %s
                ORDER BY pregunta_id ASC
            """, (cuestionario_id,))
            
            preguntas = cursor.fetchall()
            
            if pregunta_index >= len(preguntas):
                return jsonify({
                    'success': True,
                    'finalizada': True,
                    'message': 'No hay más preguntas'
                }), 200
            
            # Obtener la pregunta actual
            pregunta = preguntas[pregunta_index]
            
            # Obtener respuestas de la pregunta
            cursor.execute("""
                SELECT 
                    respuesta_id,
                    texto_respuesta,
                    estado_respuesta
                FROM respuesta
                WHERE pregunta_id = %s
                ORDER BY respuesta_id ASC
            """, (pregunta['pregunta_id'],))
            
            respuestas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'pregunta': {
                    'pregunta_id': pregunta['pregunta_id'],
                    'texto_pregunta': pregunta['texto_pregunta'],
                    'media_url': pregunta['media_url'],
                    'tiempo_limite': pregunta['tiempo_limite'],
                    'respuestas': respuestas
                },
                'pregunta_actual': pregunta_index,
                'total_preguntas': len(preguntas)
            }), 200
            
    except Exception as e:
        print(f"[ERROR] api_obtener_pregunta_actual: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conexion.close()


@partidas_bp.route('/api/partida/<codigo_partida>/ranking', methods=['GET'])
def api_obtener_ranking(codigo_partida):
    """Devuelve el ranking de la partida (lista de participantes ordenada por puntuacion_total)."""
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500

    try:
        with conexion.cursor() as cursor:
            # Obtener partida_id
            cursor.execute("SELECT partida_id FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404

            partida_id = partida['partida_id']

            cursor.execute("""
                SELECT pa.participante_id, pa.usuario_id, u.nombre as nombre, COALESCE(u.url_avatar, '') as avatar,
                       COALESCE(pa.puntuacion_total, 0) as puntuacion_total,
                       COALESCE(pa.cant_preguntas_correctas, 0) as cant_correctas,
                       COALESCE(pa.cant_preguntas_incorrectas, 0) as cant_incorrectas,
                    CASE 
                        WHEN pa.lider_id IS NULL OR pa.lider_id = pa.participante_id THEN 1
                        ELSE 0
                    END AS es_lider
                FROM participante pa
                JOIN usuario u ON pa.usuario_id = u.usuario_id
                WHERE pa.partida_id = %s
                ORDER BY pa.puntuacion_total DESC, u.nombre ASC
            """, (partida_id,))

            rows = cursor.fetchall() or []

            ranking = []
            for r in rows:
                ranking.append({
                    'participante_id': r.get('participante_id'),
                    'usuario_id': r.get('usuario_id'),
                    'name': r.get('nombre'),
                    'avatarUrl': r.get('avatar') or '/static/img/avatar.jpeg',
                    'score': r.get('puntuacion_total') or 0,
                    'correct': r.get('cant_correctas') or 0,
                    'incorrect': r.get('cant_incorrectas') or 0,
                    'es_lider': bool(r.get('es_lider', 0))
                })

            return jsonify({'success': True, 'ranking': ranking}), 200

    except Exception as e:
        print(f"[ERROR] api_obtener_ranking: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conexion.close()


# =========================================================================
# NUEVO ENDPOINT: Registrar respuesta de participante (versión 100% diccionario)
# =========================================================================
@partidas_bp.route('/api/juego/responder', methods=['POST'])
def api_responder_pregunta():
    data = request.get_json() or {}

    participante_id = data.get('participante_id')
    pregunta_id = data.get('pregunta_id')
    respuesta_id = data.get('respuesta_seleccionada_id')
    tiempo_respuesta = data.get('tiempo_respuesta', 0)

    if not participante_id or not pregunta_id:
        return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500

    try:
        with conexion.cursor() as cursor:
            # 1️⃣ Obtener participante
            cursor.execute("""
                SELECT participante_id, lider_id, partida_id, grupo_id
                FROM participante
                WHERE participante_id = %s
            """, (participante_id,))
            participante = cursor.fetchone()
            if not participante:
                return jsonify({'success': False, 'message': 'Participante no encontrado'}), 404

            participante_id_db = participante["participante_id"]
            lider_id = participante["lider_id"]
            partida_id = participante["partida_id"]
            grupo_id = participante["grupo_id"]

            # 2️⃣ Verificar si ya respondió
            cursor.execute("""
                SELECT 1 FROM pregunta_participante
                WHERE participante_id = %s AND pregunta_id = %s
            """, (participante_id, pregunta_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Ya respondiste esta pregunta'}), 400

            # 3️⃣ Obtener texto y límite de tiempo de la pregunta
            cursor.execute("""
                SELECT texto_pregunta, tiempo_limite
                FROM pregunta
                WHERE pregunta_id = %s
            """, (pregunta_id,))
            pregunta = cursor.fetchone()
            if not pregunta:
                return jsonify({'success': False, 'message': 'Pregunta no encontrada'}), 404

            texto_pregunta = pregunta["texto_pregunta"]
            tiempo_limite = pregunta["tiempo_limite"]

            # 4️⃣ Verificar si la respuesta es correcta
            correcta = 0
            if respuesta_id:
                cursor.execute("""
                    SELECT estado_respuesta 
                    FROM respuesta
                    WHERE respuesta_id = %s AND pregunta_id = %s
                """, (respuesta_id, pregunta_id))
                respuesta = cursor.fetchone()
                if respuesta and respuesta["estado_respuesta"] == 1:
                    correcta = 1

            # 5️⃣ Insertar la respuesta del participante
            cursor.execute("""
                INSERT INTO pregunta_participante (
                    participante_id, pregunta_id, respuesta_seleccionada_id,
                    texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                participante_id, pregunta_id, respuesta_id,
                texto_pregunta, correcta, tiempo_respuesta, tiempo_limite
            ))

            # 6️⃣ Actualizar estadísticas
            if correcta == 1:
                cursor.execute("""
                    UPDATE participante
                    SET cant_preguntas_correctas = cant_preguntas_correctas + 1,
                        puntuacion_total = puntuacion_total + 1000
                    WHERE participante_id = %s
                """, (participante_id,))
            else:
                cursor.execute("""
                    UPDATE participante
                    SET cant_preguntas_incorrectas = cant_preguntas_incorrectas + 1
                    WHERE participante_id = %s
                """, (participante_id,))

            # 7️⃣ Replicar si es líder
            if lider_id == participante_id_db:
                print(f"[DEBUG] {participante_id_db} es líder — se intentará replicar su respuesta", file=sys.stderr)

                cursor.execute("""
                    SELECT participante_id
                    FROM participante
                    WHERE lider_id = %s
                      AND partida_id = %s
                      AND participante_id != %s
                """, (participante_id_db, partida_id, participante_id_db))
                miembros = [row["participante_id"] for row in cursor.fetchall()]
                print(f"[DEBUG] Miembros detectados para replicar: {miembros}", file=sys.stderr)

                if miembros:
                    cursor.execute("""
                        INSERT INTO pregunta_participante (
                            participante_id, pregunta_id, respuesta_seleccionada_id,
                            texto_pregunta, correcta, tiempo_pregunta, tiempo_maximo_pregunta
                        )
                        SELECT p.participante_id, %s, %s, %s, %s, %s, %s
                        FROM participante p
                        WHERE p.lider_id = %s
                          AND p.partida_id = %s
                          AND p.participante_id != %s
                          AND NOT EXISTS (
                              SELECT 1 FROM pregunta_participante pp
                              WHERE pp.participante_id = p.participante_id
                                AND pp.pregunta_id = %s
                          )
                    """, (
                        pregunta_id, respuesta_id, texto_pregunta, correcta,
                        tiempo_respuesta, tiempo_limite,
                        participante_id_db, partida_id, participante_id_db, pregunta_id
                    ))
                    print("[DEBUG] Réplica ejecutada correctamente.", file=sys.stderr)
                else:
                    print("[DEBUG] No hay miembros para replicar.", file=sys.stderr)

            conexion.commit()
            return jsonify({'success': True, 'message': 'Respuesta registrada', 'correcta': bool(correcta)}), 200

    except Exception as e:
        import traceback
        print("[ERROR] api_responder_pregunta:", e)
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        conexion.close()


# =========================================================================
# NUEVO ENDPOINT: Finalizar partida
# =========================================================================
@partidas_bp.route('/api/partida/finalizar', methods=['POST'])
def api_finalizar_partida():
    """
    Marca una partida como finalizada y retorna el ID para ver resultados.
    Body: { codigo_partida: str }
    """
    data = request.get_json() or {}
    codigo_partida = data.get('codigo_partida')
    
    if not codigo_partida:
        return jsonify({'success': False, 'message': 'Falta código de partida'}), 400
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT partida_id 
                FROM partida 
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'message': 'Partida no encontrada'}), 404
            
            # Actualizar estado
            cursor.execute("""
                UPDATE partida 
                SET estado = 'finalizada' 
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            conexion.commit()
            
            return jsonify({
                'success': True,
                'partida_id': partida['partida_id'],
                'message': 'Partida finalizada'
            }), 200
            
    except Exception as e:
        print(f"[ERROR] api_finalizar_partida: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conexion.close()

