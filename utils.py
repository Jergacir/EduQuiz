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
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    smtp_user = os.environ.get('EMAIL_USER')
    smtp_pass = os.environ.get('EMAIL_PASS')
    from_header = os.environ.get('EMAIL_FROM') or smtp_user

    if not host or not smtp_user or not smtp_pass:
        raise RuntimeError('Configuración SMTP incompleta. Ajusta EMAIL_HOST/EMAIL_USER/EMAIL_PASS')

    try:
        verify_link = url_for('auth.frm_verificar', email=to_email, _external=True)
    except Exception:
        base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        verify_link = f"{base}/verificar?email={to_email}" if base else f"/verificar?email={to_email}"

    msg = EmailMessage()
    msg['From'] = from_header
    msg['To'] = to_email
    msg['Subject'] = 'Confirma tu cuenta en EduQuiz'
    msg.set_content(f"Tu código: {code}\n{verify_link}")
    msg.add_alternative(f"<p>Tu código: <strong>{code}</strong></p><p><a href=\"{verify_link}\">Verificar</a></p>", subtype='html')

    skip_tls = os.environ.get('SKIP_TLS_VERIFY', '0') in ('1', 'true', 'True')
    if skip_tls:
        context = ssl._create_unverified_context()
    else:
        context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
