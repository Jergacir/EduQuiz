"""Script de prueba para Gmail API - Ejecutar SOLO en local"""
from test_api_gmail_correo import send_verification_email_gmail_api

# Cambia esto por tu email de prueba
email_destino = input("Ingresa el email de prueba: ")
token_prueba = "TEST123456"

print(f"\n[INFO] Enviando email de prueba a: {email_destino}")
print("[INFO] La primera vez se abrirá el navegador para autorizar la app\n")

try:
    result = send_verification_email_gmail_api(email_destino, token_prueba)
    print(f"\n✅ Email enviado exitosamente!")
    print(f"Message ID: {result['id']}")
    print(f"\nSe generó el archivo 'token.pickle' - súbelo a PythonAnywhere junto con credentials.json")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\nAsegúrate de:")
    print("1. Haber descargado credentials.json de Google Cloud Console")
    print("2. Colocar credentials.json en la carpeta del proyecto")
    print("3. Haber agregado tu email como 'test user' en OAuth consent screen")
