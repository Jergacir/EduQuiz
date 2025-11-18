"""
Utilidades de autenticación con JWT
Combina session de Flask con tokens JWT para mayor seguridad
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from typing import Optional, Dict, Any

# Clave secreta para JWT (debe estar en .env en producción)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24  # Token expira en 24 horas


def generate_jwt_token(user_id: int, username: str, tipo_usuario: str) -> str:
    try:
        payload = {
            'user_id': user_id,
            'username': username,
            'tipo_usuario': tipo_usuario,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        print(f"❌ Error generando JWT: {e}")
        return None


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("⚠️ Token JWT expirado")
        return None
    except jwt.InvalidTokenError as e:
        print(f"⚠️ Token JWT inválido: {e}")
        return None


def verify_jwt_from_cookie() -> Optional[Dict[str, Any]]:
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    return decode_jwt_token(token)


def jwt_required(f):
    """
    Decorador para proteger rutas que requieren autenticación JWT
    ✅ CORREGIDO: Permite el paso si hay sesión pero falta el token (para regenerarlo)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar sesión de Flask (Fundamental)
        if 'user_id' not in session:
            return redirect(url_for('auth.frm_login'))

        # 2. Verificar JWT
        jwt_payload = verify_jwt_from_cookie()

        if not jwt_payload:
            # 🔥 CAMBIO IMPORTANTE:
            # Si hay sesión pero no hay JWT, NO expulsamos al usuario.
            # Asumimos que es un login reciente y dejamos pasar para que
            # el middleware 'after_request' o 'inject_user_data' generen el token.
            # Solo imprimimos advertencia.
            print(f"⚠️ Usuario {session.get('user_id')} tiene sesión pero no JWT. permitiendo acceso para regeneración.")
            return f(*args, **kwargs)

        # 3. Verificar que el user_id coincida
        if jwt_payload.get('user_id') != session.get('user_id'):
            # Aquí sí hay peligro: Token de Usuario A con Sesión de Usuario B
            print("❌ Mismatch: Token no coincide con sesión. Cerrando sesión.")
            session.clear()
            return redirect(url_for('auth.frm_login'))

        return f(*args, **kwargs)

    return decorated_function


def jwt_required_api(f):
    """
    Decorador para API (Retorna JSON).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401

        jwt_payload = verify_jwt_from_cookie()

        # En API somos más estrictos, pero si usas esto en AJAX desde el navegador,
        # podrías necesitar la misma tolerancia que arriba.
        if not jwt_payload:
             # Intento de tolerancia para API también si hay sesión
             print("⚠️ API: Sesión existe, JWT falta. Permitido (asumiendo regeneración próxima)")
             pass
        elif jwt_payload.get('user_id') != session.get('user_id'):
            session.clear()
            return jsonify({'success': False, 'error': 'Token no coincide con sesión'}), 401

        return f(*args, **kwargs)

    return decorated_function


def refresh_jwt_if_needed(user_id: int, username: str, tipo_usuario: str) -> Optional[str]:
    """Renueva el JWT si está próximo a expirar o SI NO EXISTE."""
    jwt_payload = verify_jwt_from_cookie()

    # 🔥 CAMBIO: Si no hay payload (no hay cookie), generamos uno nuevo YA.
    if not jwt_payload:
        print(f"🔄 Generando PRIMER JWT para user_id={user_id}")
        return generate_jwt_token(user_id, username, tipo_usuario)

    # Verificar si falta poco para expirar
    exp_timestamp = jwt_payload.get('exp', 0)
    time_remaining = datetime.fromtimestamp(exp_timestamp) - datetime.utcnow()

    if time_remaining.total_seconds() < 7200:  # 2 horas
        new_token = generate_jwt_token(user_id, username, tipo_usuario)
        print(f"🔄 JWT renovado por expiración para user_id={user_id}")
        return new_token

    return None


def jwt_required_api_enhanced(f):
    """
    Decorador mejorado para proteger endpoints API que requieren JWT
    Acepta JWT desde:
    1. Cookie (jwt_token) - para requests desde el navegador
    2. Header Authorization: Bearer <token> - para Postman/APIs externas

    Retorna JSON en lugar de redireccionar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        jwt_payload = None

        # 1️⃣ Intentar obtener JWT desde Cookie (para navegador)
        token_from_cookie = request.cookies.get('jwt_token')
        if token_from_cookie:
            jwt_payload = decode_jwt_token(token_from_cookie)
            if jwt_payload:
                print(f"✅ JWT válido desde cookie para user_id={jwt_payload.get('user_id')}")

        # 2️⃣ Si no hay cookie, intentar obtener desde Header Authorization (para Postman)
        if not jwt_payload:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('JWT '):
                token_from_header = auth_header.split(' ')[1]
                jwt_payload = decode_jwt_token(token_from_header)
                if jwt_payload:
                    print(f"✅ JWT válido desde header para user_id={jwt_payload.get('user_id')}")

        # 3️⃣ Si no hay JWT válido, denegar acceso
        if not jwt_payload:
            return jsonify({
                'status': 'error',
                'error': 'Authorization Required',
                'description': 'Request does not contain a valid access token',
                'status_code': 401
            }), 401

        # 4️⃣ Verificar que el user_id coincida con la sesión (si existe sesión)
        if 'user_id' in session:
            if jwt_payload.get('user_id') != session.get('user_id'):
                session.clear()
                return jsonify({
                    'status': 'error',
                    'error': 'Token Mismatch',
                    'description': 'JWT token does not match session',
                    'status_code': 401
                }), 401

        # 5️⃣ JWT válido - ejecutar la función
        return f(*args, **kwargs)

    return decorated_function



# ============================================
# UTILIDAD: obtener datos del usuario desde BD
# ============================================

from db import obtenerConexion

def get_user_by_id(user_id: int):
    """
    Obtiene información del usuario desde la base de datos.
    Esta función reemplaza el SELECT que estaba en main.py.
    """
    conexion = obtenerConexion()
    if not conexion:
        print("❌ No hay conexión a la BD en get_user_by_id()")
        return None

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT usuario_id, username, nombre, correo, tipo_usuario,
                       cant_monedas, dni, vigencia
                FROM usuario
                WHERE usuario_id = %s
            """, (user_id,))
            row = cursor.fetchone()
            return row
    except Exception as e:
        print(f"❌ Error al obtener usuario en get_user_by_id(): {e}")
        return None



# En auth_utils.py - AGREGAR ESTA FUNCIÓN

def get_user_from_jwt_or_session():
    from flask import session, request
    if 'user_id' in session:
        return {'user_id': session['user_id'], 'username': session.get('username'), 'tipo_usuario': session.get('tipo_usuario')}

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('JWT '):
        token = auth_header.split(' ')[1]
        jwt_payload = decode_jwt_token(token)
        if jwt_payload: return jwt_payload

    jwt_payload = verify_jwt_from_cookie()
    if jwt_payload: return jwt_payload

    return None





