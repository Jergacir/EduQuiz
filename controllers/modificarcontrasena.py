from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import smtplib
import ssl
from email.message import EmailMessage
import secrets
import hashlib
from datetime import datetime, timedelta
import re
import sys
import db as dbmod
from utils import hash_password_sha256


modificarcontrasena_bp = Blueprint('modificarcontrasena', __name__, template_folder='../../templates')


def send_password_reset_email(to_email: str, token: str):
    """Envía el email con el enlace para restablecer la contraseña.

    Usa las variables de entorno EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_FROM.
    Lanza RuntimeError si la configuración SMTP está incompleta.
    """
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    smtp_user = os.environ.get('EMAIL_USER')
    smtp_pass = os.environ.get('EMAIL_PASS')
    from_header = os.environ.get('EMAIL_FROM') or smtp_user
    if not host or not smtp_user or not smtp_pass:
        raise RuntimeError('Configuración SMTP incompleta. Ajusta EMAIL_HOST/EMAIL_USER/EMAIL_PASS')

    # Construir enlace de reset (url_for se resuelve en contexto de request en main)
    try:
        from flask import url_for
        reset_link = url_for('modificarcontrasena.frm_restablecer', token=token, _external=True)
    except Exception:
        base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        reset_link = f"{base}/restablecer?token={token}" if base else f"/restablecer?token={token}"

    subject = 'Restablece tu contraseña en EduQuiz'
    text_body = (
        f"Hola,\n\n"
        f"Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Si no la solicitaste, ignora este correo.\n\n"
        f"Para restablecer tu contraseña, abre el siguiente enlace (válido por 1 hora):\n{reset_link}\n\n"
        f"Si no solicitaste este cambio, puedes ignorar este correo.\n\nSaludos,\nEquipo EduQuiz"
    )

    html_body = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width,initial-scale=1" />
            <title>Restablece tu contraseña — EduQuiz</title>
        </head>
        <body style="margin:0;padding:0;font-family: 'Segoe UI', Roboto, Arial, sans-serif;background:#f6f9fc;color:#111;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td align="center" style="padding:20px 10px;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="600" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 6px 18px rgba(20,30,50,0.08);">
                            <tr style="background:linear-gradient(90deg,#0a58ca,#3b82f6);color:#fff;">
                                <td style="padding:20px 30px;font-weight:700;font-size:18px;">Restablecer contraseña — EduQuiz</td>
                            </tr>
                            <tr>
                                <td style="padding:24px 30px;color:#2b3440;">
                                    <h2 style="margin:0 0 10px 0;font-size:18px;color:#111;">Reestablece tu contraseña</h2>
                                    <p style="margin:0 0 12px 0;font-size:15px;">Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Si no la solicitaste, puedes ignorar este correo.</p>
                                    <p style="margin:8px 0 20px 0;color:#55606a;">El enlace es válido por 1 hora.</p>

                                    <div style="text-align:center;margin:14px 0;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" align="center">
                                            <tr>
                                                <td bgcolor="#0a58ca" style="border-radius:8px;">
                                                    <a href="{reset_link}" style="display:inline-block;padding:12px 20px;color:#fff;text-decoration:none;font-weight:600;border-radius:8px;">Restablecer contraseña</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:16px 30px;background:#fbfdff;color:#94a3b8;font-size:13px;text-align:center;">Si no solicitaste esto, ignora el mensaje. — EduQuiz</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    msg = EmailMessage()
    msg['From'] = from_header
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    skip_tls = os.environ.get('SKIP_TLS_VERIFY', '0') in ('1', 'true', 'True')
    if skip_tls:
        context = ssl._create_unverified_context()
    else:
        context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


@modificarcontrasena_bp.route('/solicitar_restablecer', methods=['GET'], endpoint='frm_solicitar_restablecer')
def frm_solicitar_restablecer():
    return render_template('solicitar_restablecer.html')


@modificarcontrasena_bp.route('/solicitar_restablecer', methods=['POST'], endpoint='solicitar_restablecer')
def solicitar_restablecer():
    email = request.form.get('email')
    if not email:
        flash('Ingresa un correo válido.', 'error')
        return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))

    conexion = dbmod.obtenerConexion()
    if not conexion:
        flash('Error al conectar con la base de datos.', 'error')
        return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))

    try:
        with conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT usuario_id, correo FROM usuario WHERE correo=%s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()
                if not user:
                    # Indicar explícitamente que el correo no existe en el sistema
                    flash('El correo no existe en nuestro sistema.', 'reset_warning')
                    return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))

                usuario_id = user['usuario_id']
                # Generar token y guardarlo hasheado
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
                expires_at = datetime.utcnow() + timedelta(hours=1)

                # DEBUG: mostrar token en consola para pruebas locales (no en producción)
                print(f"[DEBUG] Password reset token para {email}: {token}")

                sql_insert = "INSERT INTO password_reset_tokens (usuario_id, token_hash, expires_at) VALUES (%s, %s, %s)"
                cursor.execute(sql_insert, (usuario_id, token_hash, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
                conexion.commit()

                # Enviar email
                try:
                    send_password_reset_email(email, token)
                    flash(f'Se ha enviado un correo con instrucciones a {email}.', 'reset_info')
                    return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))
                except Exception as e:
                    print(f"Error enviando email de restablecimiento: {e}")
                    flash('No se pudo enviar el correo de restablecimiento. Contacta al administrador.', 'reset_warning')
                    return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))

    except Exception as e:
        print(f"Error en solicitar_restablecer (controller): {e}")
        flash('Ocurrió un error. Intenta más tarde.', 'error')
        return redirect(url_for('modificarcontrasena.frm_solicitar_restablecer'))


@modificarcontrasena_bp.route('/restablecer', methods=['GET'], endpoint='frm_restablecer')
def frm_restablecer():
    token = request.args.get('token')
    if not token:
        flash('Token inválido.', 'error')
        return redirect(url_for('auth.frm_login'))
    return render_template('restablecer.html', token=token)


@modificarcontrasena_bp.route('/restablecer', methods=['POST'], endpoint='restablecer_post')
def restablecer_post():
    token = request.form.get('token')
    nueva = request.form.get('contrasena')
    confirmar = request.form.get('confirmarContrasena')

    if not token or not nueva or not confirmar:
        flash('Faltan campos.', 'error')
        return redirect(url_for('modificarcontrasena.frm_restablecer') + f"?token={token}")

    if nueva != confirmar:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('modificarcontrasena.frm_restablecer') + f"?token={token}")

    # Validación de contraseña fuerte
    pwd = nueva
    pwd_errors = []
    if len(pwd) < 8:
        pwd_errors.append('al menos 8 caracteres')
    if not re.search(r'[A-Z]', pwd):
        pwd_errors.append('una letra mayúscula')
    if not re.search(r'[a-z]', pwd):
        pwd_errors.append('una letra minúscula')
    if not re.search(r'\d', pwd):
        pwd_errors.append('un número')
    if not re.search(r'[!@#$%^&*()_+\-=[\]{};:\"\\|,.<>\/\?`~]', pwd):
        pwd_errors.append('un carácter especial (ej: !@#$%)')

    if pwd_errors:
        flash('La contraseña no cumple los requisitos: ' + ', '.join(pwd_errors), 'error')
        return redirect(url_for('modificarcontrasena.frm_restablecer') + f"?token={token}")

    conexion = dbmod.obtenerConexion()
    if not conexion:
        flash('Error de conexión.', 'error')
        return redirect(url_for('auth.frm_login'))

    try:
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        with conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT prt_id, usuario_id, expires_at FROM password_reset_tokens WHERE token_hash=%s"
                cursor.execute(sql, (token_hash,))
                row = cursor.fetchone()
                if not row:
                    flash('Token inválido o expirado.', 'error')
                    return redirect(url_for('auth.frm_login'))

                expires = row['expires_at']
                if isinstance(expires, str):
                    from datetime import datetime as _dt
                    expires_dt = _dt.strptime(expires, '%Y-%m-%d %H:%M:%S')
                else:
                    expires_dt = expires

                if expires_dt < datetime.utcnow():
                    flash('El token ha expirado.', 'error')
                    return redirect(url_for('auth.frm_login'))

                usuario_id = row['usuario_id']
                # Actualizar contraseña usando bcrypt desde extensions
                try:
                    hashed, _ = hash_password_sha256(nueva)
                except Exception:
                    flash('Error al cifrar la contraseña.', 'error')
                    return redirect(url_for('auth.frm_login'))

                sql_upd = "UPDATE usuario SET contrasena=%s WHERE usuario_id=%s"
                cursor.execute(sql_upd, (hashed, usuario_id))

                sql_del = "DELETE FROM password_reset_tokens WHERE prt_id=%s"
                cursor.execute(sql_del, (row['prt_id'],))
                conexion.commit()

                flash('Contraseña restablecida correctamente. Inicia sesión con tu nueva contraseña.', 'success')
                return redirect(url_for('auth.frm_login'))

    except Exception as e:
        print(f"Error en restablecer_post (controller): {e}", file=sys.stderr)
        flash('Ocurrió un error procesando la solicitud.', 'error')
        return redirect(url_for('auth.frm_login'))
