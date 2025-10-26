from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import db as dbmod
import random
import pymysql
import re
from extensions import bcrypt as bcrypt_ext
from utils import send_verification_email, mask_email

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')


@auth_bp.route('/login')
def frm_login():
    return render_template('login.html')


@auth_bp.route('/registro')
def frm_registro():
    return render_template('registro.html')


@auth_bp.route('/verificar', methods=['GET'], endpoint='frm_verificar')
def frm_verificar():
    """Página para que el usuario ingrese el código de verificación que recibió por email.

    Acepta un parámetro `email` en la query string para prellenar el campo.
    """
    email = request.args.get('email', '')
    masked = mask_email(email) if email else ''
    return render_template('verificar.html', email=email, email_masked=masked)


@auth_bp.route('/logout')
def logout():
    # Limpiar toda la sesión para evitar que queden valores de avatar u otros datos
    try:
        session.clear()
    except Exception:
        # Fallback: eliminar claves conocidas si clear no funciona
        for k in ['user_id', 'url_foto_perfil', 'url_avatar', 'username', 'cant_monedas']:
            session.pop(k, None)
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.frm_login'))


@auth_bp.route('/procesarregistro', methods=['POST'])
def procesarregistro():
    # Mover la lógica del viejo main.procesarregistro aquí
    tipo = request.form.get('tipo')
    dni = request.form.get('dni')
    email = request.form.get('email')
    contrasena_plana = request.form.get('contrasena')
    confirmar = request.form.get('confirmarContrasena')

    if not tipo or not dni or not email or not contrasena_plana or not confirmar:
        flash('Faltan campos obligatorios.', 'error')
        return redirect(url_for('auth.frm_registro'))

    if len(dni) != 8 or not dni.isdigit():
        flash('DNI inválido. Debe contener 8 dígitos.', 'error')
        return redirect(url_for('auth.frm_registro'))

    if contrasena_plana != confirmar:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('auth.frm_registro'))

    pwd = contrasena_plana
    pwd_errors = []
    if len(pwd) < 8:
        pwd_errors.append('al menos 8 caracteres')
    if not re.search(r'[A-Z]', pwd):
        pwd_errors.append('una letra mayúscula')
    if not re.search(r'[a-z]', pwd):
        pwd_errors.append('una letra minúscula')
    if not re.search(r'\d', pwd):
        pwd_errors.append('un número')
    if not re.search(r'[!@#$%^&*()_+\-=[\]{};:\"\\|,.<>\/?`~]', pwd):
        pwd_errors.append('un carácter especial (ej: !@#$%)')

    if pwd_errors:
        flash('La contraseña es débil. Debe contener: ' + ', '.join(pwd_errors), 'error')
        return redirect(url_for('auth.frm_registro'))

    tipo_usuario = None
    if tipo == 'Docente':
        if not email.endswith('@usat.edu.pe'):
            email = f"{email}@usat.edu.pe"
        tipo_usuario = 'P'
    elif tipo == 'Alumno':
        if not email.endswith('@usat.pe'):
            email = f"{dni}@usat.pe"
        tipo_usuario = 'A'
    else:
        flash('Tipo de usuario inválido.', 'error')
        return redirect(url_for('auth.frm_registro'))

    hashed_bytes = bcrypt_ext.generate_password_hash(contrasena_plana)
    contrasena_cifrada = hashed_bytes.decode('utf-8')

    username = email.split('@')[0]
    nombre = username.replace('_', ' ').title()

    verification_code = ''.join(str(random.randint(0,9)) for _ in range(6))

    conexion = dbmod.obtenerConexion()
    if not conexion:
        flash('Error de conexión a BD.', 'error')
        return redirect(url_for('auth.frm_registro'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql_check = 'SELECT usuario_id FROM usuario WHERE correo=%s OR dni=%s'
                cursor.execute(sql_check, (email, dni))
                if cursor.fetchone():
                    flash('El DNI o correo ya está registrado.', 'error')
                    return redirect(url_for('auth.frm_registro'))

                sql_temp = 'SELECT temp_id FROM registro_temp WHERE correo=%s'
                cursor.execute(sql_temp, (email,))
                temp_row = cursor.fetchone()

                if temp_row:
                    sql_update = '''UPDATE registro_temp SET username=%s, nombre=%s, contrasena=%s, dni=%s, tipo_usuario=%s, cant_monedas=%s, verification_code=%s, created_at=CURRENT_TIMESTAMP WHERE temp_id=%s'''
                    cursor.execute(sql_update, (username, nombre, contrasena_cifrada, dni, tipo_usuario, 0, verification_code, temp_row['temp_id']))
                else:
                    sql_insert_temp = '''INSERT INTO registro_temp (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verification_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
                    cursor.execute(sql_insert_temp, (username, nombre, contrasena_cifrada, email, dni, tipo_usuario, 0, verification_code))

                conexion.commit()

        # Intentar enviar código de verificación (utils.send_verification_email)
        try:
            from utils import send_verification_email
            send_verification_email(email, verification_code)
            flash('Se envió un código de verificación a tu correo.', 'info')
        except Exception:
            flash('No se pudo enviar el correo de verificación automáticamente.', 'warning')

        masked = __import__('utils').mask_email(email)
        return render_template('verificar.html', email=email, email_masked=masked)

    except Exception as e:
        print(f"Error en procesarregistro: {e}")
        flash('Ocurrió un error en el sistema.', 'error')
        return redirect(url_for('auth.frm_registro'))


@auth_bp.route('/procesarlogin', methods=['POST'])
def procesarlogin():
    correo = request.form.get('correo')
    contrasena_plana = request.form.get('contrasena')
    conexion = dbmod.obtenerConexion()

    # Detectar si la petición viene por AJAX (X-Requested-With) para devolver JSON
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not conexion:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Error de conexión a BD.'}), 500
        return redirect(url_for('pages.frm_error'))

    try:
        with conexion.cursor() as cursor:
            sql = "SELECT usuario_id, contrasena, verificado, correo, vigencia, COALESCE(url_foto_perfil,'') AS url_foto_perfil, COALESCE(url_avatar,'') AS url_avatar, username, cant_monedas, tipo_usuario FROM usuario WHERE correo=%s"
            cursor.execute(sql, (correo,))
            result = cursor.fetchone()

        if not result:
            # Correo no encontrado
            if is_ajax:
                return jsonify({'success': False, 'code': 'email_not_found', 'message': 'Correo no encontrado.'}), 404
            flash('Correo no encontrado. ¿Deseas registrarte?', 'error')
            return redirect(url_for('auth.frm_login'))

        if result and bcrypt_ext.check_password_hash(result['contrasena'], contrasena_plana):
            # Usuario encontrado y contraseña correcta
            if result.get('vigencia', 0) == 0:
                # Cuenta inactiva
                if is_ajax:
                    return jsonify({'success': False, 'code': 'inactive', 'message': 'Tu cuenta está inactiva.'}), 403
                flash('Tu cuenta está inactiva.', 'error')
                return redirect(url_for('auth.frm_login'))

            if result.get('verificado', 0) == 0:
                # No verificado
                if is_ajax:
                    return jsonify({'success': False, 'code': 'not_verified', 'message': 'Tu cuenta aún no está verificada.'}), 403
                flash('Tu cuenta aún no está verificada.', 'warning')
                return render_template('verificar.html', email=result.get('correo'), email_masked=__import__('utils').mask_email(result.get('correo')))

            # Login exitoso
            session['user_id'] = result['usuario_id']
            # Guardar datos útiles en la sesión para evitar inconsistencias en el header
            try:
                session['url_foto_perfil'] = result.get('url_foto_perfil') or ''
                session['url_avatar'] = result.get('url_avatar') or ''
                session['username'] = result.get('username') or ''
                session['cant_monedas'] = result.get('cant_monedas') or 0
                session['tipo_usuario'] = result.get('tipo_usuario') or ''
            except Exception:
                # No crítico si falla almacenar en sesión
                pass
            if is_ajax:
                return jsonify({'success': True, 'redirect': url_for('pages.frm_home')}), 200
            return redirect(url_for('pages.frm_home'))

        else:
            # Credenciales incorrectas (usuario existe pero contraseña no coincide)
            if is_ajax:
                return jsonify({'success': False, 'code': 'credentials', 'message': 'Credenciales incorrectas.'}), 401
            flash('Credenciales incorrectas.', 'error')
            return redirect(url_for('auth.frm_login'))

    except Exception as e:
        print(f"Error en procesarlogin: {e}")
        return redirect(url_for('pages.frm_error'))


@auth_bp.route('/procesar_verificacion', methods=['POST'])
def procesar_verificacion():
    data = request.get_json(silent=True)
    if data:
        email = data.get('email')
        codigo = data.get('codigo')
        nombre_reniec = data.get('nombre_reniec')
    else:
        email = request.form.get('email')
        codigo = request.form.get('codigo')
        nombre_reniec = request.form.get('nombre_reniec')

    print("=== [DEBUG procesar_verificacion] ===")
    print(f"Email: {email}, Nombre RENIEC: {nombre_reniec}")
    print("===================================")

    if not email or not codigo:
        if data:
            return jsonify({'success': False, 'message': 'Faltan datos para verificar la cuenta.'}), 400
        flash('Faltan datos para verificar la cuenta.', 'error')
        return redirect(url_for('auth.frm_registro'))

    conexion = dbmod.obtenerConexion()
    if not conexion:
        if data:
            return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500
        return redirect(url_for('pages.frm_error'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM registro_temp WHERE correo=%s", (email,))
                temp = cursor.fetchone()

                if not temp:
                    cursor.execute("SELECT usuario_id, verificado FROM usuario WHERE correo=%s", (email,))
                    user_row = cursor.fetchone()
                    if user_row and user_row.get('verificado') == 1:
                        msg = 'Cuenta ya verificada. Puedes iniciar sesión.'
                        if data:
                            return jsonify({'success': False, 'message': msg}), 200
                        flash(msg, 'info')
                        return redirect(url_for('auth.frm_login'))

                    msg = 'Correo no encontrado en el registro temporal. Vuelve a registrarte.'
                    if data:
                        return jsonify({'success': False, 'message': msg}), 404
                    flash(msg, 'error')
                    return redirect(url_for('auth.frm_registro'))

                if temp.get('verification_code') == codigo:
                    dni = temp.get('dni')
                    nombre_final = nombre_reniec.strip() if nombre_reniec else temp.get('nombre')
                    if nombre_final.strip() == dni:
                        nombre_final = "(Sin nombre RENIEC)"

                    cursor.execute("""
                        INSERT INTO usuario (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,1)
                    """, (temp['username'], nombre_final, temp['contrasena'], temp['correo'],
                          temp['dni'], temp['tipo_usuario'], temp['cant_monedas']))

                    cursor.execute("DELETE FROM registro_temp WHERE temp_id=%s", (temp['temp_id'],))
                    # Asignar skins por defecto a este nuevo usuario (si existen)
                    try:
                        # Obtener el id del usuario recién insertado de forma robusta
                        cursor.execute("SELECT usuario_id FROM usuario WHERE correo=%s", (temp['correo'],))
                        new_user = cursor.fetchone()
                        new_user_id = new_user.get('usuario_id') if new_user else None
                        if new_user_id:
                            # Determinar nombre de la tabla inventario (mayúsc/minúsc)
                            inventario_table = 'inventario'
                            try:
                                cursor.execute("SELECT 1 FROM inventario LIMIT 1")
                            except Exception:
                                inventario_table = 'Inventario'

                            # Obtener skins por defecto (skinDefault = 1)
                            try:
                                cursor.execute("SELECT skin_id FROM skin WHERE COALESCE(skinDefault, 0) = 1")
                                default_skins = cursor.fetchall() or []
                            except Exception:
                                default_skins = []

                            # Si no hay skins explícitamente marcadas como default, usar un fallback
                            # (por ejemplo, la primera skin activa encontrada) para garantizar
                            # que los usuarios reciban al menos una skin inicial.
                            if not default_skins:
                                try:
                                    cursor.execute("SELECT skin_id FROM skin WHERE vigencia = 1 ORDER BY skin_id ASC LIMIT 1")
                                    fallback = cursor.fetchall() or []
                                    if fallback:
                                        default_skins = fallback
                                        print("Info: no se encontraron skins con skinDefault=1; usando fallback (primera skin activa).")
                                except Exception:
                                    # mantener default_skins vacío si falla el fallback
                                    default_skins = []

                            for ds in default_skins:
                                try:
                                    sk_id = ds.get('skin_id') or ds.get('id') or ds
                                    # Verificar que no exista ya en el inventario del usuario
                                    check_sql = f"SELECT 1 FROM {inventario_table} WHERE usuario_id=%s AND id_item=%s AND tipo_item='SKIN'"
                                    cursor.execute(check_sql, (new_user_id, sk_id))
                                    if not cursor.fetchone():
                                        insert_sql = f"INSERT INTO {inventario_table} (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion) VALUES (%s, %s, %s, %s, NOW())"
                                        cursor.execute(insert_sql, (new_user_id, sk_id, 'SKIN', 0))
                                except Exception as e:
                                    print(f"Warning asignando skin por defecto (usuario {new_user_id}): {e}")
                    except Exception as e:
                        print(f"Warning al asignar skins por defecto: {e}")
                    conexion.commit()

                    if data:
                        return jsonify({'success': True, 'message': 'Registro completado correctamente.',
                                        'dni': dni, 'nombre': nombre_final}), 200

                    flash('Registro completado correctamente. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('auth.frm_login'))

                else:
                    if data:
                        return jsonify({'success': False, 'message': 'Código incorrecto.'}), 400
                    flash('Código incorrecto. Intenta de nuevo.', 'error')
                    return render_template('verificar.html', email=email, email_masked=mask_email(email))

    except Exception as e:
        print(f"❌ Error en procesar_verificacion: {e}")
        if data:
            return jsonify({'success': False, 'message': 'Error interno del servidor.'}), 500
        return redirect(url_for('pages.frm_error'))


@auth_bp.route('/api/get_dni', methods=['GET'])
def get_dni():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email requerido"}), 400

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({"error": "No hay conexión"}), 500

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT dni FROM registro_temp WHERE correo=%s", (email,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Registro temporal no encontrado"}), 404
            return jsonify({"dni": row.get("dni")})
    except Exception as e:
        return jsonify({"error": "Error interno", "detail": str(e)}), 500
# ------------------- Reenviar código -------------------
@auth_bp.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    data = request.get_json(silent=True)
    email = data.get('email') if data else request.form.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Falta el email'}), 400 if data else flash('Falta el email', 'error')

    conexion = dbmod.obtenerConexion()
    if not conexion:
        return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500

    try:
        with conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT temp_id FROM registro_temp WHERE correo=%s", (email,))
                temp = cursor.fetchone()
                new_code = ''.join(str(random.randint(0,9)) for _ in range(6))

                if temp:
                    cursor.execute("UPDATE registro_temp SET verification_code=%s, created_at=CURRENT_TIMESTAMP WHERE temp_id=%s",
                                   (new_code, temp['temp_id']))
                else:
                    cursor.execute("SELECT * FROM usuario WHERE correo=%s", (email,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return jsonify({'success': False, 'message': 'Email no encontrado'}), 404
                    if user_row.get('verificado') == 1:
                        return jsonify({'success': False, 'message': 'Cuenta ya verificada.'}), 400
                    cursor.execute("""
                        INSERT INTO registro_temp (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verification_code)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (user_row['username'], user_row['nombre'], user_row['contrasena'],
                          user_row['correo'], user_row['dni'], user_row['tipo_usuario'],
                          user_row.get('cant_monedas', 0), new_code))
                conexion.commit()

                try:
                    send_verification_email(email, new_code)
                except Exception as e:
                    print(f"Error enviando email: {e}")
                    return jsonify({'success': False, 'message': 'No se pudo enviar el correo.'}), 500

                return jsonify({'success': True, 'message': 'Código reenviado.', 'email_masked': mask_email(email)}), 200

    except Exception as e:
        print(f"❌ Error en reenviar_codigo: {e}")
        return jsonify({'success': False, 'message': 'Error interno.'}), 500
