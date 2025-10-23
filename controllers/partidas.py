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
            # Obtener datos de la partida
            cursor.execute("""
                SELECT estado, cuestionario_id 
                FROM partida 
                WHERE codigo_partida = %s
            """, (codigo_partida,))
            
            partida_info = cursor.fetchone()
            if not partida_info:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404
            
            # Obtener participantes
            participantes = obtener_participantes(codigo_partida)
            
            # Timestamp
            timestamp = partidas_cache.get(codigo_partida, {}).get('last_update', datetime.now().timestamp())
            
            response_data = {
                'success': True,
                'participantes': participantes,
                'estado_partida': partida_info['estado'],
                'timestamp': timestamp,
                'total': len(participantes)
            }
            
            # Si está en curso, incluir pregunta actual
            if partida_info['estado'] == EstadoPartida.EN_CURSO.value:
                pregunta_actual = obtener_pregunta_actual(codigo_partida)
                if pregunta_actual:
                    response_data['pregunta_actual'] = pregunta_actual
            
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

            # 2. Actualizar el estado a 'en_juego'
            cursor.execute(
                "UPDATE partida SET estado = 'en_juego' WHERE codigo_partida = %s",
                (codigo_partida,)
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
    """Renderiza la vista principal de juego para el alumno/participante."""
    # Aquí puedes añadir lógica de carga de la primera pregunta
    return render_template(
        'preguntasalumno.html', 
        codigo_partida=codigo_partida,
        # ... datos adicionales ...
    )


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


