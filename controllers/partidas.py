from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash,abort
import sys
import db as dbmod
from flask_socketio import emit, join_room, leave_room
from flask import session
from main import socketio 

partidas = {}
# Evento cuando un usuario se une a la sala de espera
@socketio.on('unirse_sala')
def handle_unirse_sala(data):
    codigo_partida = data.get('codigo_partida')
    usuario = data.get('usuario')  # dict: usuario_id, nombre, avatar

    if not codigo_partida or not usuario:
        return

    # Unirse a la sala
    join_room(codigo_partida)

    # Obtener todos los participantes desde la BD
    participantes = obtener_participantes(codigo_partida)

    # Emitir la lista completa a todos en la sala
    emit('actualizar_participantes', {'participantes': participantes}, room=codigo_partida)

@socketio.on('salir_sala')
def handle_salir_sala(data):
    codigo_partida = data.get('codigo_partida')
    usuario_id = data.get('usuario_id')

    if not codigo_partida or not usuario_id:
        return

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return

    try:
        with conexion.cursor() as cursor:
            # Obtener ID de la partida y creador
            cursor.execute("SELECT partida_id, usuario_creador_id FROM partida WHERE codigo_partida=%s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida or int(usuario_id) == int(partida.get('usuario_creador_id')):
                return  # El creador no se elimina

            # Eliminar participante
            cursor.execute(
                "DELETE FROM participante WHERE partida_id=%s AND usuario_id=%s",
                (partida['partida_id'], usuario_id)
            )
            conexion.commit()

            # Emitir actualización a todos los que quedan en la sala
            participantes = obtener_participantes(codigo_partida)

            socketio.emit('actualizar_participantes', {'participantes': participantes}, room=codigo_partida)

            # Salir de la sala
            leave_room(codigo_partida)

    finally:
        conexion.close()

@socketio.on('unirse_grupo')
def handle_unirse_grupo(data):
    """
    Evento emitido desde salaespera.js cuando un alumno se cambia de grupo.
    data = {codigo_partida, usuario_id, grupo_id}
    """
    codigo_partida = data.get('codigo_partida')
    usuario_id = data.get('usuario_id')
    grupo_id = data.get('grupo_id')

    if not codigo_partida or not usuario_id or not grupo_id:
        print("[SocketIO] ⚠️ Datos incompletos en unirse_grupo:", data)
        return

    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("[SocketIO] ❌ No se pudo conectar a la base de datos.")
        return

    try:
        with conexion.cursor() as cursor:
            # 🔹 1️⃣ Obtener partida_id
            cursor.execute("SELECT partida_id FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                print(f"[SocketIO] ❌ No existe partida con código {codigo_partida}")
                return

            partida_id = partida["partida_id"]

            # 🔹 2️⃣ Eliminar el lider_id del participante (sale del grupo anterior)
            cursor.execute("""
                UPDATE participante
                SET grupo_id = %s, lider_id = NULL
                WHERE partida_id = %s AND usuario_id = %s
            """, (grupo_id, partida_id, usuario_id))
            conexion.commit()

            # 🔹 3️⃣ Verificar si el nuevo grupo ya tiene un líder
            cursor.execute("""
                SELECT DISTINCT lider_id 
                FROM participante 
                WHERE partida_id = %s AND grupo_id = %s AND lider_id IS NOT NULL
                LIMIT 1
            """, (partida_id, grupo_id))
            lider_existente = cursor.fetchone()

            if lider_existente and lider_existente["lider_id"]:
                nuevo_lider_id = lider_existente["lider_id"]

                # 🔹 4️⃣ Asignar ese lider_id al participante recién llegado
                cursor.execute("""
                    UPDATE participante
                    SET lider_id = %s
                    WHERE partida_id = %s AND usuario_id = %s
                """, (nuevo_lider_id, partida_id, usuario_id))
                conexion.commit()

                print(f"[SocketIO] ✅ Participante {usuario_id} se unió al grupo {grupo_id} con líder {nuevo_lider_id}")
            else:
                print(f"[SocketIO] ℹ️ Grupo {grupo_id} no tiene líder, participante {usuario_id} se une sin líder.")

            # 🔹 5️⃣ Obtener lista actualizada de participantes (con grupos y líderes)
            participantes = obtener_participantes(codigo_partida)

            # 🔹 6️⃣ Emitir actualización a todos los clientes en la sala
            socketio.emit('actualizar_participantes', {'participantes': participantes}, room=codigo_partida)

    except Exception as e:
        print(f"[SocketIO] 💥 Error en unirse_grupo: {e}", file=sys.stderr)
    finally:
        conexion.close()

@socketio.on('designar_lider')
def handle_designar_lider(data):
    """
    Evento emitido cuando el profesor designa a un líder.
    data = {
        "codigo_partida": "ABC123",
        "grupo_id": 1,
        "lider_participante_id": 42
    }
    """
    codigo_partida = data.get("codigo_partida")
    grupo_id = data.get("grupo_id")
    lider_participante_id = data.get("lider_participante_id")

    if not codigo_partida or not grupo_id or not lider_participante_id:
        print("[SocketIO] ⚠️ Datos incompletos para designar líder:", data)
        return

    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("[SocketIO] ❌ No se pudo conectar a la base de datos.")
        return

    try:
        with conexion.cursor() as cursor:
            # 1️⃣ Obtener el ID interno de la partida
            cursor.execute(
                "SELECT partida_id FROM partida WHERE codigo_partida = %s",
                (codigo_partida,)
            )
            partida = cursor.fetchone()
            if not partida:
                print(f"[SocketIO] ❌ No existe partida con código {codigo_partida}")
                return

            partida_id = partida["partida_id"]

            # 2️⃣ Actualizar el campo lider_id en los participantes del grupo
            cursor.execute("""
                UPDATE participante
                SET lider_id = %s
                WHERE partida_id = %s AND grupo_id = %s
            """, (lider_participante_id, partida_id, grupo_id))
            conexion.commit()

            print(f"[SocketIO] ✅ Líder asignado correctamente → participante_id={lider_participante_id}, grupo={grupo_id}")

            # 3️⃣ Obtener lista actualizada de participantes
            cursor.execute("""
                SELECT 
                    p.participante_id,
                    p.usuario_id,
                    u.nombre,
                    p.grupo_id,
                    p.lider_id
                FROM participante p
                JOIN usuario u ON p.usuario_id = u.usuario_id
                WHERE p.partida_id = %s
                ORDER BY p.grupo_id, u.nombre
            """, (partida_id,))
            participantes = cursor.fetchall() or []

            # 4️⃣ Emitir actualización a todos los clientes conectados en la sala
            socketio.emit(
                "actualizar_participantes",
                {"participantes": participantes},
                room=codigo_partida
            )

    except Exception as e:
        print(f"[SocketIO] 💥 Error al designar líder: {e}", file=sys.stderr)

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

@partidas_bp.route('/api/partida/<codigo_partida>/participantes')
def api_participantes(codigo_partida):
    participantes = obtener_participantes(codigo_partida)
    return jsonify({'participantes': participantes})

def validar_y_unir(codigo_partida, usuario_id):
    """
    Valida si el usuario puede unirse a la partida y lo inserta únicamente en
    la tabla participante (estadísticas). Retorna True si se unió o ya estaba.
    """
    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("Error: No se pudo conectar a la base de datos (validar_y_unir)", file=sys.stderr)
        return False

    try:
        with conexion.cursor() as cursor:
            # --- Buscar partida ---
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

            # --- Verificar si el usuario ya está en participante ---
            cursor.execute(
                "SELECT 1 FROM participante WHERE partida_id = %s AND usuario_id = %s",
                (partida_id, usuario_id)
            )
            if cursor.fetchone():
                return True  # Ya estaba

            # --- Insertar usuario en participante ---
            cursor.execute(
                "INSERT INTO participante (usuario_id, partida_id) VALUES (%s, %s)",
                (usuario_id, partida_id)
            )

            conexion.commit()
            return True

    except Exception as e:
        print(f"Error validar_y_unir: {e}", file=sys.stderr)
        conexion.rollback()
        return False
    finally:
        conexion.close()

@partidas_bp.route('/api/partida/unirse', methods=['POST'])
def api_unirse_partida():
    data = request.get_json() or {}
    usuario_id = session.get('user_id')
    codigo_partida = data.get('codigo')

    if not codigo_partida or not usuario_id:
        return jsonify({"success": False, "message": "Faltan el código de partida o el ID de usuario."}), 400

    if validar_y_unir(codigo_partida, usuario_id):
        # 🔹 Obtener lista de participantes actualizada
        participantes = obtener_participantes(codigo_partida)

        # 🔹 Filtrar al creador si no quieres que aparezca
        conexion = dbmod.obtenerConexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT usuario_creador_id FROM partida WHERE codigo_partida=%s", (codigo_partida,))
                row = cursor.fetchone()
                creador_id = row.get('usuario_creador_id') if row else None
        finally:
            conexion.close()

        participantes_para_emitir = [
            p for p in participantes if p['usuario_id'] != creador_id
        ]

        # 🔹 Emitir a todos los que están en la sala (si hay socketio)
        try:
            socketio.emit(
                'actualizar_participantes',
                {'participantes': participantes_para_emitir},
                room=codigo_partida
            )
        except Exception as e:
            print(f"[SocketIO] Error al emitir participantes: {e}", file=sys.stderr)

        return jsonify({
            "success": True,
            "message": "¡Te has unido a la partida!",
            "redirect_url": url_for('partidas.frm_sala_espera', codigo_partida=codigo_partida)
        }), 200

    return jsonify({"success": False, "message": "Código de partida inválido o partida llena."}), 400

@partidas_bp.route('/partidas_profesor')
def frm_partidas_profesor():
    logged = _get_logged_in_user()
    return render_template('partidas_profesor.html', logged_in_user=logged)


@partidas_bp.route('/api/partidas/crear', methods=['POST'])
def crear_partida():
    data = request.get_json()
    usuario = _get_logged_in_user()
    if not usuario:
        return jsonify({'status': 'error', 'mensaje': 'Usuario no autenticado'}), 401

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'status': 'error', 'mensaje': 'No se pudo conectar a la base de datos'}), 500

    try:
        with conexion.cursor() as cursor:
            # --- Validar código único ---
            codigo_partida = data.get('pin')
            if not codigo_partida:
                # Si el usuario no lo especificó o era automático, generar uno
                codigo_partida = generar_codigo_unico(cursor)

            # Verificar si ya existe ese código
            cursor.execute("SELECT 1 FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'mensaje': 'El código ya existe, intenta nuevamente'}), 400

            # --- Determinar tipo de partida ---
            modalidad = data.get('modalidad', 'I').upper()
            tipo_partida = 'G' if modalidad == 'G' else 'I'

            num_grupos = int(data.get('num_grupos', 0))  # 0 si es individual

            sql_insert = """
                INSERT INTO partida (codigo_partida, cuestionario_id, usuario_creador_id, estado, tipo_partida, fecha_creacion, num_grupos)
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

            # Obtener el ID de la partida creada
            partida_id = cursor.lastrowid

        return jsonify({
            'status': 'ok',
            'mensaje': 'Partida creada exitosamente',
            'codigo_partida': codigo_partida,
            'partida_id': partida_id
        })
    except Exception as e:
        print(f"Error al crear partida: {e}", file=sys.stderr)
        conexion.rollback()
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500
    finally:
        conexion.close()


def generar_codigo_unico(cursor, longitud=6):
    """Genera un código aleatorio de 6 dígitos y verifica que no exista en la BD."""
    import random, string
    while True:
        codigo = ''.join(random.choices(string.digits, k=longitud))
        cursor.execute("SELECT 1 FROM partida WHERE codigo_partida = %s", (codigo,))
        if not cursor.fetchone():
            return codigo


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
        return render_template('previapartida.html', partida=partida, logged_in_user=logged,codigo_partida=partida['codigo_partida'], tipo_partida=partida['tipo_partida'], num_grupos=partida['num_grupos'])
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
            tipo_partida=partida.get('tipo_partida', 'I'),  # Por defecto individual
            num_grupos=partida.get('num_grupos', 0)  
        )
    finally:
        conexion.close()





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



@partidas_bp.route('/api/partida/salir', methods=['POST'])
def api_salir_partida():
    data = request.get_data() or b'{}'
    import json
    try:
        data = json.loads(data)
    except:
        return '', 400

    codigo_partida = data.get('codigo_partida')
    usuario_id = data.get('usuario_id')

    if not codigo_partida or not usuario_id:
        return '', 400

    # Lógica para eliminar al participante (igual que salir_sala)
    conexion = dbmod.obtenerConexion()
    if conexion:
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT partida_id, usuario_creador_id FROM partida WHERE codigo_partida=%s", (codigo_partida,))
                partida = cursor.fetchone()
                if partida and int(usuario_id) != int(partida.get('usuario_creador_id')):
                    cursor.execute(
                        "DELETE FROM participante WHERE partida_id=%s AND usuario_id=%s",
                        (partida['partida_id'], usuario_id)
                    )
                    conexion.commit()

                # Emitir actualización vía SocketIO
                cursor.execute("""
                    SELECT p.participante_id, u.usuario_id, u.nombre
                    FROM participante p
                    JOIN usuario u ON u.usuario_id = p.usuario_id
                    WHERE p.partida_id = %s
                """, (partida['partida_id'],))
                participantes = cursor.fetchall() or []
                socketio.emit('actualizar_participantes', {'participantes': participantes}, room=codigo_partida)

        finally:
            conexion.close()

    return '', 204