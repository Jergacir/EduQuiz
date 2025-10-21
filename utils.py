import os
import smtplib
import ssl
from email.message import EmailMessage
from flask import url_for
import sys


def mask_email(email: str) -> str:
    try:
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = local[0] + '*'*(len(local)-1)
        else:
            masked_local = local[0] + '*'*(len(local)-2) + local[-1]
        return f"{masked_local}@{domain}"
    except Exception:
        return email


# Funciones de envío de correo simplificadas para mantener la lógica central fuera de main.py
# NOTA: Estas funciones usan variables de entorno y pueden lanzar excepciones si falta configuración
def send_verification_email(to_email: str, code: str):
    """Envía un correo con el código de verificación usando SMTP.

    Configura las variables de entorno:
    - EMAIL_HOST: servidor SMTP (ej: smtp.gmail.com)
    - EMAIL_PORT: puerto (ej: 587)
    - EMAIL_USER: usuario
    - EMAIL_PASS: contraseña o app password
    """
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    # EMAIL_USER se usa para autenticar contra el servidor SMTP
    smtp_user = os.environ.get('EMAIL_USER')
    smtp_pass = os.environ.get('EMAIL_PASS')
    # EMAIL_FROM es la dirección que aparecerá en el encabezado From (debe estar verificada en el proveedor)
    from_header = os.environ.get('EMAIL_FROM') or smtp_user
    if not host or not smtp_user or not smtp_pass:
        raise RuntimeError('Configuración SMTP incompleta. Ajusta EMAIL_HOST/EMAIL_USER/EMAIL_PASS')

    subject = 'Confirma tu cuenta en EduQuiz'

    # Construir enlace de verificación (si estamos en contexto de request, usar url_for)
    try:
        verify_link = url_for('frm_verificar', email=to_email, _external=True)
    except Exception:
        # Fallback: si no hay contexto de app, intentar usar APP_BASE_URL de .env
        base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        verify_link = f"{base}/verificar?email={to_email}" if base else f"/verificar?email={to_email}"

    # Mensaje de texto plano
    text_body = (
        f"Hola,\n\n"
        f"Gracias por registrarte en EduQuiz. Para completar tu registro introduce el siguiente código de verificación:\n\n"
        f"{code}\n\n"
        f"También puedes verificar tu cuenta haciendo clic en el siguiente enlace:\n{verify_link}\n\n"
        f"Si no solicitaste este correo, ignora este mensaje.\n\n"
        f"Saludos,\nEquipo EduQuiz"
    )

    # Mensaje HTML
    html_body = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width,initial-scale=1" />
            <title>Confirma tu cuenta — EduQuiz</title>
        </head>
        <body style="margin:0;padding:0;font-family: 'Segoe UI', Roboto, Arial, sans-serif;background:#f6f9fc;color:#111;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td align="center" style="padding:20px 10px;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="600" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 6px 18px rgba(20,30,50,0.08);">
                            <tr style="background:linear-gradient(90deg,#0a58ca,#3b82f6);color:#fff;">
                                <td style="padding:28px 30px;text-align:left;font-weight:700;font-size:20px;">EduQuiz</td>
                            </tr>
                            <tr>
                                <td style="padding:28px 30px;color:#2b3440;">
                                    <h2 style="margin:0 0 10px 0;font-size:18px;color:#111;">¡Bienvenido a EduQuiz!</h2>
                                    <p style="margin:0 0 18px 0;color:#55606a;line-height:1.45">Gracias por registrarte — solo falta un paso para activar tu cuenta. Ingresa el siguiente código en la página de registro o pulsa el botón para verificar automáticamente.</p>

                                    <div style="margin:18px 0;text-align:center;">
                                        <div style="display:inline-block;background:#f3f6fb;padding:14px 20px;border-radius:12px;font-size:22px;letter-spacing:6px;color:#0a58ca;font-weight:600;">{code}</div>
                                    </div>

                                    <!-- Botón estilo Outlook-friendly usando tabla -->
                                    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:20px 0 auto;" align="center">
                                        <tr>
                                            <td align="center" bgcolor="#0a58ca" style="border-radius:8px;">
                                                <a href="{verify_link}" style="display:inline-block;padding:12px 22px;color:#ffffff;text-decoration:none;font-weight:600;border-radius:8px;">Verificar mi cuenta</a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:18px 30px;background:#fbfdff;color:#94a3b8;font-size:13px;text-align:center;">EduQuiz — Tu camino al éxito académico</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    msg = EmailMessage()
    # Usa EMAIL_FROM si está configurado en el entorno, sino el usuario SMTP
    msg['From'] = from_header
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    # DEBUG: imprimir configuración SMTP (sin exponer la contraseña)
    print(f"[DEBUG] Enviando email SMTP -> host={host}, port={port}, smtp_user={smtp_user}, from_header={from_header}, to={to_email}")

    # Opción para pruebas locales: si SKIP_TLS_VERIFY está activado, crear contexto sin verificación
    skip_tls = os.environ.get('SKIP_TLS_VERIFY', '0') in ('1', 'true', 'True')
    if skip_tls:
        context = ssl._create_unverified_context()
    else:
        context = ssl.create_default_context()

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.set_debuglevel(1)
            # STARTTLS con contexto
            server.starttls(context=context)
            # Autenticación con SMTP_USER
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print("[DEBUG] Email enviado (o al menos enviado al servidor SMTP)")
    except Exception as e:
        # Mostrar traza completa para depuración
        import traceback
        traceback.print_exc()
        # Re-lanzar para que los handlers existentes puedan reaccionar o capturarlo
        raise
