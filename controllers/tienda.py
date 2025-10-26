from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import sys
import db as dbmod
tienda_bp = Blueprint('tienda', __name__, template_folder='../../templates')

# Ruta para inventario
@tienda_bp.route('/inventario')
def inventario_index():
    if not _is_logged_in():
        return redirect(url_for('auth.frm_login'))

    lista_skins = []
    lista_accesorios = []
    # leer filtros desde query string
    selected_categoria = (request.args.get('categoria') or '').upper()

    conexion = dbmod.obtenerConexion()
    if conexion:
        try:
            with conexion.cursor() as cursor:
                user_id = session.get('user_id')
                # Detectar tablas (comodín para mayúsculas/minúsculas)
                inventario_table = 'inventario'
                try:
                    cursor.execute("SELECT 1 FROM inventario LIMIT 1")
                except Exception:
                    inventario_table = 'Inventario'

                # Usar joins para traer sólo lo que el usuario posee
                try:
                    # Construir consulta con posible filtro por categoria
                    sql_skins = (
                        f"SELECT i.id_inventario AS inventory_id, s.skin_id AS skin_id, s.nombre AS nombre, s.url_imagen AS skin_url, s.precio AS precio, i.equipada "
                        f"FROM {inventario_table} i JOIN skin s ON i.id_item = s.skin_id "
                        f"WHERE i.usuario_id = %s AND i.tipo_item = 'SKIN' "
                    )
                    params = [user_id]
                    if selected_categoria in ('N', 'E', 'L'):
                        sql_skins += " AND s.categoria = %s"
                        params.append(selected_categoria)
                    sql_skins += " ORDER BY i.fecha_adquisicion DESC"
                    cursor.execute(sql_skins, tuple(params))
                    lista_skins = cursor.fetchall()
                except Exception:
                    lista_skins = []

                try:
                    sql_accesorios = (
                        f"SELECT i.id_inventario AS inventory_id, a.accesorio_id AS accesorio_id, a.nombre AS nombre, a.url_imagen AS url_imagen, a.precio AS precio, i.equipada "
                        f"FROM {inventario_table} i JOIN accesorio a ON i.id_item = a.accesorio_id "
                        f"WHERE i.usuario_id = %s AND i.tipo_item = 'ACCESORIO' ORDER BY i.fecha_adquisicion DESC"
                    )
                    cursor.execute(sql_accesorios, (user_id,))
                    lista_accesorios = cursor.fetchall()
                except Exception:
                    lista_accesorios = []
        except Exception as e:
            print(f"Error al consultar el inventario: {e}")

    return render_template('inventario.html', skins=lista_skins, accesorios=lista_accesorios,
               selected_categoria=selected_categoria)




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
    # filtros desde querystring
    selected_categoria = (request.args.get('categoria') or '').upper()
    selected_price = (request.args.get('price') or 'all').lower()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    conexion = dbmod.obtenerConexion()
    if conexion:
        try:
            with conexion.cursor() as cursor:
                # Mostrar únicamente skins que no sean default (skinDefault = 0)
                # Construir consulta dinámica aplicada a filtros
                where_clauses = ["s.vigencia = 1", "COALESCE(s.skinDefault, 0) = 0"]
                params = []
                if selected_categoria in ('N', 'E', 'L'):
                    where_clauses.append("s.categoria = %s")
                    params.append(selected_categoria)

                # Precio: si se proveen min/max en querystring, se usan preferentemente
                try:
                    if min_price is not None or max_price is not None:
                        if min_price:
                            where_clauses.append("s.precio >= %s")
                            params.append(int(min_price))
                        if max_price:
                            where_clauses.append("s.precio <= %s")
                            params.append(int(max_price))
                    else:
                        # Mapeo estético de rangos
                        if selected_price == 'low':
                            where_clauses.append("s.precio <= %s")
                            params.append(50)
                        elif selected_price == 'mid':
                            where_clauses.append("s.precio BETWEEN %s AND %s")
                            params.extend([51, 200])
                        elif selected_price == 'high':
                            where_clauses.append("s.precio > %s")
                            params.append(200)
                except Exception:
                    pass

                where_sql = " AND ".join(where_clauses)
                sql_skins = (
                    "SELECT s.skin_id, s.nombre, s.url_imagen AS skin_url, s.precio "
                    "FROM skin s "
                    f"WHERE {where_sql} "
                    "ORDER BY s.precio ASC"
                )
                cursor.execute(sql_skins, tuple(params))
                lista_skins = cursor.fetchall()

                # No manejamos accesorios: lista vacía
                lista_accesorios = []
                # Obtener IDs de items que ya posee el usuario (para marcar "Adquirido" en la tienda)
                owned_skins = []
                owned_accesorios = []
                try:
                    user_id = session.get('user_id')
                    # detectar nombre de la tabla inventario (mayúsc/minúsc)
                    inventario_table = 'inventario'
                    try:
                        cursor.execute("SELECT 1 FROM inventario LIMIT 1")
                    except Exception:
                        inventario_table = 'Inventario'

                    sql_owned_skins = f"SELECT id_item FROM {inventario_table} WHERE usuario_id = %s AND tipo_item = 'SKIN'"
                    cursor.execute(sql_owned_skins, (user_id,))
                    rows = cursor.fetchall()
                    owned_skins = [r.get('id_item') for r in rows if r.get('id_item') is not None]

                    sql_owned_acc = f"SELECT id_item FROM {inventario_table} WHERE usuario_id = %s AND tipo_item = 'ACCESORIO'"
                    cursor.execute(sql_owned_acc, (user_id,))
                    rows2 = cursor.fetchall()
                    owned_accesorios = [r.get('id_item') for r in rows2 if r.get('id_item') is not None]
                except Exception:
                    # si algo falla, dejamos las listas vacías (no crítico)
                    owned_skins = []
                    owned_accesorios = []
                # No usamos SkinAccesorio ni accesorios en la vista pública de tienda
                lista_skinacc_no_default = []
                # Merge: para cada skin de lista_skins, si existe una combinación no-default, añadir acc_url
                try:
                    if lista_skins and lista_skinacc_no_default:
                        # Crear mapa por skin_id para lookup rápido
                        mapa_sa = {}
                        for sa in lista_skinacc_no_default:
                            try:
                                key = int(sa.get('skin_id')) if sa.get('skin_id') is not None else None
                            except Exception:
                                key = sa.get('skin_id')
                            if key is None:
                                continue
                            # preferimos la primera combinación encontrada
                            if key not in mapa_sa:
                                mapa_sa[key] = sa

                        # Aplicar merge
                        for sk in lista_skins:
                            try:
                                sk_id = int(sk.get('skin_id') or sk.get('id'))
                            except Exception:
                                sk_id = sk.get('skin_id') or sk.get('id')
                            if sk_id in mapa_sa:
                                sa = mapa_sa[sk_id]
                                # sólo asignar si no existe ya acc_url (priorizar acc_url que venga con la skin)
                                if not sk.get('acc_url') and sa.get('acc_url'):
                                    sk['acc_url'] = sa.get('acc_url')
                                    # mantener id del accesorio si hace falta
                                    if sa.get('acc_id'):
                                        sk['acc_id'] = sa.get('acc_id')
                except Exception:
                    pass
        except Exception as e:
            print(f"Error al consultar la tienda: {e}")

    return render_template('tienda.html', skins=lista_skins, accesorios=lista_accesorios,
                           owned_skins=owned_skins, owned_accesorios=owned_accesorios,
                           skinacc_no_default=lista_skinacc_no_default,
                           selected_categoria=selected_categoria, selected_price=selected_price,
                           min_price=min_price, max_price=max_price)


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
            sql = "SELECT accesorio_id AS id, nombre, precio FROM accesorio WHERE vigencia = 1 ORDER BY accesorio_id ASC"
            try:
                cursor.execute(sql)
                items = cursor.fetchall()
                return jsonify(items)
            except Exception:
                # fallback sin vigencia
                try:
                    sql2 = "SELECT accesorio_id AS id, nombre, precio FROM accesorio ORDER BY accesorio_id ASC"
                    cursor.execute(sql2)
                    items = cursor.fetchall()
                    return jsonify(items)
                except Exception as e:
                    print(f"Error listar accesorios (tienda): {e}", file=sys.stderr)
                    return jsonify([])
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
            sql = "SELECT skin_id AS id, nombre, precio FROM skin WHERE vigencia = 1 ORDER BY skin_id ASC"
            try:
                cursor.execute(sql)
                items = cursor.fetchall()
                return jsonify(items)
            except Exception:
                try:
                    sql2 = "SELECT skin_id AS id, nombre, precio FROM skin ORDER BY skin_id ASC"
                    cursor.execute(sql2)
                    items = cursor.fetchall()
                    return jsonify(items)
                except Exception as e:
                    print(f"Error listar skins (tienda): {e}", file=sys.stderr)
                    return jsonify([])
    except Exception as e:
        print(f"Error listar skins (tienda): {e}", file=sys.stderr)
        return jsonify([])


@tienda_bp.route('/api/tienda/skinaccesorio/no_default', methods=['GET'])
def listar_skinaccesorio_no_default_api():
    # Eliminado: endpoint de SkinAccesorio no-default (ya no usamos accesorios)
    return jsonify({'error': 'Endpoint deshabilitado.'}), 404


@tienda_bp.route('/api/tienda/accesorios/crear', methods=['POST'])
def crear_accesorio_api():
    # Endpoint eliminado: ya no se gestionan accesorios
    return jsonify({'success': False, 'message': 'Funcionalidad de accesorios deshabilitada.'}), 410


@tienda_bp.route('/api/tienda/accesorios/editar/<int:accesorio_id>', methods=['POST'])
def editar_accesorio_api(accesorio_id):
    return jsonify({'success': False, 'message': 'Funcionalidad de accesorios deshabilitada.'}), 410


@tienda_bp.route('/api/tienda/accesorios/eliminar/<int:accesorio_id>', methods=['POST'])
def eliminar_accesorio_api(accesorio_id):
    return jsonify({'success': False, 'message': 'Funcionalidad de accesorios deshabilitada.'}), 410


@tienda_bp.route('/api/tienda/accesorios/<int:accesorio_id>', methods=['GET'])
def obtener_accesorio_api(accesorio_id):
    return jsonify({'success': False, 'message': 'Funcionalidad de accesorios deshabilitada.'}), 410


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
            sql = "INSERT INTO skin (nombre, url_imagen, precio) VALUES (%s, %s, %s)"
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
            sql = "UPDATE skin SET nombre=%s, url_imagen=%s, precio=%s WHERE skin_id=%s"
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
            sql = "UPDATE skin SET vigencia = %s WHERE skin_id = %s"
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
            sql = "SELECT skin_id AS id, nombre, url_imagen, precio FROM skin WHERE skin_id = %s"
            cursor.execute(sql, (skin_id,))
            item = cursor.fetchone()
            if item:
                return jsonify(item), 200
            else:
                return jsonify({'success': False, 'message': 'Accesorio no encontrado.'}), 404
    except Exception as e:
        print(f"Error obtener skin: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': str(e)}), 500


@tienda_bp.route('/admin/assign_default_skins', methods=['POST'])
def admin_assign_default_skins():
    """Endpoint administrado por un gestor para asignar retroactivamente las skins por defecto a todos los usuarios.
    Devuelve un resumen con la cantidad de inserciones realizadas.
    """
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401
    if not _is_gestor(session['user_id']):
        return jsonify({'success': False, 'message': 'Acceso prohibido.'}), 403

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                # Determinar nombre de la tabla inventario
                inventario_table = 'inventario'
                try:
                    cursor.execute("SELECT 1 FROM inventario LIMIT 1")
                except Exception:
                    inventario_table = 'Inventario'

                # Obtener skins por defecto
                try:
                    cursor.execute("SELECT skin_id FROM skin WHERE COALESCE(skinDefault,0) = 1")
                    default_skins = [r.get('skin_id') for r in (cursor.fetchall() or []) if r.get('skin_id') is not None]
                except Exception:
                    default_skins = []

                if not default_skins:
                    return jsonify({'success': True, 'message': 'No hay skins marcadas como default.', 'assigned': 0}), 200

                # Obtener todos los usuarios activos/verificados
                cursor.execute("SELECT usuario_id FROM usuario WHERE verificado=1")
                users = [r.get('usuario_id') for r in (cursor.fetchall() or []) if r.get('usuario_id') is not None]

                total_assigned = 0
                per_user = {}
                for u in users:
                    assigned_for_user = 0
                    for sk in default_skins:
                        try:
                            check_sql = f"SELECT 1 FROM {inventario_table} WHERE usuario_id=%s AND id_item=%s AND tipo_item='SKIN'"
                            cursor.execute(check_sql, (u, sk))
                            if not cursor.fetchone():
                                insert_sql = f"INSERT INTO {inventario_table} (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion) VALUES (%s, %s, %s, %s, NOW())"
                                cursor.execute(insert_sql, (u, sk, 'SKIN', 0))
                                total_assigned += 1
                                assigned_for_user += 1
                        except Exception as e:
                            # No interrumpir todo el proceso si hay un error con un usuario/skin
                            print(f"Warning assigning default skin {sk} to user {u}: {e}")
                    per_user[u] = assigned_for_user

                conexion.commit()
                return jsonify({'success': True, 'message': 'Asignación completada.', 'assigned': total_assigned, 'per_user': per_user}), 200
    except Exception as e:
        print(f"Error admin_assign_default_skins: {e}", file=sys.stderr)
        try:
            conexion.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'message': 'Error interno.'}), 500


@tienda_bp.route('/api/inventario/equipar', methods=['POST'])
def api_inventario_equipar():
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    user_id = session.get('user_id')
    inventory_id = request.form.get('inventory_id') or request.json.get('inventory_id') if request.is_json else request.form.get('inventory_id')
    if not inventory_id:
        return jsonify({'success': False, 'message': 'Falta inventory_id.'}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexion.'}), 500

    try:
        with conexion.cursor() as cursor:
            # Verificar propiedad del inventario
            sql_check = "SELECT id_inventario, usuario_id, id_item, tipo_item, equipada FROM inventario WHERE id_inventario = %s"
            cursor.execute(sql_check, (inventory_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'message': 'Item de inventario no encontrado.'}), 404
            if int(row.get('usuario_id')) != int(user_id):
                return jsonify({'success': False, 'message': 'No posees ese item.'}), 403

            tipo = row.get('tipo_item')

            # Si es SKIN, desequipar otras skins del usuario
            if tipo == 'SKIN':
                try:
                    sql_desequip = "UPDATE inventario SET equipada = 0 WHERE usuario_id = %s AND tipo_item = 'SKIN'"
                    cursor.execute(sql_desequip, (user_id,))
                except Exception:
                    pass

            # Alternar equipada en el item seleccionado (si ya estaba equipada, la des-equipamos)
            nueva = 1 if not row.get('equipada') else 0
            try:
                sql_upd = "UPDATE inventario SET equipada = %s WHERE id_inventario = %s"
                cursor.execute(sql_upd, (nueva, inventory_id))

                # Si se trata de una SKIN que queda equipada, actualizar el avatar del usuario
                if tipo == 'SKIN' and nueva == 1:
                    try:
                        # obtener la url de la skin
                        skin_id = row.get('id_item')
                        sql_skin = "SELECT url_imagen FROM skin WHERE skin_id = %s"
                        cursor.execute(sql_skin, (skin_id,))
                        skin_row = cursor.fetchone()
                        skin_url = skin_row.get('url_imagen') if skin_row else None
                        if skin_url:
                            # Actualizar únicamente el avatar del usuario con la URL de la skin equipada.
                            # NO sobrescribimos url_foto_perfil para respetar la foto de perfil personalizada del usuario.
                            sql_update_user = "UPDATE usuario SET url_avatar = %s WHERE usuario_id = %s"
                            cursor.execute(sql_update_user, (skin_url, user_id))
                            # Actualizar la sesión para que los templates muestren la nueva imagen (solo avatar)
                            try:
                                session['url_avatar'] = skin_url
                            except Exception:
                                # Si la sesión no es modificable por alguna razón, no interrumpir el flujo
                                pass
                    except Exception as e:
                        # No crítico si falla al actualizar avatar; registrar y continuar
                        print(f"Warning: no se pudo actualizar url_avatar: {e}", file=sys.stderr)

                conexion.commit()
                resp = {'success': True, 'message': 'Estado de equipamiento actualizado.', 'equipada': bool(nueva)}
                # Si acabamos de equipar una skin, devolver la URL del avatar para que el cliente pueda actualizar el DOM.
                # No devolvemos ni modificamos url_foto_perfil aquí para no sobrescribir la foto de perfil del usuario.
                if tipo == 'SKIN' and nueva == 1 and skin_url:
                    resp['url_avatar'] = skin_url
                return jsonify(resp)
            except Exception as e:
                print(f"Error actualizando equipamiento: {e}", file=sys.stderr)
                return jsonify({'success': False, 'message': 'Error al actualizar.'}), 500

    except Exception as e:
        print(f"Error en api_inventario_equipar: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': 'Error interno.'}), 500



@tienda_bp.route('/api/tienda/comprar', methods=['POST'])
def api_tienda_comprar():
    if not _is_logged_in():
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    data = request.get_json() if request.is_json else request.form
    tipo = data.get('tipo')
    item_id = data.get('id')
    if not tipo or not item_id:
        return jsonify({'success': False, 'message': 'Faltan parámetros.'}), 400

    try:
        item_id = int(item_id)
    except Exception:
        return jsonify({'success': False, 'message': 'ID inválido.'}), 400

    user_id = session.get('user_id')

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión.'}), 500

    try:
        with conexion.cursor() as cursor:
            # detectar inventario table
            inventario_table = 'inventario'
            try:
                cursor.execute("SELECT 1 FROM inventario LIMIT 1")
            except Exception:
                inventario_table = 'Inventario'

            # Verificar si ya posee el item
            sql_check = f"SELECT 1 FROM {inventario_table} WHERE usuario_id=%s AND id_item=%s AND tipo_item=%s"
            cursor.execute(sql_check, (user_id, item_id, tipo.upper()))
            if cursor.fetchone():
                return jsonify({'success': True, 'message': 'Ya adquirido.', 'adquirido': True}), 200

            # Obtener precio del item
            precio = None
            try:
                if tipo.lower() == 'skin':
                    sql_item = "SELECT precio FROM skin WHERE skin_id = %s AND vigencia = 1"
                else:
                    sql_item = "SELECT precio FROM accesorio WHERE accesorio_id = %s AND vigencia = 1"
                cursor.execute(sql_item, (item_id,))
                row = cursor.fetchone()
                if not row:
                    # intentar sin vigencia
                    if tipo.lower() == 'skin':
                        cursor.execute("SELECT precio FROM skin WHERE skin_id = %s", (item_id,))
                    else:
                        cursor.execute("SELECT precio FROM accesorio WHERE accesorio_id = %s", (item_id,))
                    row = cursor.fetchone()

                if not row:
                    return jsonify({'success': False, 'message': 'Ítem no encontrado.'}), 404
                precio = int(row.get('precio') or 0)
            except Exception as e:
                print(f"Error obteniendo precio: {e}", file=sys.stderr)
                return jsonify({'success': False, 'message': 'Error interno.'}), 500

            # Bloquear fila de usuario para evitar race conditions
            try:
                cursor.execute("SELECT cant_monedas FROM usuario WHERE usuario_id=%s FOR UPDATE", (user_id,))
                urow = cursor.fetchone()
                if not urow:
                    return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404
                monedas = int(urow.get('cant_monedas') or 0)
                if monedas < precio:
                    return jsonify({'success': False, 'message': 'Fondos insuficientes.'}), 400

                # Deduct monedas
                nuevo_saldo = monedas - precio
                cursor.execute("UPDATE usuario SET cant_monedas = %s WHERE usuario_id = %s", (nuevo_saldo, user_id))

                # Insertar en inventario
                try:
                    # Comprobar si la columna id_inventario es AUTO_INCREMENT; si no lo es, intentar modificar la tabla
                    try:
                        cursor.execute(
                            "SELECT EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME='id_inventario'",
                            (inventario_table,)
                        )
                        info = cursor.fetchone()
                        extra = info.get('EXTRA') if info else ''
                    except Exception:
                        extra = ''

                    if not extra or 'auto_increment' not in str(extra).lower():
                        # Intentar alterar la tabla para añadir AUTO_INCREMENT
                        try:
                            alter_sql = f"ALTER TABLE {inventario_table} MODIFY id_inventario INT NOT NULL AUTO_INCREMENT"
                            cursor.execute(alter_sql)
                        except Exception as e:
                            # Si falla la alteración, informar específicamente
                            print(f"No se pudo habilitar AUTO_INCREMENT en {inventario_table}. Error: {e}", file=sys.stderr)
                            conexion.rollback()
                            return jsonify({'success': False, 'message': 'Error de configuración de base de datos: id_inventario no es AUTO_INCREMENT y no se puede modificar. Ejecuta ALTER TABLE manualmente.'}), 500

                    sql_ins = f"INSERT INTO {inventario_table} (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion) VALUES (%s, %s, %s, %s, NOW())"
                    cursor.execute(sql_ins, (user_id, item_id, tipo.upper(), 0))
                    id_inventario = cursor.lastrowid
                except Exception as e:
                    print(f"Error insertando inventario: {e}", file=sys.stderr)
                    try:
                        conexion.rollback()
                    except Exception:
                        pass
                    return jsonify({'success': False, 'message': 'Error al insertar inventario.'}), 500

                conexion.commit()
                return jsonify({'success': True, 'message': 'Compra realizada.', 'adquirido': True, 'nuevo_saldo': nuevo_saldo, 'id_inventario': id_inventario}), 200

            except Exception as e:
                print(f"Error en transacción de compra: {e}", file=sys.stderr)
                try:
                    conexion.rollback()
                except Exception:
                    pass
                return jsonify({'success': False, 'message': 'Error en la compra.'}), 500

    except Exception as e:
        print(f"Error en api_tienda_comprar: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': 'Error interno.'}), 500
