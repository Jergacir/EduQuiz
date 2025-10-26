from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import os
import pickle

# Scopes necesarios para enviar emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Obtiene el servicio de Gmail autenticado"""
    creds = None
    
    # El token se guarda en token.pickle después del primer login
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay credenciales válidas, hacer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar credenciales para la próxima vez
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def send_verification_email_gmail_api(to_email, token):
    """Envía email usando Gmail API"""
    
    # Para desarrollo local usa localhost:5000, para producción usa tu dominio de PythonAnywhere
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    verification_link = f"{base_url}/auth/verificar?token={token}"
    
    message = MIMEText(f"""
    <html>
    <body>
        <h2>Bienvenido a EduQuiz</h2>
        <p>Haz clic en el siguiente enlace para verificar tu cuenta:</p>
        <a href="{verification_link}">Verificar mi cuenta</a>
    </body>
    </html>
    """, 'html')
    
    message['to'] = to_email
    message['subject'] = 'Verifica tu cuenta - EduQuiz'
    
    # Codificar el mensaje
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    try:
        service = get_gmail_service()
        send_message = service.users().messages().send(
            userId="me", 
            body={'raw': raw}
        ).execute()
        
        print(f"[GMAIL API] Email enviado: {send_message['id']}")
        return send_message
    except Exception as e:
        print(f"[GMAIL API ERROR] {str(e)}")
        raise