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
    """
    Genera un token JWT para el usuario
    
    Args:
        user_id: ID del usuario
        username: Nombre de usuario
        tipo_usuario: Tipo de usuario (A, P, G)
    
    Returns:
        Token JWT como string
    """
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
    """
    Decodifica y valida un token JWT
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Diccionario con los datos del payload o None si es inválido
    """
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
    """
    Verifica el token JWT desde las cookies
    
    Returns:
        Payload del token si es válido, None en caso contrario
    """
    token = request.cookies.get('jwt_token')
    
    if not token:
        return None
    
    return decode_jwt_token(token)


def jwt_required(f):
    """
    Decorador para proteger rutas que requieren autenticación JWT
    Verifica tanto la sesión como el JWT
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero verificar sesión de Flask (más rápido)
        if 'user_id' not in session:
            return redirect(url_for('auth.frm_login'))
        
        # Luego verificar JWT (más seguro)
        jwt_payload = verify_jwt_from_cookie()
        
        if not jwt_payload:
            # JWT inválido o expirado - cerrar sesión
            session.clear()
            return redirect(url_for('auth.frm_login'))
        
        # Verificar que el user_id coincida
        if jwt_payload.get('user_id') != session.get('user_id'):
            session.clear()
            return redirect(url_for('auth.frm_login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def jwt_required_api(f):
    """
    Decorador para proteger endpoints API que requieren JWT
    Retorna JSON en lugar de redireccionar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar sesión
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401
        
        # Verificar JWT
        jwt_payload = verify_jwt_from_cookie()
        
        if not jwt_payload:
            session.clear()
            return jsonify({'success': False, 'error': 'Token inválido o expirado'}), 401
        
        # Verificar coincidencia
        if jwt_payload.get('user_id') != session.get('user_id'):
            session.clear()
            return jsonify({'success': False, 'error': 'Token no coincide con sesión'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def refresh_jwt_if_needed(user_id: int, username: str, tipo_usuario: str) -> Optional[str]:
    """
    Renueva el JWT si está próximo a expirar (menos de 2 horas restantes)
    
    Returns:
        Nuevo token si fue renovado, None si no es necesario
    """
    jwt_payload = verify_jwt_from_cookie()
    
    if not jwt_payload:
        return None
    
    # Verificar si falta poco para expirar
    exp_timestamp = jwt_payload.get('exp', 0)
    time_remaining = datetime.fromtimestamp(exp_timestamp) - datetime.utcnow()
    
    # Si quedan menos de 2 horas, renovar
    if time_remaining.total_seconds() < 7200:  # 2 horas
        new_token = generate_jwt_token(user_id, username, tipo_usuario)
        print(f"🔄 JWT renovado para user_id={user_id}")
        return new_token
    
    return None