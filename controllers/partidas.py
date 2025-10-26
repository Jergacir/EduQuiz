from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, abort
import sys
import db as dbmod
from datetime import datetime
import random
import string
import json
from enum import Enum

# ========================================================
# API DE EXPORTACIÓN MEJORADA CON INTEGRACIÓN A DRIVE
# ========================================================
# pip install pandas
# pip install openpyxl
# pip install reportlab
from flask import send_file
from io import BytesIO
import pandas as pd #
import sys

# Para PDF
from reportlab.lib.pagesizes import letter #
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# Para integración con Google Drive y OneDrive
import requests


# ========================================================
# EXPORTACIÓN CON OAUTH 2.0 (Para cuentas @gmail.com gratuitas)
# ========================================================
import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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
            # Información de la partida
            cursor.execute("""
                SELECT p.partida_id, p.codigo_partida, p.estado, p.tipo_partida, p.fecha_creacion,
                       c.nombre_cuestionario, c.descripcion
                FROM partida p
                JOIN cuestionario c ON p.cuestionario_id = c.cuestionario_id
                WHERE p.partida_id = %s
            """, (partida_id,))
            partida_info = cursor.fetchone()
            
            if not partida_info:
                abort(404, "Partida no encontrada")

            # Estadísticas reales
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT pa.participante_id) as total_jugadores,
                    AVG(pa.puntuacion_total) as puntuacion_promedio,
                    AVG(pa.cant_preguntas_correctas) as correctas_promedio,
                    AVG(pa.cant_preguntas_incorrectas) as incorrectas_promedio
                FROM participante pa
                WHERE pa.partida_id = %s
            """, (partida_id,))
            stats = cursor.fetchone() or {}

            # Ranking completo
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
        
        # Agregar estadísticas al dict de partida_info
        partida_info_dict = dict(partida_info)
        partida_info_dict['jugadores_totales'] = stats.get('total_jugadores', 0)
        partida_info_dict['acierto_promedio'] = f"{int(stats.get('puntuacion_promedio', 0))} pts"
        partida_info_dict['fecha'] = partida_info['fecha_creacion'].strftime('%Y-%m-%d') if partida_info.get('fecha_creacion') else 'N/A'

        return render_template(
            'resultados_partida.html',
            partida_info=partida_info_dict,
            partida_id=partida_id,
            ranking=ranking,
            logged_in_user=logged
        )
    finally:
        conexion.close()


# En partidas.py
@partidas_bp.route('/podio/<string:codigo_partida>')
def frm_podio(codigo_partida): # Renombrado a frm_podio para seguir el estilo de las demás rutas
    """Muestra la vista del podio final de la partida."""
    logged = _get_logged_in_user()
    
    conexion = dbmod.obtenerConexion()
    if not conexion:
        abort(500, "Error de conexión")
    
    try:
        with conexion.cursor() as cursor:
            # 1. Obtener partida_id y marcar la partida como FINALIZADA
            cursor.execute("SELECT partida_id, estado FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                abort(404, "Partida no encontrada")
                
            # Marcar como FINALIZADA si no lo está
            if partida['estado'] != EstadoPartida.FINALIZADA.value:
                 cursor.execute(
                    "UPDATE partida SET estado = %s WHERE partida_id = %s",
                    (EstadoPartida.FINALIZADA.value, partida['partida_id'])
                )
                 conexion.commit()
                 actualizar_timestamp_partida(codigo_partida)

            # 2. Obtener el ranking COMPLETO en una sola consulta
            cursor.execute("""
                SELECT 
                    u.nombre, 
                    u.url_avatar, 
                    pa.puntuacion_total, 
                    pa.cant_preguntas_correctas
                FROM participante pa
                JOIN usuario u ON pa.usuario_id = u.usuario_id
                WHERE pa.partida_id = %s
                ORDER BY pa.puntuacion_total DESC, pa.cant_preguntas_correctas DESC
            """, (partida['partida_id'],))
            
            ranking_completo = cursor.fetchall() or []
        
        # 3. Usar Slicing de Python para dividir la lista
        top3 = ranking_completo[:3]  # Primeros 3 (índices 0, 1, 2)
        resto = ranking_completo[3:] # Del 4to en adelante (índice 3 en adelante)
        
        return render_template('podio.html', 
                               codigo_partida=codigo_partida, 
                               logged_in_user=logged,
                               top3=top3,
                               resto=resto)
    
    except Exception as e:
        print(f"[partidas] Error en frm_podio: {e}", file=sys.stderr)
        abort(500, "Error interno del servidor al cargar el podio.")
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
    """Devuelve el ranking REAL de la partida desde la BD."""
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT partida_id FROM partida WHERE codigo_partida = %s", (codigo_partida,))
            partida = cursor.fetchone()
            if not partida:
                return jsonify({'success': False, 'error': 'Partida no encontrada'}), 404

            partida_id = partida['partida_id']

            cursor.execute("""
                SELECT pa.participante_id, pa.usuario_id, u.nombre, COALESCE(u.url_avatar, '') as avatar,
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
    tiempo_respuesta = data.get('tiempo_respuesta', 0)  # Tiempo que tardó en responder

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
            tiempo_limite = pregunta["tiempo_limite"] or 30

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

            # 5️⃣ CALCULAR PUNTOS SEGÚN FÓRMULA
            puntos_ganados = 0
            if correcta == 1:
                # Fórmula: puntos = 1000 * (tiempo_restante / tiempo_limite)
                # Si responde en 15s de 30s → puntos = 1000 * (15/30) = 500
                # Si responde en 0s (instantáneo) → 1000 puntos
                tiempo_restante = max(0, tiempo_limite - tiempo_respuesta)
                puntos_ganados = int(1000 * (tiempo_restante / tiempo_limite))
                
                # Asegurar mínimo de 100 puntos si es correcta
                puntos_ganados = max(100, puntos_ganados)

            # 6️⃣ Insertar la respuesta del participante
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

            # 7️⃣ Actualizar estadísticas Y PUNTUACIÓN
            if correcta == 1:
                cursor.execute("""
                    UPDATE participante
                    SET cant_preguntas_correctas = cant_preguntas_correctas + 1,
                        puntuacion_total = puntuacion_total + %s
                    WHERE participante_id = %s
                """, (puntos_ganados, participante_id))
            else:
                cursor.execute("""
                    UPDATE participante
                    SET cant_preguntas_incorrectas = cant_preguntas_incorrectas + 1
                    WHERE participante_id = %s
                """, (participante_id,))

            # 8️⃣ Replicar si es líder
            if lider_id == participante_id_db:
                cursor.execute("""
                    SELECT participante_id
                    FROM participante
                    WHERE lider_id = %s
                      AND partida_id = %s
                      AND participante_id != %s
                """, (participante_id_db, partida_id, participante_id_db))
                miembros = [row["participante_id"] for row in cursor.fetchall()]

                if miembros:
                    # Insertar respuesta para cada miembro
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
                    
                    # Actualizar puntuación de miembros
                    if correcta == 1:
                        cursor.execute("""
                            UPDATE participante
                            SET cant_preguntas_correctas = cant_preguntas_correctas + 1,
                                puntuacion_total = puntuacion_total + %s
                            WHERE lider_id = %s
                              AND partida_id = %s
                              AND participante_id != %s
                        """, (puntos_ganados, participante_id_db, partida_id, participante_id_db))
                    else:
                        cursor.execute("""
                            UPDATE participante
                            SET cant_preguntas_incorrectas = cant_preguntas_incorrectas + 1
                            WHERE lider_id = %s
                              AND partida_id = %s
                              AND participante_id != %s
                        """, (participante_id_db, partida_id, participante_id_db))

            conexion.commit()
            return jsonify({
                'success': True, 
                'message': 'Respuesta registrada', 
                'correcta': bool(correcta),
                'puntos_ganados': puntos_ganados
            }), 200

    except Exception as e:
        import traceback
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



# ========================================================
# FUNCIÓN: Enviar email con Gmail API
# ========================================================
def enviar_email_oauth(destinatario_email, link_descarga, nombre_archivo, nombre_cuestionario):
    """
    Envía email usando OAuth (desde eduquiz.usat@gmail.com)
    
    Args:
        destinatario_email: Email del profesor
        link_descarga: URL de Google Drive
        nombre_archivo: Nombre del archivo
        nombre_cuestionario: Nombre del cuestionario
    """
    try:
        creds = get_oauth_credentials()
        if not creds:
            return {"success": False, "error": "No hay credenciales OAuth válidas"}
        
        gmail_service = build('gmail', 'v1', credentials=creds)
        
        # Crear mensaje HTML (mismo que antes)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 30px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #0a58ca, #3b82f6); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .btn {{ 
                    display: inline-block; 
                    padding: 14px 32px; 
                    background: #0a58ca; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .btn:hover {{ background: #084298; }}
                .footer {{ text-align: center; padding: 20px; background: #f8f9fa; color: #666; font-size: 13px; }}
                .info-box {{ background: #e7f3ff; border-left: 4px solid #0a58ca; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 24px;">📊 Resultados de EduQuiz</h1>
                    <p style="margin: 10px 0 0; opacity: 0.9;">Tu archivo está listo para descargar</p>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Los resultados de <strong>{nombre_cuestionario}</strong> ya están disponibles.</p>
                    
                    <div class="info-box">
                        <strong>📁 Archivo:</strong> {nombre_archivo}<br>
                        <strong>☁️ Ubicación:</strong> Google Drive (EduQuiz)
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{link_descarga}" class="btn">📥 Descargar Resultados</a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">
                        💡 <strong>Tip:</strong> El archivo estará disponible en tu Google Drive por tiempo indefinido. 
                        Puedes descargarlo desde cualquier dispositivo usando el enlace.
                    </p>
                </div>
                <div class="footer">
                    <p><strong>EduQuiz</strong> - Sistema de Evaluación Interactiva</p>
                    <p>eduquiz.usat@gmail.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear mensaje MIME
        message = MIMEMultipart('alternative')
        message['From'] = CORPORATE_EMAIL
        message['To'] = destinatario_email
        message['Subject'] = f"📊 Resultados: {nombre_cuestionario}"
        
        # Texto plano (fallback)
        text_part = MIMEText(f"""
        Resultados de EduQuiz
        
        Los resultados de "{nombre_cuestionario}" están listos.
        
        📥 Descargar: {link_descarga}
        
        Archivo: {nombre_archivo}
        
        ---
        EduQuiz - eduquiz.usat@gmail.com
        """, 'plain')
        
        html_part = MIMEText(html_body, 'html')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Codificar para Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Enviar
        resultado = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        message_id = resultado.get('id')
        print(f"✅ Email enviado a {destinatario_email} (ID: {message_id})")
        
        return {
            "success": True,
            "message_id": message_id,
            "destinatario": destinatario_email
        }
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send'
]

CORPORATE_EMAIL = 'eduquiz.usat@gmail.com'

# ========================================================
# FUNCIÓN: Obtener credenciales OAuth
# ========================================================
def get_oauth_credentials():
    """
    Obtiene credenciales desde token.pickle.
    Si no existe o está expirado, lo renueva automáticamente.
    """
    creds = None
    
    # Cargar token existente
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay credenciales válidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token OAuth...")
            creds.refresh(Request())
            
            # Guardar token renovado
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        else:
            print("❌ ERROR: token.pickle no existe o es inválido")
            print("   Ejecuta primero: python setup_oauth.py")
            return None
    
    return creds




# ========================================================
# FUNCIÓN: Subir archivo a Google Drive
# ========================================================
def subir_a_drive_oauth(buffer, filename, mimetype):
    """
    Sube archivo a Google Drive usando OAuth
    
    Returns:
        dict: {"success": bool, "url": str, "file_id": str}
    """
    try:
        creds = get_oauth_credentials()
        if not creds:
            return {"success": False, "error": "No hay credenciales OAuth válidas"}
        
        drive_service = build('drive', 'v3', credentials=creds)
        
        # 1. Buscar o crear carpeta "EduQuiz Resultados"
        folder_query = "name='EduQuiz Resultados' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = drive_service.files().list(
            q=folder_query,
            fields='files(id, name)'
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            folder_id = folders[0]['id']
            print(f"✅ Carpeta encontrada: {folder_id}")
        else:
            # Crear carpeta
            folder_metadata = {
                'name': 'EduQuiz Resultados',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            folder_id = folder['id']
            print(f"✅ Carpeta creada: {folder_id}")
        
        # 2. Subir archivo
        buffer.seek(0)
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(buffer, mimetype=mimetype, resumable=True)
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file['id']
        print(f"✅ Archivo subido: {file_id}")
        
        # 3. Hacer público (cualquiera con link puede ver)
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        drive_service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        # 4. Obtener link
        web_link = file.get('webViewLink')
        
        return {
            "success": True,
            "url": web_link,
            "file_id": file_id,
            "message": "Archivo subido correctamente"
        }
        
    except Exception as e:
        print(f"❌ Error subiendo a Drive: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

from datetime import timedelta
from collections import defaultdict

# Diccionario para rastrear envíos por IP
envios_recientes = defaultdict(list)

# ========================================================
# ENDPOINT DE EXPORTACIÓN (modificado)
# ========================================================
@partidas_bp.route('/api/exportar_partida/<int:partida_id>', methods=['POST'])
def api_exportar_partida(partida_id):
    """
    Exporta resultados con OAuth (sin Service Account)
    """
    data = request.get_json() or {}
    formato = data.get("formato", "csv").lower()
    campos = data.get("campos", [])
    enviar_por_email = data.get("enviar_por_email", False)
    email_destinatario = data.get("email_destinatario", "")
    
    # Validación básica
    if not campos:
        return jsonify({"status": "error", "error": "No se seleccionaron campos"}), 400
    
    if formato not in ["csv", "excel", "pdf"]:
        return jsonify({"status": "error", "error": "Formato no soportado"}), 400
    
    # Obtener datos de la BD
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"status": "error", "error": "Error de conexión a BD"}), 500
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.nombre,
                    pa.puntuacion_total AS puntaje_final,
                    pa.cant_preguntas_correctas AS respuestas_correctas,
                    pa.cant_preguntas_incorrectas AS respuestas_incorrectas,
                    p.codigo_partida,
                    c.nombre_cuestionario,
                    p.fecha_creacion
                FROM participante pa
                JOIN usuario u ON u.usuario_id = pa.usuario_id
                JOIN partida p ON p.partida_id = pa.partida_id
                JOIN cuestionario c ON c.cuestionario_id = p.cuestionario_id
                WHERE pa.partida_id = %s
                ORDER BY pa.puntuacion_total DESC
            """, (partida_id,))
            
            rows = cursor.fetchall()
        
        if not rows:
            return jsonify({"status": "error", "error": "No hay datos para exportar"}), 404
        
        # Convertir a DataFrame
        import pandas as pd
        df = pd.DataFrame(rows)
        
        # Filtrar columnas
        alias_map = {
            'puntuacion_total': 'puntaje_final',
            'puntaje_final': 'puntaje_final',
            'cant_preguntas_correctas': 'respuestas_correctas',
            'cant_preguntas_incorrectas': 'respuestas_incorrectas',
        }
        campos_normalizados = [alias_map.get(c, c) for c in campos]
        campos_validos = [c for c in campos_normalizados if c in df.columns]
        df = df[campos_validos]
        
        # Generar archivo
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        buffer = BytesIO()
        
        if formato == "csv":
            from io import TextIOWrapper
            text_wrapper = TextIOWrapper(buffer, encoding="utf-8-sig", newline="", write_through=True)
            df.to_csv(text_wrapper, index=False)
            text_wrapper.detach()
            buffer.seek(0)
            mimetype = "text/csv"
            extension = "csv"
        
        elif formato == "excel":
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Resultados")
            buffer.seek(0)
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        elif formato == "pdf":
            # Tu función existente de PDF
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(buffer, pagesize=letter)
            # ... tu código de PDF ...
            c.save()
            buffer.seek(0)
            mimetype = "application/pdf"
            extension = "pdf"
        
        filename = f"resultados_partida_{partida_id}_{timestamp}.{extension}"
        
        # Si se solicitó envío por email
        if enviar_por_email and email_destinatario:
            # 1. Subir a Drive
            resultado_drive = subir_a_drive_oauth(buffer, filename, mimetype)
            
            if not resultado_drive.get("success"):
                return jsonify({
                    "status": "error",
                    "error": f"Error subiendo a Drive: {resultado_drive.get('error')}"
                }), 500
            
            # 2. Enviar email
            nombre_cuestionario = rows[0].get('nombre_cuestionario', 'Cuestionario')
            resultado_email = enviar_email_oauth(
                email_destinatario,
                resultado_drive["url"],
                filename,
                nombre_cuestionario
            )
            
            if resultado_email.get("success"):
                return jsonify({
                    "status": "success",
                    "message": f"✅ Resultados enviados a {email_destinatario}",
                    "drive_url": resultado_drive["url"]
                }), 200
            else:
                return jsonify({
                    "status": "partial",
                    "message": "Archivo subido pero error al enviar email",
                    "drive_url": resultado_drive["url"],
                    "error_email": resultado_email.get("error")
                }), 200
        
        # Descarga directa
        from flask import send_file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        if conexion:
            conexion.close()


# ========================================================
# GENERADOR DE PDF MEJORADO
# ========================================================
def generar_pdf_mejorado(buffer, df, partida_id, info_partida):
    """Genera un PDF profesional con los resultados"""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(colors.HexColor('#2D3047'))
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, f"Resultados - Partida #{partida_id}")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Cuestionario: {info_partida.get('nombre_cuestionario', 'N/A')}")
    
    # Información general
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    y_pos = height - 110
    c.drawString(50, y_pos, f"Fecha: {info_partida.get('fecha_creacion', 'N/A')}")
    c.drawString(50, y_pos - 20, f"Total de participantes: {len(df)}")
    
    # Tabla de resultados
    y_pos -= 60
    
    # Preparar datos para la tabla
    table_data = [df.columns.tolist()]  # Headers
    for _, row in df.iterrows():
        table_data.append([str(val)[:30] for val in row.values])
    
    # Crear tabla
    # ColWidths: Usar el ancho de la página menos los márgenes, dividido por el número de columnas
    col_width = (width - 100) / len(df.columns) 
    col_widths = [col_width] * len(df.columns)
    table = Table(table_data, colWidths=col_widths)
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#419D78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Dibujar tabla
    table.wrapOn(c, width - 100, height) # El ancho de envoltura es el ancho de la página menos los márgenes
    table.drawOn(c, 50, y_pos - (len(table_data) * 20)) 
    
    c.save() 
    
    # Muy importante: Reportlab.c.save() cierra el buffer, así que lo re-abrimos y posicionamos al inicio
    buffer.seek(0)


# ========================================================
# INTEGRACIÓN CON ONEDRIVE Y GOOGLE DRIVE
# ========================================================

def subir_archivo_a_drive(buffer, filename, mimetype, drive_tipo, access_token):
    """
    Sube un archivo a OneDrive o Google Drive.
    
    Returns:
        dict: {"success": bool, "url": str, "file_id": str, "error": str}
    """
    try:
        if drive_tipo == "onedrive":
            return subir_a_onedrive(buffer, filename, access_token)
        elif drive_tipo == "google_drive":
            return subir_a_google_drive(buffer, filename, mimetype, access_token)
        else:
            return {"success": False, "error": "Tipo de Drive no válido"}
    except Exception as e:
        print(f"[ERROR] subir_archivo_a_drive: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


def subir_a_onedrive(buffer, filename, access_token):
    """Sube archivo a OneDrive usando Microsoft Graph API"""
    try:
        buffer.seek(0)
        file_content = buffer.read()
        
        # Endpoint de OneDrive
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/EduQuiz/{filename}:/content"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        response = requests.put(url, headers=headers, data=file_content)
        
        if response.status_code in [200, 201]:
            data = response.json()
            return {
                "success": True,
                "url": data.get("webUrl", ""),
                "file_id": data.get("id", ""),
                "drive_type": "onedrive"
            }
        else:
            return {
                "success": False,
                "error": f"Error {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def subir_a_google_drive(buffer, filename, mimetype, access_token):
    """Sube archivo a Google Drive dentro de la carpeta 'EduQuiz' usando la API v3"""
    try:
        buffer.seek(0)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        # 1️⃣ Buscar o crear carpeta "EduQuiz"
        folder_id = None
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false and name='EduQuiz'"
        search = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            headers=headers,
            params={"q": query, "fields": "files(id,name)"}
        )

        if search.status_code == 200 and search.json().get("files"):
            folder_id = search.json()["files"][0]["id"]
        else:
            # Crear carpeta si no existe
            metadata_folder = {
                "name": "EduQuiz",
                "mimeType": "application/vnd.google-apps.folder"
            }
            create_folder = requests.post(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                json=metadata_folder
            )
            if create_folder.status_code in [200, 201]:
                folder_id = create_folder.json()["id"]

        if not folder_id:
            return {"success": False, "error": "No se pudo crear o encontrar carpeta EduQuiz"}

        # 2️⃣ Subir el archivo dentro de la carpeta
        metadata = {
            "name": filename,
            "mimeType": mimetype,
            "parents": [folder_id]
        }

        files = {
            "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": (filename, buffer, mimetype)
        }

        upload = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files
        )

        if upload.status_code in [200, 201]:
            data = upload.json()
            file_id = data.get("id", "")
            return {
                "success": True,
                "url": f"https://drive.google.com/file/d/{file_id}/view",
                "file_id": file_id,
                "drive_type": "google_drive"
            }
        else:
            return {
                "success": False,
                "error": f"Error {upload.status_code}: {upload.text}"
            }

    except Exception as e:
        print(f"[ERROR] subir_a_google_drive: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


# ========================================================
# ENDPOINTS PARA AUTENTICACIÓN DE DRIVE (OAuth)
# ========================================================

@partidas_bp.route('/api/auth/onedrive/url', methods=['GET'])
def obtener_url_auth_onedrive():
    """Retorna la URL para autenticar con OneDrive"""
    # Configura tus credenciales en variables de entorno
    client_id = "TU_CLIENT_ID_ONEDRIVE"
    redirect_uri = "http://localhost:5000/api/auth/onedrive/callback"
    scope = "Files.ReadWrite offline_access"
    
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}"
    )
    
    return jsonify({"auth_url": auth_url})

import os

# Configuración de Google (en .env o aquí temporalmente)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '52705894161-h0iaill994m2somatd50kh4drlt3dsve.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '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')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/google_drive/callback')


# @partidas_bp.route('/api/auth/google_drive/url', methods=['POST'])
# def obtener_url_auth_google():
#     """
#     Retorna la URL para autenticar con Google Drive
#     Acepta un login_hint con el email del usuario
#     """
#     data = request.get_json() or {}
#     login_hint = data.get('login_hint', '')
    
#     scope = "https://www.googleapis.com/auth/drive.file"
    
#     params = {
#         'client_id': GOOGLE_CLIENT_ID,
#         'redirect_uri': GOOGLE_REDIRECT_URI,
#         'response_type': 'code',
#         'scope': scope,
#         'access_type': 'offline',
#         'prompt': 'consent'  # Forzar pantalla de consentimiento
#     }
    
#     if login_hint:
#         params['login_hint'] = login_hint
    
#     from urllib.parse import urlencode
#     auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
#     return jsonify({"auth_url": auth_url})

@partidas_bp.route('/api/auth/google_drive/url', methods=['GET', 'POST'])
def obtener_url_auth_google():
    """
    Retorna la URL para autenticar con Google Drive
    Acepta un login_hint con el email del usuario
    """
    # Soportar tanto GET como POST
    if request.method == 'POST':
        data = request.get_json() or {}
        login_hint = data.get('login_hint', '')
    else:
        login_hint = request.args.get('login_hint', '')
    
    scope = "https://www.googleapis.com/auth/drive.file"
    
    # Construir URL
    from urllib.parse import urlencode
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': scope,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    if login_hint:
        params['login_hint'] = login_hint
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return jsonify({"success": True, "auth_url": auth_url})


@partidas_bp.route('/api/auth/google_drive/callback')
def callback_google_drive():
    """
    Recibe el código de autorización de Google y lo intercambia por access_token
    """
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"""
        <html>
        <body>
            <h2>Error de autenticación</h2>
            <p>{error}</p>
            <script>
                window.opener.postMessage({{
                    type: 'google_auth_error',
                    error: '{error}'
                }}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
    
    if not code:
        return "Error: No se recibió el código de autorización", 400
    
    try:
        # Intercambiar código por token
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            return f"""
            <html>
            <head>
                <title>Autenticación exitosa</title>
                <style>
                    body {{
                        font-family: 'Roboto', Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #4285F4 0%, #34A853 100%);
                    }}
                    .success-box {{
                        background: white;
                        padding: 40px;
                        border-radius: 16px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                    }}
                    h2 {{ color: #333; margin: 20px 0 10px; }}
                    p {{ color: #666; margin: 0; }}
                </style>
            </head>
            <body>
                <div class="success-box">
                    <i class="fa-solid fa-check-circle" style="font-size: 4rem; color: #34A853;"></i>
                    <h2>✅ Conectado a Google Drive</h2>
                    <p>Esta ventana se cerrará automáticamente...</p>
                </div>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'google_auth_success',
                            access_token: '{access_token}'
                        }}, '*');
                    }}
                    
                    setTimeout(() => {{
                        window.close();
                    }}, 2000);
                </script>
            </body>
            </html>
            """
        else:
            return f"Error al obtener token: {response.text}", 500
            
    except Exception as e:
        print(f"[ERROR] callback_google_drive: {e}", file=sys.stderr)
        return f"Error: {str(e)}", 500




@partidas_bp.route("/api/subir_excel", methods=["POST"])
def subir_excel():
    """
    Recibe un Excel con preguntas y respuestas, y devuelve JSON listo para tu JS.
    La columna 'RespuestaCorrecta' se trata como cualquier otra respuesta,
    y su índice se coloca en 'correcta'.
    """
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]

    try:
        df = pd.read_excel(file)

        columnas_requeridas = ["Pregunta", "RespuestaCorrecta", "Respuesta1", "Respuesta2", "Respuesta3"]
        for col in columnas_requeridas:
            if col not in df.columns:
                return jsonify({"error": f"Falta columna obligatoria: {col}"}), 400

        preguntas = []

        for _, row in df.iterrows():
            # Limpiar NaN y convertir todo a string
            respuestas = [
                str(row["Respuesta1"]) if not pd.isna(row["Respuesta1"]) else "",
                str(row["Respuesta2"]) if not pd.isna(row["Respuesta2"]) else "",
                str(row["Respuesta3"]) if not pd.isna(row["Respuesta3"]) else "",
                str(row["RespuestaCorrecta"]) if not pd.isna(row["RespuestaCorrecta"]) else ""
            ]

            correcta_texto = str(row["RespuestaCorrecta"]) if not pd.isna(row["RespuestaCorrecta"]) else ""

            # Mezclar respuestas
            random.shuffle(respuestas)

            # Recalcular índice de la respuesta correcta
            correcta = respuestas.index(correcta_texto)

            preguntas.append({
                "texto": str(row["Pregunta"]) if not pd.isna(row["Pregunta"]) else "",
                "respuestas": respuestas,
                "correcta": correcta,
                "imagen": None
            })

        return jsonify({"preguntas": preguntas})

    except Exception as e:
        return jsonify({"error": str(e)}), 500