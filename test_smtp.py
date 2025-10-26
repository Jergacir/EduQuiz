"""
Script de prueba SMTP para EduQuiz.
- Carga variables desde .env (usa python-dotenv)
- Envía un correo de prueba y muestra logs en la consola

Uso:
1) Crea un archivo .env en la raíz con EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS y opcional TEST_TO
2) Ejecuta: python smtp_test.py
"""
from dotenv import load_dotenv
import os
import smtplib
import ssl
from email.message import EmailMessage
import random

load_dotenv()

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
TEST_TO = os.getenv('TEST_TO') or EMAIL_USER
EMAIL_FROM = os.getenv('EMAIL_FROM') or EMAIL_USER
from_header = EMAIL_FROM

if not EMAIL_HOST or not EMAIL_USER or not EMAIL_PASS:
    print('Faltan variables SMTP en .env. Asegúrate de tener EMAIL_HOST, EMAIL_PORT, EMAIL_USER y EMAIL_PASS')
    exit(1)

# Generar un código de verificación de 6 dígitos (igual que en la app)
verification_code = ''.join(str(random.randint(0,9)) for _ in range(6))

# Construir enlace de verificación usando APP_BASE_URL si está disponible
base = os.getenv('APP_BASE_URL', '').rstrip('/')
if base:
    verify_link = f"{base}/verificar?email={TEST_TO}"
else:
    # Fallback a localhost (útil para pruebas locales)
    verify_link = f"http://localhost:5000/verificar?email={TEST_TO}"

msg = EmailMessage()
# Usa EMAIL_FROM si está configurado (debe ser un remitente verificado en Brevo)
msg['From'] = EMAIL_FROM
msg['To'] = TEST_TO
msg['Subject'] = 'Confirma tu cuenta en EduQuiz'

# Mensaje de texto plano
text_body = (
    f"Hola,\n\n"
    f"Gracias por registrarte en EduQuiz. Para completar tu registro introduce el siguiente código de verificación:\n\n"
    f"{verification_code}\n\n"
    f"También puedes verificar tu cuenta haciendo clic en el siguiente enlace:\n{verify_link}\n\n"
    f"Si no solicitaste este correo, ignora este mensaje.\n\n"
    f"Saludos,\nEquipo EduQuiz"
)

# Mensaje HTML (similar al usado por la app)
html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; color: #222;">
        <p>Hola,</p>
        <p>Gracias por registrarte en <strong>EduQuiz</strong>. Para completar tu registro, ingresa el siguiente <strong>código de verificación</strong> en la página de registro:</p>
        <div style="margin:20px 0;">
            <span style="display:inline-block;padding:14px 18px;border-radius:8px;background:#f4f4f4;font-size:20px;letter-spacing:4px">{verification_code}</span>
        </div>
        <p>O pulsa el botón para verificar automáticamente:</p>
        <p><a href="{verify_link}" style="background:#0a58ca;color:#ffffff;padding:12px 20px;border-radius:6px;text-decoration:none;display:inline-block">Verificar mi cuenta</a></p>
        <p style="color:#666;font-size:14px">Si no solicitaste este código, puedes ignorar este correo.</p>
        <hr style="border:none;border-top:1px solid #eee" />
        <p style="font-size:13px;color:#999">EduQuiz — Tu camino al éxito académico</p>
    </body>
</html>
"""

msg.set_content(text_body)
msg.add_alternative(html_body, subtype='html')

print(f"[INFO] Código de verificación generado: {verification_code}")
print(f"[INFO] Enlace de verificación: {verify_link}")

print(f"[DEBUG] Enviando email SMTP -> host={EMAIL_HOST}, port={EMAIL_PORT}, smtp_user={EMAIL_USER}, from_header={from_header}, to={TEST_TO}")

context = ssl.create_default_context()
try:
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=20) as server:
        server.set_debuglevel(1)
        # Permitir desactivar la verificación TLS para pruebas locales mediante .env
        skip_verify = os.getenv('SKIP_TLS_VERIFY', '').lower() in ('1', 'true', 'yes')
        if skip_verify:
            print('[WARN] SKIP_TLS_VERIFY está activado: no se verificará el certificado TLS (solo para pruebas locales).')
            insecure_context = ssl.create_default_context()
            insecure_context.check_hostname = False
            insecure_context.verify_mode = ssl.CERT_NONE
            server.starttls(context=insecure_context)
        else:
            server.starttls(context=context)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
    print('[DEBUG] Email enviado (o al menos enviado al servidor SMTP)')
except Exception as e:
    print('[ERROR] No se pudo enviar el correo:')
    import traceback
    traceback.print_exc()
    print('\nComprueba las variables en .env y las políticas del proveedor SMTP (App Password, bloqueo, etc.).')
