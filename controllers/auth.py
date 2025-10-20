from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import db as dbmod
import random
import pymysql
import re
from extensions import bcrypt as bcrypt_ext

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')


@auth_bp.route('/login')
def frm_login():
    return render_template('login.html')


@auth_bp.route('/registro')
def frm_registro():
    return render_template('registro.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
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

    if not conexion:
        return redirect(url_for('pages.frm_error'))

    try:
        with conexion.cursor() as cursor:
            sql = 'SELECT usuario_id, contrasena, verificado, correo, vigencia FROM usuario WHERE correo=%s'
            cursor.execute(sql, (correo,))
            result = cursor.fetchone()

        if result and bcrypt_ext.check_password_hash(result['contrasena'], contrasena_plana):
            if result.get('vigencia', 0) == 0:
                flash('Tu cuenta está inactiva.', 'error')
                return redirect(url_for('auth.frm_login'))
            if result.get('verificado', 0) == 0:
                flash('Tu cuenta aún no está verificada.', 'warning')
                return render_template('verificar.html', email=result.get('correo'), email_masked=__import__('utils').mask_email(result.get('correo')))
            session['user_id'] = result['usuario_id']
            return redirect(url_for('pages.frm_home'))
        else:
            flash('Credenciales incorrectas.', 'error')
            return redirect(url_for('auth.frm_login'))

    except Exception as e:
        print(f"Error en procesarlogin: {e}")
        return redirect(url_for('pages.frm_error'))


@auth_bp.route('/procesar_verificacion', methods=['POST'])
def procesar_verificacion():
    # Esta función se mantiene en main.py en parte, se puede delegar a aquí si se desea
    # Para compatibilidad, importamos la implementación global si existe
    from main import procesar_verificacion as main_proc_ver
    return main_proc_ver()


@auth_bp.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    from main import reenviar_codigo as main_reenviar
    return main_reenviar()
