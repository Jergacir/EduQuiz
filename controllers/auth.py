from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import db as dbmod
import random
import pymysql
import re
from extensions import bcrypt as bcrypt_ext
from utils import send_verification_email, mask_email, hash_password_sha256, verify_password_sha256
from flask import make_response
import hashlib
from auth_utils import generate_jwt_token
from auth_utils import verify_jwt_from_cookie
from auth_utils import generate_jwt_token, verify_jwt_from_cookie

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

def encriptar_sha256(texto):
    texto = texto.encode('utf-8')
    objHash = hashlib.sha256(texto)
    textenc = objHash.hexdigest()
    return textenc

def verify_password_hybrid(password_plain: str, stored_hash: str) -> bool:
    """Verifica contraseña con bcrypt O SHA-256"""
    if not stored_hash or not password_plain:
        print(f"❌ verify_password_hybrid: Datos faltantes - stored_hash={bool(stored_hash)}, password_plain={bool(password_plain)}")
        return False

    print(f"🔍 verify_password_hybrid: Verificando contraseña...")
    print(f"   Hash almacenado: {stored_hash[:30]}...")

    # Detectar si es bcrypt
    if stored_hash.startswith(('$2b$', '$2a$', '$2y$')):
        print(f"   Tipo detectado: BCRYPT")
        try:
            result = bcrypt_ext.check_password_hash(stored_hash, password_plain)
            print(f"   Resultado bcrypt: {result}")
            return result
        except Exception as e:
            print(f"❌ Error verificando bcrypt: {e}")
            return False
    # Detectar si es SHA-256 con salt (formato: hash$salt)
    elif '$' in stored_hash and len(stored_hash) > 64:
        print(f"   Tipo detectado: SHA-256")
        print(f"   Longitud total: {len(stored_hash)}")
        try:
            result = verify_password_sha256(password_plain, stored_hash)
            print(f"   Resultado SHA-256: {result}")
            return result
        except Exception as e:
            print(f"❌ Error verificando SHA-256: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"⚠️ Hash no reconocido - longitud: {len(stored_hash)}, contiene '$': {'$' in stored_hash}")
        return False


@auth_bp.route('/login')
def frm_login():
    """
    ✨ NUEVA LÓGICA: Si el usuario ya está autenticado (tiene sesión y JWT válido),
    redirigir automáticamente a home
    """

    # 1. Verificar si existe sesión activa

    if 'user_id' in session:
        # 2. Verificar si el JWT es válido
        jwt_payload = verify_jwt_from_cookie()

        if jwt_payload:
            # 3. Verificar que el user_id coincida
            if jwt_payload.get('user_id') == session.get('user_id'):
                print(f"✅ Usuario ya autenticado (ID: {session.get('user_id')}), redirigiendo a home...")
                flash('Ya has iniciado sesión.', 'info')
                return redirect(url_for('pages.frm_home'))
            else:
                # JWT no coincide con sesión - limpiar todo
                print(f"⚠️ JWT no coincide con sesión, limpiando...")
                session.clear()
        else:
            # JWT inválido o expirado - limpiar sesión
            print(f"⚠️ JWT inválido o expirado, limpiando sesión...")
            session.clear()

    # Si llegamos aquí, el usuario NO está autenticado

    return render_template('login.html')


@auth_bp.route('/registro')
def frm_registro():
    return render_template('registro.html')


@auth_bp.route('/verificar', methods=['GET'], endpoint='frm_verificar')
def frm_verificar():
    email = request.args.get('email', '')
    masked = mask_email(email) if email else ''
    return render_template('verificar.html', email=email, email_masked=masked)


@auth_bp.route('/logout')
def logout():
    # 1. Limpiar sesión de Flask
    try:
        session.clear()
    except Exception:
        for k in ['user_id', 'url_foto_perfil', 'url_avatar', 'username', 'cant_monedas', 'tipo_usuario']:
            session.pop(k, None)

    flash('Has cerrado sesión exitosamente.', 'success')
    resp = make_response(redirect(url_for('auth.frm_login')))

    # 2. ✨ ELIMINAR COOKIE DE SESIÓN DE FLASK (
    resp.set_cookie('session', '', expires=0, path='/', httponly=True, samesite='Lax')

    # 3. ✨ ELIMINAR JWT TOKEN
    resp.set_cookie('jwt_token', '', expires=0, path='/', httponly=True, samesite='Lax')

    # 4. Eliminar cookies legacy
    resp.set_cookie('username', '', expires=0, path='/')
    resp.set_cookie('correo', '', expires=0, path='/')

    print("🧹 Logout: Todas las cookies eliminadas (session, jwt_token, username, correo)")

    return resp


@auth_bp.route('/procesarregistro', methods=['POST'])
def procesarregistro():
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

    # ✅ ENCRIPTAR CON SHA-256
    contrasena_cifrada, salt_usado = hash_password_sha256(contrasena_plana)
    print(f"🔐 Registro: Nueva contraseña encriptada con SHA-256")
    print(f"   Salt: {salt_usado[:20]}...")
    print(f"   Hash completo: {contrasena_cifrada[:50]}...")

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

        try:
            send_verification_email(email, verification_code)
            flash('Se envió un código de verificación a tu correo.', 'info')
        except Exception:
            flash('No se pudo enviar el correo de verificación automáticamente.', 'warning')

        masked = mask_email(email)
        return render_template('verificar.html', email=email, email_masked=masked)

    except Exception as e:
        print(f"Error en procesarregistro: {e}")
        flash('Ocurrió un error en el sistema.', 'error')
        return redirect(url_for('auth.frm_registro'))


@auth_bp.route('/procesarlogin', methods=['POST'])
def procesarlogin():
    # ✅ DETECTAR SI ES JSON O FORM-DATA
    if request.is_json:
        data = request.get_json()
        correo = data.get('correo')
        contrasena_plana = data.get('contrasena')
    else:
        correo = request.form.get('correo')
        contrasena_plana = request.form.get('contrasena')

    print(f"\n{'='*60}")
    print(f"🔐 INICIO DE SESIÓN - {correo}")
    print(f"{'='*60}")

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # ✅ MEJORAR DETECCIÓN DE API REQUEST
    is_api_request = (
        request.is_json or  # Si envía JSON
        request.headers.get('Accept') == 'application/json' or
        is_ajax
    )

    conexion = dbmod.obtenerConexion()
    if not conexion:
        print("❌ Error: No hay conexión a la BD")
        if is_api_request:
            return jsonify({'success': False, 'message': 'Error de conexión a BD.'}), 500
        return redirect(url_for('pages.frm_error'))

    cursor = None

    try:
        cursor = conexion.cursor()

        # 1. BUSCAR USUARIO
        sql = "SELECT usuario_id, contrasena, verificado, correo, vigencia, COALESCE(url_foto_perfil,'') AS url_foto_perfil, COALESCE(url_avatar,'') AS url_avatar, username, cant_monedas, tipo_usuario FROM usuario WHERE correo=%s"
        cursor.execute(sql, (correo,))
        result = cursor.fetchone()

        if not result:
            print(f"❌ Usuario no encontrado: {correo}")
            if is_api_request:
                return jsonify({'success': False, 'code': 'email_not_found', 'message': 'Correo no encontrado.'}), 404
            flash('Correo no encontrado. ¿Deseas registrarte?', 'error')
            return redirect(url_for('auth.frm_login'))

        stored_hash = result.get('contrasena')
        usuario_id = result['usuario_id']
        username = result.get('username') or ''
        tipo_usuario = result.get('tipo_usuario') or ''

        print(f"✅ Usuario encontrado: ID={usuario_id}")

        # 2. VERIFICAR CONTRASEÑA
        if not verify_password_hybrid(contrasena_plana, stored_hash):
            print(f"❌ CONTRASEÑA INCORRECTA")
            if is_api_request:
                return jsonify({'success': False, 'code': 'credentials', 'message': 'Credenciales incorrectas.'}), 401
            flash('Credenciales incorrectas.', 'error')
            return redirect(url_for('auth.frm_login'))

        print(f"✅ CONTRASEÑA CORRECTA")

        # 3. VERIFICAR ESTADO DE CUENTA
        if result.get('vigencia', 0) == 0:
            print(f"⚠️ Cuenta inactiva")
            if is_api_request:
                return jsonify({'success': False, 'code': 'inactive', 'message': 'Tu cuenta está inactiva.'}), 403
            flash('Tu cuenta está inactiva.', 'error')
            return redirect(url_for('auth.frm_login'))

        if result.get('verificado', 0) == 0:
            print(f"⚠️ Cuenta no verificada")
            if is_api_request:
                return jsonify({'success': False, 'code': 'not_verified', 'message': 'Tu cuenta aún no está verificada.'}), 403
            flash('Tu cuenta aún no está verificada.', 'warning')
            return render_template('verificar.html', email=result.get('correo'), email_masked=mask_email(result.get('correo')))

        # 4. MIGRAR DE BCRYPT A SHA-256 SI ES NECESARIO
        if stored_hash.startswith(('$2b$', '$2a$', '$2y$')):
            try:
                new_hash, salt_usado = hash_password_sha256(contrasena_plana)
                print(f"🔄 Migrando usuario {usuario_id} de bcrypt a SHA-256...")
                cursor.execute("UPDATE usuario SET contrasena=%s WHERE usuario_id=%s", (new_hash, usuario_id))
                conexion.commit()
                print(f"✅ Usuario {usuario_id} migrado exitosamente")
            except Exception as e:
                print(f"❌ Error migrando usuario {usuario_id}: {e}")
                try:
                    conexion.rollback()
                except:
                    pass

        # 5. ✨ GENERAR TOKEN JWT
        jwt_token = generate_jwt_token(usuario_id, username, tipo_usuario)

        if not jwt_token:
            print(f"❌ Error generando JWT para usuario {usuario_id}")
            if is_api_request:
                return jsonify({'success': False, 'message': 'Error generando token de autenticación'}), 500
            flash('Error en el sistema. Intenta nuevamente.', 'error')
            return redirect(url_for('auth.frm_login'))

        print(f"✅ JWT generado exitosamente")

        # 6. CREAR SESIÓN DE FLASK
        session['user_id'] = usuario_id
        session['url_foto_perfil'] = result.get('url_foto_perfil') or ''
        session['url_avatar'] = result.get('url_avatar') or ''
        session['username'] = username
        session['cant_monedas'] = result.get('cant_monedas') or 0
        session['tipo_usuario'] = tipo_usuario

        print(f"✅ LOGIN EXITOSO - Sesión y JWT creados")
        print(f"📊 is_api_request={is_api_request}, request.is_json={request.is_json}")

        # 7. COOKIES LEGACY
        username_hash = encriptar_sha256(username)
        correo_hash = encriptar_sha256(result.get('correo', ''))

        is_pure_api_call = is_api_request and not is_ajax

        # 8️⃣ DETECTAR SI ES REQUEST DE API (Postman) o NAVEGADOR
        if is_pure_api_call:
            # PARA POSTMAN: Retornar JWT en el body
            return jsonify({
                'success': True,
                'message': 'Login exitoso',
                'jwt_token': jwt_token,  # 🔑 ESTO ES LO QUE USARÁS EN POSTMAN
                'user': {
                    'usuario_id': usuario_id,
                    'username': username,
                    'tipo_usuario': tipo_usuario,
                    'cant_monedas': result.get('cant_monedas') or 0
                }
            }), 200
        else:
            # 1. Crear la respuesta base (Redirección para form tradicional o JSON para AJAX)
            if is_ajax:
                # Si es AJAX, devolvemos JSON con la URL de redirección
                resp = make_response(jsonify({'success': True, 'redirect_to': url_for('pages.frm_home')}), 200)
                print(f"📊 Respuesta AJAX. Cookies configuradas.")
            else:
                # Si es formulario tradicional, redireccionamos directamente
                resp = make_response(redirect(url_for('pages.frm_home')))
                print(f"📊 Respuesta Formulario. Cookies configuradas.")

            # 2. Establecer JWT en cookie

            # PARA NAVEGADOR: Redireccionar y establecer cookies
            #resp = make_response(redirect(url_for('pages.frm_home')))

            # Establecer JWT en cookie
            resp.set_cookie(
                'jwt_token',
                jwt_token,
                max_age=60*60*24*30,
                httponly=True,
                secure=True,
                samesite='Lax'
            )

            # Cookies legacy
            resp.set_cookie('username', username_hash, max_age=60*60*24*30)
            resp.set_cookie('correo', correo_hash, max_age=60*60*24*30)

            return resp


    except Exception as e:
        print(f"❌ Error CRÍTICO en procesarlogin: {e}")
        import traceback
        traceback.print_exc()

        if is_api_request:
            return jsonify({'success': False, 'message': 'Error interno del servidor.'}), 500
        return redirect(url_for('pages.frm_error'))
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conexion:
            try:
                conexion.close()
            except:
                pass


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

                    def generate_username_from_fullname(fullname: str) -> str:
                        try:
                            parts = [p for p in fullname.strip().split() if p]
                            if not parts:
                                return temp.get('username') or 'user'
                            first_name = parts[0].title()
                            if len(parts) >= 3:
                                last_parts = parts[-2:]
                            elif len(parts) == 2:
                                last_parts = [parts[-1]]
                            else:
                                last_parts = []

                            initials = ''
                            for lp in last_parts:
                                if lp:
                                    initials += lp[0].upper()

                            username_candidate = f"{first_name}_{initials}" if initials else f"{first_name}"
                            username_candidate = username_candidate.replace(' ', '_')
                            return username_candidate
                        except Exception:
                            return temp.get('username') or 'user'

                    base_username = generate_username_from_fullname(nombre_final)
                    username = base_username
                    suffix = 1
                    cursor.execute("SELECT 1 FROM usuario WHERE username=%s", (username,))
                    while cursor.fetchone():
                        username = f"{base_username}{suffix}"
                        suffix += 1
                        cursor.execute("SELECT 1 FROM usuario WHERE username=%s", (username,))

                    print(f"🔐 Verificación: Insertando usuario con contraseña SHA-256")
                    print(f"   Hash: {temp['contrasena'][:50]}...")

                    # ✅ La contraseña YA está encriptada en registro_temp
                    cursor.execute("""
                        INSERT INTO usuario (username, nombre, contrasena, correo, dni, tipo_usuario, cant_monedas, verificado)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,1)
                    """, (username, nombre_final, temp['contrasena'], temp['correo'],
                          temp['dni'], temp['tipo_usuario'], temp.get('cant_monedas', 0)))

                    cursor.execute("DELETE FROM registro_temp WHERE temp_id=%s", (temp['temp_id'],))

                    try:
                        cursor.execute("SELECT usuario_id FROM usuario WHERE correo=%s", (temp['correo'],))
                        new_user = cursor.fetchone()
                        new_user_id = new_user.get('usuario_id') if new_user else None
                        if new_user_id:
                            inventario_table = 'inventario'
                            try:
                                cursor.execute("SELECT 1 FROM inventario LIMIT 1")
                            except Exception:
                                inventario_table = 'Inventario'

                            try:
                                cursor.execute("SELECT skin_id FROM skin WHERE COALESCE(skinDefault, 0) = 1")
                                default_skins = cursor.fetchall() or []
                            except Exception:
                                default_skins = []

                            if not default_skins:
                                try:
                                    cursor.execute("SELECT skin_id FROM skin WHERE vigencia = 1 ORDER BY skin_id ASC LIMIT 1")
                                    fallback = cursor.fetchall() or []
                                    if fallback:
                                        default_skins = fallback
                                except Exception:
                                    default_skins = []

                            for ds in default_skins:
                                try:
                                    sk_id = ds.get('skin_id') or ds.get('id') or ds
                                    check_sql = f"SELECT 1 FROM {inventario_table} WHERE usuario_id=%s AND id_item=%s AND tipo_item='SKIN'"
                                    cursor.execute(check_sql, (new_user_id, sk_id))
                                    if not cursor.fetchone():
                                        insert_sql = f"INSERT INTO {inventario_table} (usuario_id, id_item, tipo_item, equipada, fecha_adquisicion) VALUES (%s, %s, %s, %s, NOW())"
                                        cursor.execute(insert_sql, (new_user_id, sk_id, 'SKIN', 0))
                                except Exception as e:
                                    print(f"Warning asignando skin por defecto: {e}")
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


@auth_bp.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    data = request.get_json(silent=True)
    email = data.get('email') if data else request.form.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Falta el email'}), 400

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