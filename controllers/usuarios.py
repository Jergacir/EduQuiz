from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
import pymysql
import sys
import db as dbmod

usuarios_bp = Blueprint('usuarios', __name__, template_folder='../../templates')


@usuarios_bp.route('/crud-usuarios')
def usuarios_index():
    return render_template('crudUsuario.html')


@usuarios_bp.route('/api/usuarios', methods=['GET'])
def listar_usuarios_api():
    # 1. Verificar autenticación
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado. Debes iniciar sesión.'}), 401

    user_id = session['user_id']

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'Error de conexión a la base de datos.'}), 500

    try:
        # Verificación de rol usando solo el cursor (no usar `with conexion:` que puede cambiar el estado de la conexión)
        with conexion.cursor() as cursor:
            sql_check_role = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
            cursor.execute(sql_check_role, (user_id,))
            user_role_data = cursor.fetchone()

            if not user_role_data or user_role_data.get('tipo_usuario') != 'G':
                return jsonify({'error': 'Acceso prohibido. No tienes permisos de administrador.'}), 403

        # Parámetros de paginación y filtros
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
        except ValueError:
            return jsonify({'error': 'page y per_page deben ser enteros.'}), 400

        tipo_filter = request.args.get('tipo')  # A,P,G,E
        vigencia_filter = request.args.get('vigencia')  # '1' o '0' o None

        where_clauses = []
        params = []
        if tipo_filter:
            where_clauses.append('tipo_usuario = %s')
            params.append(tipo_filter.upper())
        if vigencia_filter in ('0', '1'):
            where_clauses.append('vigencia = %s')
            params.append(int(vigencia_filter))

        where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

        # Contar total de registros con filtros
        with conexion.cursor() as cursor:
            count_sql = f"SELECT COUNT(*) AS total FROM usuario {where_sql}"
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone().get('total', 0)

        # Calcular offset y obtener página
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
        offset = (page - 1) * per_page if page > 0 else 0

        usuarios = []
        with conexion.cursor() as cursor:
            sql = f"SELECT usuario_id, username, nombre, correo, tipo_usuario, cant_monedas, dni, vigencia FROM usuario {where_sql} ORDER BY usuario_id LIMIT %s OFFSET %s"
            exec_params = tuple(params) + (per_page, offset)
            cursor.execute(sql, exec_params)
            rows = cursor.fetchall()
            for user in rows:
                usuarios.append({
                    'usuario_id': user.get('usuario_id'),
                    'username': user.get('username'),
                    'nombre': user.get('nombre'),
                    'correo': user.get('correo'),
                    'tipo_usuario': user.get('tipo_usuario'),
                    'cant_monedas': user.get('cant_monedas'),
                    'dni': user.get('dni'),
                    'vigencia': int(user.get('vigencia')) if user.get('vigencia') is not None else 0,
                })

        return jsonify({
            'users': usuarios,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })

    except Exception as e:
        print(f"Error al obtener usuarios (controller): {e}", file=sys.stderr)
        return jsonify({'error': 'Error interno del servidor al obtener datos'}), 500


@usuarios_bp.route('/api/register-gestor', methods=['POST'])
def register_gestor_api():
    data = request.get_json()
    required_fields = ['username', 'nombre', 'contrasena', 'correo', 'dni']
    if not data or any(key not in data for key in required_fields):
        return jsonify({"success": False, "message": "Faltan campos obligatorios: username, nombre, contrasena, correo, dni."}), 400

    username = data['username']
    nombre = data['nombre']
    contrasena_plana = data['contrasena']
    correo = data['correo']
    dni = data['dni']
    verificado_raw = data.get('verificado', 0)
    verificado = 1 if str(verificado_raw) == '1' else 0

    if len(dni) != 8 or not dni.isdigit():
        return jsonify({"success": False, "message": "DNI inválido. Debe contener 8 dígitos."}), 400

    try:
        hashed_password_bytes = __import__('extensions').bcrypt.generate_password_hash(contrasena_plana)
        contrasena_cifrada = hashed_password_bytes.decode('utf-8')
    except Exception:
        return jsonify({"success": False, "message": "Error al cifrar la contraseña."}), 500

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "message": "Error de conexión a la base de datos."}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s"
                cursor.execute(sql_check, (correo, dni))
                if cursor.fetchone():
                    return jsonify({"success": False, "message": "El DNI o correo ya está registrado."}), 409

                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

                tipo_usuario = 'G'
                cursor.execute(sql, (username, nombre, contrasena_cifrada, correo, dni, tipo_usuario, 0, verificado))
                conexion.commit()

        return jsonify({"success": True, "message": f"Gestor '{nombre}' ({username}) creado exitosamente. Verificado: {verificado}"}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"success": False, "message": "Error de integridad: El usuario ya existe o hay un problema con los datos."}), 409
    except Exception as e:
        print(f"Error en el registro de gestor (controller): {e}")
        return jsonify({"success": False, "message": "Ocurrió un error en el sistema."}), 500


@usuarios_bp.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario_api(usuario_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado.'}), 401
    user_id_logueado = session['user_id']

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'Error de conexión a la base de datos.'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_check_role = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
                cursor.execute(sql_check_role, (user_id_logueado,))
                user_role_data = cursor.fetchone()

                if not user_role_data or user_role_data.get('tipo_usuario') != 'G':
                    return jsonify({'error': 'Acceso prohibido. No tienes permisos de gestor.'}), 403

                if usuario_id == user_id_logueado:
                    return jsonify({'error': 'No puedes inactivar tu propia cuenta de Gestor a través de esta interfaz.'}), 403

                sql_update_vigencia = "UPDATE usuario SET vigencia = 0 WHERE usuario_id=%s AND vigencia = 1"
                cursor.execute(sql_update_vigencia, (usuario_id,))
                filas_afectadas = cursor.rowcount
                conexion.commit()

                if filas_afectadas == 0:
                    return jsonify({'error': f'Usuario con ID {usuario_id} no encontrado o ya estaba inactivo.'}), 404

                return jsonify({'success': True, 'message': f'Usuario con ID {usuario_id} inactivado exitosamente (vigente = 0).'}), 200
    except Exception as e:
        print(f"Error al inactivar usuario (controller): {e}", file=sys.stderr)
        return jsonify({'error': 'Error interno del servidor al inactivar datos.'}), 500


@usuarios_bp.route('/api/usuarios/<int:usuario_id>/activar', methods=['PUT'])
def activar_usuario_api(usuario_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado.'}), 401
    user_id_logueado = session['user_id']

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'error': 'Error de conexión a la base de datos.'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_check_role = "SELECT tipo_usuario FROM usuario WHERE usuario_id=%s"
                cursor.execute(sql_check_role, (user_id_logueado,))
                user_role_data = cursor.fetchone()

                if not user_role_data or user_role_data.get('tipo_usuario') != 'G':
                    return jsonify({'error': 'Acceso prohibido. No tienes permisos de gestor.'}), 403

                if usuario_id == user_id_logueado:
                    return jsonify({'error': 'No puedes activar/desactivar tu propia cuenta de Gestor a través de esta interfaz.'}), 403

                sql_update_vigencia = "UPDATE usuario SET vigencia = 1 WHERE usuario_id=%s AND vigencia = 0"
                cursor.execute(sql_update_vigencia, (usuario_id,))
                filas_afectadas = cursor.rowcount
                conexion.commit()

                if filas_afectadas == 0:
                    return jsonify({'error': f'Usuario con ID {usuario_id} no encontrado o ya estaba activo.'}), 404

                return jsonify({'success': True, 'message': f'Usuario con ID {usuario_id} activado exitosamente (vigente = 1).'}), 200
    except Exception as e:
        print(f"Error al activar usuario (controller): {e}", file=sys.stderr)
        return jsonify({'error': 'Error interno del servidor al activar datos.'}), 500


@usuarios_bp.route('/baja_cuenta', methods=['POST'])
def dar_baja_cuenta():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para realizar esta acción.', 'error')
        return redirect(url_for('auth.frm_login'))

    user_id_a_inactivar = session['user_id']
    conexion = dbmod.obtenerConexion()
    if not conexion:
        flash('Error de conexión a la base de datos. Intente más tarde.', 'error')
        return redirect(url_for('usuarios.usuarios_index'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_update_vigencia = "UPDATE usuario SET vigencia = 0 WHERE usuario_id=%s AND vigencia = 1"
                cursor.execute(sql_update_vigencia, (user_id_a_inactivar,))
                filas_afectadas = cursor.rowcount
                conexion.commit()

                if filas_afectadas == 0:
                    flash('Tu cuenta no pudo ser dada de baja. Es posible que ya esté inactiva.', 'warning')
                    return redirect(url_for('usuarios.usuarios_index'))

        flash('Tu cuenta ha sido dada de baja exitosamente. ¡Lamentamos verte partir!', 'success')
        # Cerrar sesión: delegamos al blueprint de auth
        return redirect(url_for('auth.logout'))

    except Exception as e:
        print(f"Error al dar de baja la propia cuenta (controller): {e}", file=sys.stderr)
        flash('Ocurrió un error interno al procesar la baja de la cuenta.', 'error')
        return redirect(url_for('usuarios.usuarios_index'))


@usuarios_bp.route('/api/usuarios', methods=['POST'])
def crear_usuario_api():
    data = request.get_json()
    required_fields = ['username', 'nombre', 'contrasena', 'correo', 'tipo_usuario', 'dni']
    if not data or any(key not in data or not data[key] for key in required_fields):
        return jsonify({"success": False, "error": "Faltan campos obligatorios: nombre, username, contrasena, correo, tipo_usuario, DNI."}), 400

    username = data['username']
    nombre = data['nombre']
    contrasena_plana = data['contrasena']
    correo = data['correo']
    tipo_usuario = data['tipo_usuario'].upper()
    dni = data['dni']

    if len(dni) != 8 or not dni.isdigit():
        return jsonify({"success": False, "error": "DNI inválido. Debe contener 8 dígitos."}), 400

    if tipo_usuario not in ['A', 'P', 'G', 'E']:
        return jsonify({"success": False, "error": "Tipo de usuario inválido (solo A, P, G, E permitidos)."}), 400

    try:
        hashed_password_bytes = __import__('extensions').bcrypt.generate_password_hash(contrasena_plana)
        contrasena_cifrada = hashed_password_bytes.decode('utf-8')
    except Exception:
        return jsonify({"success": False, "error": "Error al cifrar la contraseña."}), 500

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"success": False, "error": "Error de conexión a la base de datos."}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_check = "SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s OR username=%s"
                cursor.execute(sql_check, (correo, dni, username))
                if cursor.fetchone():
                    return jsonify({"success": False, "error": "El DNI, correo o username ya está registrado."}), 409

                sql = """INSERT INTO usuario
                             (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

                cursor.execute(sql, (username, nombre, contrasena_cifrada, correo, dni, tipo_usuario, 0))
                conexion.commit()

        return jsonify({"success": True, "message": f"Usuario '{username}' creado exitosamente."}), 201
    except Exception as e:
        print(f"Error al crear usuario (controller): {e}")
        return jsonify({"success": False, "error": "Ocurrió un error en el sistema."}), 500
