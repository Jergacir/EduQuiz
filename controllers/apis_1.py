from flask import Blueprint, request, jsonify
from datetime import datetime
from auth_utils import jwt_required_api_enhanced, get_user_from_jwt_or_session
import random
import string

import db as dbmod
def obtenerConexion():
	try:
		import main as mainmod
		if hasattr(mainmod, 'obtenerConexion'):
			return mainmod.obtenerConexion()
	except Exception:
		pass
	return dbmod.obtenerConexion()
try:
	from extensions import bcrypt
except Exception:
	bcrypt = None

apis_1_bp = Blueprint('apis_1', __name__, url_prefix='/api')


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


# =============== USUARIO (5 APIs) ===============

@apis_1_bp.get('/api_obtenerusuarios')
@jwt_required_api_enhanced
def api_obtenerusuarios():
    # Nivel 1
    user_data = get_user_from_jwt_or_session()

    if not user_data:
        return jsonify({'error': 'No autenticado.'}), 401

    # Nivel 1 (Corregido: alineado con user_data)
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

@apis_1_bp.get('/api_obtenerusuarioporid')
def api_obtenerusuarioporid():
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


@apis_1_bp.post('/api_registrarusuario')
def api_registrarusuario():
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
				# Verificar unicidad
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


@apis_1_bp.post('/api_actualizarusuario')
def api_actualizarusuario():
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


@apis_1_bp.post('/api_eliminarusuario')
def api_eliminarusuario():
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


# =============== SKIN (5 APIs) ==
@apis_1_bp.get('/api_obtenerskins')
def api_obtenerskins():
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


@apis_1_bp.get('/api_obtenerskinporid')
def api_obtenerskinporid():
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


@apis_1_bp.post('/api_registrarskin')
def api_registrarskin():
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


@apis_1_bp.post('/api_actualizarskin')
def api_actualizarskin():
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


@apis_1_bp.post('/api_eliminarskin')
def api_eliminarskin():
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


# =============== INVENTARIO (5 APIs) ===============

@apis_1_bp.get('/api_obtenerinventarios')
def api_obtenerinventarios():
	usuario_id = request.args.get('usuario_id', type=int)
	tipo_item = request.args.get('tipo_item')  # 'SKIN' o 'ACCESORIO'
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


@apis_1_bp.get('/api_obtenerinventarioporid')
def api_obtenerinventarioporid():
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


@apis_1_bp.post('/api_registrarinventario')
def api_registrarinventario():
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


@apis_1_bp.post('/api_actualizarinventario')
def api_actualizarinventario():
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


@apis_1_bp.post('/api_eliminarinventario')
def api_eliminarinventario():
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


# =============== PARTIDA (5+ APIs) ===============

def _codigo_random(n=6):
	return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


@apis_1_bp.get('/api_obtenerpartidas')
def api_obtenerpartidas():
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


@apis_1_bp.get('/api_obtenerpartidaporid')
def api_obtenerpartidaporid():
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


@apis_1_bp.get('/api_obtenerpartidaporcodigo')
def api_obtenerpartidaporcodigo():
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


@apis_1_bp.post('/api_registrarpartida')
def api_registrarpartida():
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
					# regenerar simple
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


@apis_1_bp.post('/api_actualizarpartida')
def api_actualizarpartida():
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


@apis_1_bp.post('/api_eliminarpartida')
def api_eliminarpartida():
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
				# Eliminar primero datos dependientes para evitar errores de FK
				# 1) pregunta_participante -> participante -> partida
				c.execute("SELECT participante_id FROM participante WHERE partida_id=%s", (partida_id,))
				participantes = [row['participante_id'] for row in c.fetchall() or []]
				if participantes:
					format_ids = ','.join(['%s'] * len(participantes))
					c.execute(f"DELETE FROM pregunta_participante WHERE participante_id IN ({format_ids})", participantes)
					c.execute(f"DELETE FROM participante WHERE participante_id IN ({format_ids})", participantes)
				# Intentar borrado directo de la partida
				c.execute("DELETE FROM partida WHERE partida_id=%s", (partida_id,))
				if c.rowcount == 0:
					return _json_error('Partida no encontrada', 404)
				conexion.commit()
		return _json_ok({"partida_id": partida_id, "eliminado": True})
	except Exception as e:
		# Fallback: marcar estado eliminado si no se puede borrar por alguna dependencia futura
		try:
			with conexion:
				with conexion.cursor() as c:
					c.execute("UPDATE partida SET estado='eliminada' WHERE partida_id=%s", (partida_id,))
					conexion.commit()
			return _json_ok({"partida_id": partida_id, "eliminado": False, "estado": "eliminada", "detalle_error": str(e)})
		except Exception:
			return _json_error(str(e), 500)


@apis_1_bp.post('/api_avanzarpregunta')
def api_avanzarpregunta():
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
				# Llamar al procedimiento almacenado definido en la BD (ver eduquiz_bd.sql)
				c.execute("CALL avanzar_pregunta(%s)", (codigo,))
				conexion.commit()
		return _json_ok({"codigo_partida": codigo, "avanzado": True})
	except Exception as e:
		return _json_error(str(e), 500)

# =============== PREGUNTA_PARTICIPANTE (5 APIs) ===============

@apis_1_bp.get('/api_obtenerpreguntaparticipantes')
def api_obtenerpreguntaparticipantes():
    participante_id = request.args.get('participante_id', type=int)
    pregunta_id = request.args.get('pregunta_id', type=int)

    conexion = obtenerConexion()
    if not conexion:
        return _json_error('No hay conexión a BD', 500)

    try:
        with conexion:
            with conexion.cursor() as c:
                # Corregido: Eliminados caracteres extraños en la unión de líneas
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


@apis_1_bp.get('/api_obtenerpreguntaparticipanteporid')
def api_obtenerpreguntaparticipanteporid():
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


@apis_1_bp.post('/api_registrarpreguntaparticipante')
def api_registrarpreguntaparticipante():
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
                # Corregido: Eliminados caracteres extraños en la unión de líneas
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


@apis_1_bp.post('/api_actualizarpreguntaparticipante')
def api_actualizarpreguntaparticipante():
    body = request.get_json(silent=True) or {}
    id_reg = body.get('pregunta_participante_id')
    if not id_reg:
        return _json_error('pregunta_participante_id requerido')

    campos = ['respuesta_seleccionada_id', 'correcta', 'tiempo_pregunta', 'tiempo_maximo_pregunta', 'texto_pregunta']
    sets, params = [], []
    for k in campos:
        if k in body:
            sets.append(f"{k}=%s")
            params.append(body[k])

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


@apis_1_bp.post('/api_eliminarpreguntaparticipante')
def api_eliminarpreguntaparticipante():
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
