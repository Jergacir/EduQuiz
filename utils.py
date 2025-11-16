import os
import smtplib
import ssl
from email.message import EmailMessage
from flask import url_for
import sys
import hashlib
import secrets
import traceback # Importar traceback para el manejo de errores


# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from email.mime.text import MIMEText
    import base64
    import pickle
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    print("[WARNING] Gmail API libraries not installed. Falling back to SMTP.")


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


# ============ GMAIL API FUNCTIONS ============
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Obtiene el servicio de Gmail autenticado usando token.pickle"""
    creds = None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base_dir, 'token.pickle')
    cred_path = os.path.join(base_dir, 'credentials.json')

    print(f"[DEBUG] get_gmail_service cwd={os.getcwd()} base_dir={base_dir}")
    print(f"[DEBUG] looking for token: {token_path} exists={os.path.exists(token_path)}")
    print(f"[DEBUG] looking for credentials: {cred_path} exists={os.path.exists(cred_path)}")

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not getattr(creds, 'valid', False):
        if creds and getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
            creds.refresh(Request())
        else:
            if os.path.exists(cred_path):
                credentials_file = cred_path
            elif os.path.exists('credentials.json'):
                credentials_file = os.path.abspath('credentials.json')
            else:
                raise FileNotFoundError(
                    f"credentials.json not found. Checked: {cred_path} and {os.path.abspath('credentials.json')}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        try:
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"[WARNING] No se pudo escribir token.pickle en {token_path}: {e}")

    return build('gmail', 'v1', credentials=creds)


def send_email_via_gmail_api(to_email: str, subject: str, html_body: str):
    """Envía email usando Gmail API"""
    if not GMAIL_API_AVAILABLE:
        raise RuntimeError("Gmail API libraries not installed")

    message = MIMEText(html_body, 'html')
    message['to'] = to_email
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service = get_gmail_service()
        send_message = service.users().messages().send(
            userId="me",
            body={'raw': raw}
        ).execute()

        print(f"[GMAIL API] Email enviado exitosamente a {to_email}, Message ID: {send_message['id']}")
        return send_message
    except Exception as e:
        print(f"[GMAIL API ERROR] {str(e)}")
        raise


def send_verification_email(to_email: str, code: str):
    """Envía un correo con el código de verificación."""
    use_gmail_api = os.environ.get('USE_GMAIL_API', 'true').strip().lower() in ('1', 'true', 'yes', 'on')

    module_dir = os.path.dirname(os.path.abspath(__file__))
    token_paths = [os.path.join(module_dir, 'token.pickle'), os.path.abspath('token.pickle')]
    token_exists = any(os.path.exists(p) for p in token_paths)

    print(f"[DEBUG] send_verification_email use_gmail_api={use_gmail_api} GMAIL_API_AVAILABLE={GMAIL_API_AVAILABLE} token_exists={token_exists}")

    if use_gmail_api and GMAIL_API_AVAILABLE and token_exists:
        return _send_verification_email_via_gmail_api(to_email, code)
    else:
        return _send_verification_email_via_smtp(to_email, code)


def _send_verification_email_via_gmail_api(to_email: str, code: str):
    """Envía email de verificación usando Gmail API"""
    try:
        verify_link = url_for('frm_verificar', email=to_email, _external=True)
    except Exception:
        base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        verify_link = f"{base}/verificar?email={to_email}" if base else f"/verificar?email={to_email}"

    subject = 'Confirma tu cuenta en EduQuiz'

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

    print(f"[DEBUG] Enviando email via Gmail API a {to_email}")
    return send_email_via_gmail_api(to_email, subject, html_body)


# ============================================
# HASH DE CONTRASEÑAS CON SHA-256
# ============================================

def hash_password_sha256(password: str, salt: str = None) -> tuple:
    """
    Hashea una contraseña usando SHA-256 con salt.
    Formato: salt$hash
    """
    if salt is None:
        # **CORRECCIÓN 1:** Usar 16 bytes (32 caracteres hex) para el salt.
        # Esto asegura que el hash total (32 + 1 + 64 = 97)
        # quepa en un VARCHAR(100) y evita el truncamiento.
        salt = secrets.token_hex(16)

    salted_password = salt + password
    hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
    password_hash = hash_obj.hexdigest() # 64 caracteres

    # Total: 32 (salt) + 1 ($) + 64 (hash) = 97 caracteres.
    hash_completo = f"{salt}${password_hash}"

    return hash_completo, salt


def verify_password_sha256(password: str, stored_hash: str) -> bool:
    """
    **CORRECCIÓN 2:** Lógica de verificación robustecida.
    Verifica si una contraseña coincide con el hash almacenado.
    Versión flexible: Acepta salt$hash (normal o truncado) O hash$salt
    """
    try:
        if not stored_hash or '$' not in stored_hash:
            print(f"⚠️ Hash inválido: no contiene '$'")
            return False

        parts = stored_hash.split('$', 1)
        if len(parts) != 2:
            print(f"⚠️ Hash inválido: formato incorrecto (partes: {len(parts)})")
            return False

        part1, part2 = parts

        print(f"🔍 verify_password_sha256:")
        print(f"   Part1 length: {len(part1)}")
        print(f"   Part2 length: {len(part2)}")

        # El hash SHA-256 (hexdigest) SIEMPRE tiene 64 caracteres.

        if len(part2) == 64:
            # Caso 1: salt(X)$hash(64). Formato estándar (nuevo o antiguo).
            # (Esto funcionará para los nuevos hashes de 97 caracteres)
            print(f"   ⚙️ Formato detectado: salt$hash (hash completo en part2)")
            salt = part1
            stored_password_hash = part2

            salted_password = salt + password
            hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
            password_hash = hash_obj.hexdigest()

            resultado = secrets.compare_digest(password_hash, stored_password_hash)

            if not resultado:
                print(f"❌ Verificación fallida (salt$hash):")
                print(f"   Hash esperado:  {stored_password_hash[:20]}...")
                print(f"   Hash calculado: {password_hash[:20]}...")
            else:
                print(f"✅ Verificación exitosa (salt$hash)")
            return resultado

        elif len(part1) == 64:
            # Caso 2: Ambigüedad.
            # - Podría ser hash(64)$salt(X) (formato invertido).
            # - Podría ser salt(64)$hash(X) (formato correcto, pero hash truncado - TU CASO)
            print(f"   ⚠️ Ambigüedad detectada (part1=64). Verificando ambos formatos...")

            # Prueba 1: Asumir formato salt$hash (salt=part1, hash=part2)
            # (Este es el caso de tu log: salt(64)$hash(35))
            salt_1 = part1
            stored_hash_1 = part2 # Hash truncado
            print(f"      Prueba 1 (salt$hash truncado): salt={salt_1[:10]}... hash_fragment={stored_hash_1[:10]}... (len={len(stored_hash_1)})")

            salted_password_1 = salt_1 + password
            hash_obj_1 = hashlib.sha256(salted_password_1.encode('utf-8'))
            password_hash_1 = hash_obj_1.hexdigest() # Hash completo (64)

            # Comparamos el hash calculado completo contra el fragmento truncado
            if secrets.compare_digest(password_hash_1[:len(stored_hash_1)], stored_hash_1):
                print(f"   ✅ Verificación exitosa (Prueba 1: salt$hash truncado)")
                print(f"      Hash calculado: {password_hash_1[:20]}...")
                print(f"      Hash esperado (trunc): {stored_hash_1[:20]}...")
                return True
            else:
                print(f"      Prueba 1 fallida. Calculado (trunc): {password_hash_1[:len(stored_hash_1)]}")


            # Prueba 2: Asumir formato hash$salt (hash=part1, salt=part2)
            # (Esto es lo que tu código anterior intentó hacer y falló)
            salt_2 = part2
            stored_hash_2 = part1 # Hash completo
            print(f"      Prueba 2 (hash$salt): salt={salt_2[:10]}... (len={len(salt_2)}) hash_completo={stored_hash_2[:10]}...")

            salted_password_2 = salt_2 + password
            hash_obj_2 = hashlib.sha256(salted_password_2.encode('utf-8'))
            password_hash_2 = hash_obj_2.hexdigest() # Hash completo (64)

            resultado_2 = secrets.compare_digest(password_hash_2, stored_hash_2)

            if resultado_2:
                 print(f"   ✅ Verificación exitosa (Prueba 2: hash$salt)")
            else:
                print(f"❌ Verificación fallida (Ambas pruebas):")
                print(f"   (Prueba 2) Esperado: {stored_hash_2[:20]}... | Calculado: {password_hash_2[:20]}...")

            return resultado_2

        else:
            # Caso 3: Ninguna parte tiene 64.
            # Probablemente un hash muy antiguo o muy truncado.
            # Asumir salt$hash por defecto (el más probable).
            print(f"   ⚠️ Ninguna parte tiene 64 caracteres. Asumiendo salt$hash por defecto.")
            salt = part1
            stored_password_hash_fragment = part2

            salted_password = salt + password
            hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
            password_hash = hash_obj.hexdigest()

            # Comparar con truncamiento
            resultado = secrets.compare_digest(password_hash[:len(stored_password_hash_fragment)], stored_password_hash_fragment)

            if not resultado:
                print(f"❌ Verificación fallida (defecto):")
                print(f"   Hash esperado (trunc): {stored_password_hash_fragment[:20]}...")
                print(f"   Hash calculado (trunc): {password_hash[:len(stored_password_hash_fragment)]}...")

            return resultado

    except Exception as e:
        print(f"❌ Error en verify_password_sha256: {e}")
        traceback.print_exc()
        return False


def _send_verification_email_via_smtp(to_email: str, code: str):
    """Envía email de verificación usando SMTP tradicional"""
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    smtp_user = os.environ.get('EMAIL_USER')
    smtp_pass = os.environ.get('EMAIL_PASS')
    from_header = os.environ.get('EMAIL_FROM') or smtp_user

    if not host or not smtp_user or not smtp_pass:
        raise RuntimeError('Configuración SMTP incompleta. Ajusta EMAIL_HOST/EMAIL_USER/EMAIL_PASS')

    subject = 'Confirma tu cuenta en EduQuiz'

    try:
        verify_link = url_for('frm_verificar', email=to_email, _external=True)
    except Exception:
        base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        verify_link = f"{base}/verificar?email={to_email}" if base else f"/verificar?email={to_email}"

    text_body = (
        f"Hola,\n\n"
        f"Gracias por registrarte en EduQuiz. Para completar tu registro introduce el siguiente código de verificación:\n\n"
        f"{code}\n\n"
        f"También puedes verificar tu cuenta haciendo clic en el siguiente enlace:\n{verify_link}\n\n"
        f"Si no solicitaste este correo, ignora este mensaje.\n\n"
        f"Saludos,\nEquipo EduQuiz"
    )

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

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.set_debuglevel(1)
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print("[DEBUG] Email enviado exitosamente via SMTP")
    except Exception as e:
        traceback.print_exc()
        raise