"""Minimal bootstrap for EduQuiz."""

import os
import sys
from dotenv import load_dotenv
from flask import Flask, session, redirect, url_for, flash, request, g
from functools import wraps
from auth_utils import jwt_required, jwt_required_api, verify_jwt_from_cookie, get_user_by_id, refresh_jwt_if_needed

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecreto123')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')

# --- EXTENSIONES Y DB ---
def _init_extensions(app):
    try:
        import extensions
        if hasattr(extensions, 'init_app'): extensions.init_app(app)
        elif hasattr(extensions, 'bcrypt'): 
            try: extensions.bcrypt.init_app(app)
            except: pass
    except: pass

def obtenerConexion():
    try:
        import db as dbmod
        return dbmod.obtenerConexion()
    except Exception as e:
        print(f"[main] could not get DB connection: {e}", file=sys.stderr)
        return None

# --- DECORADORES ---
def _make_login_decorator(redirect_endpoint='auth.frm_login'):
    return jwt_required

login_required = _make_login_decorator('auth.frm_login')
gestor_required = _make_login_decorator('auth.frm_login')
profesor_required = _make_login_decorator('auth.frm_login')
api_required = jwt_required_api

# --- BLUEPRINTS ---
def _register_blueprints(app):
    names = ['auth', 'usuarios', 'tienda', 'cuestionarios', 'partidas', 'pages', 'modificarcontrasena', 'apiv1']
    for name in names:
        try:
            module_path = os.path.join(os.path.dirname(__file__), 'controllers', f'{name}.py')
            if os.path.isfile(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(f'controllers.{name}_module', module_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            else:
                mod = __import__(f'controllers.{name}', fromlist=[f'{name}_bp'])
            bp = getattr(mod, f'{name}_bp', None)
            if bp: app.register_blueprint(bp)
        except Exception as e:
            print(f"[main] could not register controllers.{name}: {e}", file=sys.stderr)

_init_extensions(app)
_register_blueprints(app)

# --- 🔒 SEGURIDAD Y MIDDLEWARE ---

# Rutas que NO requieren login
PUBLIC_ROUTES = {
    'auth.frm_login',
    'auth.frm_registro',
    'auth.procesarlogin',
    'auth.procesarregistro',
    'auth.frm_verificar',
    'auth.procesar_verificacion',
    'auth.reenviar_codigo',
    'auth.get_dni',
    'modificarcontrasena.frm_solicitar_restablecer',
    'modificarcontrasena.solicitar_restablecer',
    'modificarcontrasena.frm_restablecer',
    'modificarcontrasena.restablecer_post',
    'pages.frm_bienvenido',
    'pages.frm_error',
    'static'
}

def require_auth_middleware():
    """
    Middleware principal de seguridad.
    Decide si una petición puede pasar o debe ir al login.
    """
    # 1. Permitir archivos estáticos siempre
    if request.path.startswith('/static/') or request.path == '/favicon.ico':
        return None

    # 2. Permitir rutas públicas explícitas
    if request.endpoint in PUBLIC_ROUTES:
        return None
    
    # Caso especial: Si no hay endpoint (ej. 404), dejar pasar para que Flask maneje el error
    if not request.endpoint:
        return None

    # 3. VERIFICAR SESIÓN (Capa 1 de seguridad)
    if 'user_id' not in session:
        # Intento de acceso no autorizado -> Login
        print(f"⛔ Acceso denegado a {request.path} (Sin sesión)")
        return redirect(url_for('auth.frm_login'))

    # 4. VERIFICAR JWT (Capa 2 de seguridad)
    jwt_payload = verify_jwt_from_cookie()

    # 🔥 LÓGICA CRÍTICA:
    # Si hay sesión ('user_id') pero NO hay JWT (ej. acabas de loguearte),
    # DEJAMOS PASAR la petición.
    # ¿Por qué? Porque `inject_user_data` detectará la falta de JWT
    # y `after_request` inyectará la cookie nueva.
    if not jwt_payload:
        # print("⚠️ Petición con Sesión pero sin JWT. Permitida para regeneración.")
        return None
    
    # Si hay JWT, verificar que coincida con la sesión
    if jwt_payload.get('user_id') != session.get('user_id'):
        print("❌ Robo de sesión detectado: JWT y Sesión no coinciden.")
        session.clear()
        return redirect(url_for('auth.frm_login'))

    # Todo correcto
    return None


def redirect_authenticated_users():
    """Redirige al home si un usuario logueado intenta entrar al login"""
    if request.endpoint in {'auth.frm_login', 'auth.frm_registro', 'pages.frm_bienvenido'}:
        if 'user_id' in session:
            return redirect(url_for('pages.frm_home'))
    return None


@app.before_request
def check_authentication():
    """Se ejecuta antes de cada petición"""
    # No proteger APIs internas por ahora (o usar lógica propia)
    if request.path.startswith("/api_"):
        return None

    # 1. Proteger rutas privadas
    response = require_auth_middleware()
    if response:
        return response

    # 2. Redirigir si ya está logueado e intenta entrar al login
    response = redirect_authenticated_users()
    if response:
        return response


@app.context_processor
def inject_user_data():
    """
    Inyecta datos del usuario y GESTIONA LA CREACIÓN DEL JWT si falta.
    """
    default_user = {'usuario_id': None, 'username': '', 'nombre': '', 'correo': '', 'tipo_usuario': None, 'cant_monedas': 0}

    try:
        if 'user_id' not in session:
            return {'logged_in_user': default_user}

        user_id = session['user_id']
        
        # Obtener datos frescos de la BD
        row = get_user_by_id(user_id)
        
        if not row:
            session.clear()
            return {'logged_in_user': default_user}

        # 🔄 GESTIÓN DE JWT:
        # Si no tiene cookie, o está por vencer, refresh_jwt_if_needed generará uno nuevo.
        new_token = refresh_jwt_if_needed(
            row['usuario_id'],
            row['username'],
            row['tipo_usuario']
        )

        if new_token:
            # Guardamos el token en 'g' para que after_request lo ponga en la cookie
            g.new_jwt_token = new_token

        # Normalización de datos
        if 'vigencia' in row: row['vigencia'] = bool(row.get('vigencia'))
        if row.get('cant_monedas') is None: row['cant_monedas'] = 0

        return {'logged_in_user': row}

    except Exception as e:
        print(f"[main] inject_user_data error: {e}", file=sys.stderr)
        return {'logged_in_user': default_user}


@app.after_request
def refresh_jwt_token(response):
    """Inserta la cookie JWT en la respuesta si se generó una nueva."""
    if hasattr(g, 'new_jwt_token') and g.new_jwt_token:
        response.set_cookie(
            'jwt_token',
            g.new_jwt_token,
            max_age=60*60*24, # 1 día
            httponly=True,    # Importante para seguridad
            secure=False,     # False para desarrollo/PythonAnywhere HTTP, True si tienes HTTPS
            samesite='Lax'
        )
        print("🍪 Cookie JWT inyectada en la respuesta.")
    return response

if __name__ == '__main__':
    app.run(debug=True)