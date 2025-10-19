from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import sys
import db as dbmod

tienda_bp = Blueprint('tienda', __name__, template_folder='../../templates')


def _is_logged_in():
    return 'user_id' in session


def _is_gestor(user_id):
    # Revisar rol en la BD
    conexion = dbmod.obtenerConexion()
    if not conexion:
        return False
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return bool(row and row.get('tipo_usuario') == 'G')
    except Exception as e:
        print(f"[tienda] Error comprobando rol gestor: {e}", file=sys.stderr)
        return False


@tienda_bp.route('/tienda')
def tienda_index():
    if not _is_logged_in():
        return redirect(url_for('auth.frm_login'))

    lista_skins = []
    lista_accesorios = []

    conexion = dbmod.obtenerConexion()
    if conexion:
        try:
            with conexion.cursor() as cursor:
                sql_skins = "SELECT skin_id, nombre, url_imagen, precio FROM skins WHERE vigencia = 1  ORDER BY precio ASC"
                cursor.execute(sql_skins)
                lista_skins = cursor.fetchall()

                sql_accesorios = "SELECT accesorio_id, nombre, url_imagen, precio FROM accesorios WHERE vigencia = 1 ORDER BY precio ASC"
                cursor.execute(sql_accesorios)
                lista_accesorios = cursor.fetchall()
        except Exception as e:
            print(f"Error al consultar la tienda: {e}")

    return render_template('tienda.html', skins=lista_skins, accesorios=lista_accesorios)


@tienda_bp.route('/api/tienda/accesorios', methods=['GET'])
def listar_accesorios_api():
    # API protegida: requiere login + gestor
    if not _is_logged_in():
        return jsonify({'error': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'error': 'Acceso prohibido.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify([])
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT accesorio_id AS id, nombre, precio FROM accesorios WHERE vigencia = 1 ORDER BY accesorio_id ASC"
            cursor.execute(sql)
            items = cursor.fetchall()
            return jsonify(items)
    except Exception as e:
        print(f"Error listar accesorios (tienda): {e}", file=sys.stderr)
        return jsonify([])


@tienda_bp.route('/api/tienda/skins', methods=['GET'])
def listar_skins_api():
    if not _is_logged_in():
        return jsonify({'error': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'error': 'Acceso prohibido.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify([])
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT skin_id AS id, nombre, precio FROM skins WHERE vigencia = 1 ORDER BY skin_id ASC"
            cursor.execute(sql)
            items = cursor.fetchall()
            return jsonify(items)
    except Exception as e:
        print(f"Error listar skins (tienda): {e}", file=sys.stderr)
        return jsonify([])


@tienda_bp.route('/api/tienda/accesorios/crear', methods=['POST'])
def crear_accesorio_api():
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
            return jsonify({'success': False, 'message': 'El precio debe ser positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Precio inválido.'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO accesorios (nombre, url_imagen, precio) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, url_imagen, precio))
            conexion.commit()
            nuevo_id = cursor.lastrowid
            return jsonify({'success': True, 'message': 'Accesorio creado exitosamente.', 'accesorio_id': nuevo_id}), 201
    except Exception as e:
        print(f"Error crear accesorio: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/accesorios/editar/<int:accesorio_id>', methods=['POST'])
def editar_accesorio_api(accesorio_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
            return jsonify({'success': False, 'message': 'El precio debe ser positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Precio inválido.'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE accesorios SET nombre=%s, url_imagen=%s, precio=%s WHERE accesorio_id=%s"
            cursor.execute(sql, (nombre, url_imagen, precio, accesorio_id))
            conexion.commit()
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'No se encontró el accesorio.'}), 404
            return jsonify({'success': True, 'message': 'Ítem actualizado exitosamente.'}), 200
    except Exception as e:
        print(f"Error editar accesorio: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/accesorios/eliminar/<int:accesorio_id>', methods=['POST'])
def eliminar_accesorio_api(accesorio_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE accesorios SET vigencia = %s WHERE accesorio_id = %s"
            cursor.execute(sql, (0, accesorio_id))
            conexion.commit()
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'No se encontró el ítem para eliminar.'}), 404
            return jsonify({'success': True, 'message': 'Ítem dado de baja exitosamente.'}), 200
    except Exception as e:
        print(f"Error eliminar accesorio: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/accesorios/<int:accesorio_id>', methods=['GET'])
def obtener_accesorio_api(accesorio_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT accesorio_id AS id, nombre, url_imagen, precio FROM accesorios WHERE accesorio_id = %s"
            cursor.execute(sql, (accesorio_id,))
            item = cursor.fetchone()
            if item:
                return jsonify(item), 200
            else:
                return jsonify({'success': False, 'message': 'Accesorio no encontrado.'}), 404
    except Exception as e:
        print(f"Error obtener accesorio: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/skin/crear', methods=['POST'])
def crear_skin_api():
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
            return jsonify({'success': False, 'message': 'El precio debe ser positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Precio inválido.'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO skins (nombre, url_imagen, precio) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, url_imagen, precio))
            conexion.commit()
            nuevo_id = cursor.lastrowid
            return jsonify({'success': True, 'message': 'Skin creado exitosamente.', 'skin_id': nuevo_id}), 201
    except Exception as e:
        print(f"Error crear skin: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/skin/editar/<int:skin_id>', methods=['POST'])
def editar_skin_api(skin_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    nombre = request.form.get('nombre')
    url_imagen = request.form.get('url_imagen')
    precio_str = request.form.get('precio')

    if not nombre or not url_imagen or not precio_str:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    try:
        precio = int(precio_str)
        if precio < 0:
            return jsonify({'success': False, 'message': 'El precio debe ser positivo.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Precio inválido.'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE skins SET nombre=%s, url_imagen=%s, precio=%s WHERE skin_id=%s"
            cursor.execute(sql, (nombre, url_imagen, precio, skin_id))
            conexion.commit()
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'No se encontró el skin.'}), 404
            return jsonify({'success': True, 'message': 'Ítem actualizado exitosamente.'}), 200
    except Exception as e:
        print(f"Error editar skin: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/skin/eliminar/<int:skin_id>', methods=['POST'])
def eliminar_skin_api(skin_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE skins SET vigencia = %s WHERE skin_id = %s"
            cursor.execute(sql, (0, skin_id))
            conexion.commit()
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'No se encontró el ítem para eliminar.'}), 404
            return jsonify({'success': True, 'message': 'Ítem dado de baja exitosamente.'}), 200
    except Exception as e:
        print(f"Error eliminar skin: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/api/tienda/skin/<int:skin_id>', methods=['GET'])
def obtener_skin_api(skin_id):
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'No tienes permiso.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT skin_id AS id, nombre, url_imagen, precio FROM skins WHERE skin_id = %s"
            cursor.execute(sql, (skin_id,))
            item = cursor.fetchone()
            if item:
                return jsonify(item), 200
            else:
                return jsonify({'success': False, 'message': 'Accesorio no encontrado.'}), 404
    except Exception as e:
        print(f"Error obtener skin: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500
