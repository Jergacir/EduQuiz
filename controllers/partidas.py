from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, abort
import sys
import db as dbmod
from datetime import datetime
import random
import string
import json

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


# ====================================================================
# API ENDPOINTS PARA AJAX POLLING
# ====================================================================

@partidas_bp.route('/api/partida/<codigo_partida>/poll', methods=['GET'])
def api_poll_participantes(codigo_partida):
    """
    Endpoint principal para AJAX Polling.
    Retorna participantes y timestamp de última actualización.
    El cliente puede usar el timestamp para detectar cambios.
    """
    try:
        participantes = obtener_participantes(codigo_partida)
        
        # Obtener timestamp de cache
        timestamp = partidas_cache.get(codigo_partida, {}).get('last_update', datetime.now().timestamp())
        timestamp_str = partidas_cache.get(codigo_partida, {}).get('last_update_str', datetime.now().isoformat())
        
        return jsonify({
            'success': True,
            'participantes': participantes,
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'total': len(participantes)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] api_poll_participantes: {e}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'participantes': []
        }), 500


@partidas_bp.route('/api/partida/<codigo_partida>/participantes')
def api_participantes(codigo_partida):
    """Endpoint legacy - redirige al endpoint de polling"""
    return api_poll_participantes(codigo_partida)


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


@partidas_bp.route('/api/exportar_partida/<int:partida_id>', methods=['POST'])
def api_exportar_partida(partida_id):
    data = request.get_json() or {}
    formato = data.get('formato', 'csv')
    campos = data.get('campos', [])
    print(f"Exportando partida #{partida_id} a {formato} con campos: {campos}")
    return jsonify({'success': True, 'message': f'Partida {partida_id} exportada como {formato}.'})