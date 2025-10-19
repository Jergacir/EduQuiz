"""
Pequeño script para actualizar la contraseña de un usuario en la base de datos desde el entorno de desarrollo.
Uso:
  .venv\Scripts\activate
  python scripts\update_password.py --email usuario@example.com --password NuevaPass123!

El script usa `db.obtenerConexion()` y `extensions.bcrypt` para generar el hash.
"""
import argparse
import os
import sys

# Asegurar que el paquete principal esté en el path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extensions import bcrypt as bcrypt_ext
import db as dbmod

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True, help="Correo del usuario a actualizar")
parser.add_argument("--password", required=True, help="Nueva contraseña en texto plano")
args = parser.parse_args()

email = args.email
password = args.password

# Generar hash usando la misma extensión que la app
try:
    bcrypt_ext.init_app(None)
except Exception:
    # init_app puede requerir app; si falla, asumimos que la función sigue disponible
    pass

try:
    hashed_bytes = bcrypt_ext.generate_password_hash(password)
    hashed = hashed_bytes.decode('utf-8')
except Exception as e:
    print(f"Error generando hash bcrypt: {e}")
    raise

conexion = dbmod.obtenerConexion()
if not conexion:
    print("No se pudo obtener conexión a la base de datos. Revisa db.py y .env")
    sys.exit(1)

try:
    with conexion:
        with conexion.cursor() as cursor:
            sql = "UPDATE usuario SET contrasena=%s WHERE correo=%s"
            cursor.execute(sql, (hashed, email))
            conexion.commit()
            if cursor.rowcount == 0:
                print("No se actualizó ninguna fila. Verifica que el correo exista.")
            else:
                print(f"Contraseña actualizada para {email} (filas afectadas: {cursor.rowcount})")
except Exception as e:
    print(f"Error al actualizar la contraseña: {e}")
    raise
