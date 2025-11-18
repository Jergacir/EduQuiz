"""Minimal bootstrap for EduQuiz.

Initializes the Flask app, extensions, and registers blueprints from
the controllers package. Exposes obtenerConexion and a few simple
decorators used by the controllers.
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask, session, redirect, url_for, flash
from functools import wraps
from auth_utils import jwt_required, jwt_required_api
from flask import request, redirect, url_for, session
from auth_utils import verify_jwt_from_cookie
# ✨ IMPORTAR UTILIDADES JWT
from auth_utils import jwt_required, jwt_required_api

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecreto123')

# ✨ CONFIGURACIÓN JWT (añadir al .env)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')

def _init_extensions(app):
    try:
        import extensions
        if hasattr(extensions, 'init_app'):
            extensions.init_app(app)
        elif hasattr(extensions, 'bcrypt'):
            try:
                extensions.bcrypt.init_app(app)
            except Exception:
                pass
    except Exception:
        pass


def obtenerConexion():
    try:
        import db as dbmod
        return dbmod.obtenerConexion()
    except Exception as e:
        print(f"[main] could not get DB connection: {e}", file=sys.stderr)
        return None

def _make_login_decorator(redirect_endpoint='auth.frm_login'):
    """Usa jwt_required en lugar de solo verificar sesión"""
    return jwt_required

"""
def _make_login_decorator(redirect_endpoint='auth.frm_login'):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from flask import session, redirect, url_for, flash
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for(redirect_endpoint))
            return f(*args, **kwargs)

        return wrapped

    return decorator
"""

login_required = _make_login_decorator('auth.frm_login')
gestor_required = _make_login_decorator('auth.frm_login')
profesor_required = _make_login_decorator('auth.frm_login')

# ✨ NUEVO: Decorador específico para APIs
api_required = jwt_required_api


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
            if bp:
                app.register_blueprint(bp)
        except Exception as e:
            print(f"[main] could not register controllers.{name}: {e}", file=sys.stderr)



_init_extensions(app)
_register_blueprints(app)


# 🔒 RUTAS PÚBLICAS (accesibles sin login)
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
    'static',  # Archivos estáticos (CSS, JS, imágenes)
}

# 🔒 PREFIJOS DE RUTAS PÚBLICAS
PUBLIC_PREFIXES = (
    '/static/',
    '/favicon.ico',
)


def require_auth_middleware():
    """
    Middleware que protege TODAS las rutas excepto las públicas.
    Verificar sesión + JWT antes de permitir acceso.
    """

    # 1. Permitir rutas públicas
    if request.endpoint in PUBLIC_ROUTES:
        return None

    # 2. Permitir prefijos públicos
    if request.path.startswith(PUBLIC_PREFIXES):
        return None

    # 3. Verificar sesión
    if 'user_id' not in session:
        print(f"🚫 Acceso bloqueado a {request.path} - No hay sesión")
        return redirect(url_for('auth.frm_login'))

    # 4. Verificar JWT
    jwt_payload = verify_jwt_from_cookie()

    if not jwt_payload:
        print(f"🚫 Acceso bloqueado a {request.path} - JWT inválido/expirado")
        session.clear()
        return redirect(url_for('auth.frm_login'))

    # 5. Verificar que user_id coincida
    if jwt_payload.get('user_id') != session.get('user_id'):
        print(f"🚫 Acceso bloqueado a {request.path} - JWT no coincide con sesión")
        session.clear()
        return redirect(url_for('auth.frm_login'))

    # ✅ Todo correcto, permitir acceso
    return None



@app.context_processor
def inject_user_data():
    """Inyecta `logged_in_user` en el contexto de todas las plantillas."""
    from flask import session as _session
    from auth_utils import verify_jwt_from_cookie, refresh_jwt_if_needed

    default_user = {
        'usuario_id': None,
        'username': '',
        'nombre': '',
        'correo': '',
        'tipo_usuario': None,
        'cant_monedas': 0,
        'dni': '',
        'vigencia': False,
    }

    try:
        if 'user_id' not in _session:
            return {'logged_in_user': default_user}

        # ✨ VERIFICAR JWT
        jwt_payload = verify_jwt_from_cookie()

        if not jwt_payload or jwt_payload.get('user_id') != _session.get('user_id'):
            # JWT inválido - limpiar sesión
            _session.clear()
            return {'logged_in_user': default_user}

        user_id = _session['user_id']
        conexion = obtenerConexion()
        if not conexion:
            return {'logged_in_user': default_user}

        with conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT usuario_id, username, nombre, correo, tipo_usuario, cant_monedas, dni, vigencia FROM usuario WHERE usuario_id=%s"
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
                if not row:
                    _session.clear()
                    return {'logged_in_user': default_user}

                if 'vigencia' in row:
                    row['vigencia'] = bool(row.get('vigencia'))
                if 'cant_monedas' in row and row.get('cant_monedas') is None:
                    row['cant_monedas'] = 0

                # ✨ RENOVAR JWT SI ES NECESARIO
                new_token = refresh_jwt_if_needed(
                    row['usuario_id'],
                    row['username'],
                    row['tipo_usuario']
                )

                # Si se renovó el token, se actualizará en la próxima respuesta
                if new_token:
                    from flask import g
                    g.new_jwt_token = new_token

                return {'logged_in_user': row}

    except Exception as e:
        print(f"[main] inject_user_data error: {e}", file=sys.stderr)
        return {'logged_in_user': default_user}


# ============================================
# 🔒 MIDDLEWARE DE AUTENTICACIÓN GLOBAL
# ============================================

# from auth_middleware import require_auth_middleware, redirect_authenticated_users

@app.before_request
def check_authentication():
    """
    Se ejecuta ANTES de cada request.
    Protege TODAS las rutas automáticamente.
    """

    # 1. Redirigir usuarios autenticados que van a login/registro
    response = redirect_authenticated_users()
    if response:
        return response

    # 2. Bloquear acceso a rutas protegidas sin autenticación
    response = require_auth_middleware()
    if response:
        return response

    # Si no hay response, la petición continúa normalmente
    return None


# ✨ MIDDLEWARE PARA RENOVAR JWT AUTOMÁTICAMENTE
@app.after_request
def refresh_jwt_token(response):
    """Renueva el JWT en la respuesta si fue generado en inject_user_data"""
    from flask import g

    if hasattr(g, 'new_jwt_token') and g.new_jwt_token:
        response.set_cookie(
            'jwt_token',
            g.new_jwt_token,
            max_age=60*60*24*30,
            httponly=True,
            secure=False,  # Cambiar a True en producción
            samesite='Lax'
        )
        print("🔄 JWT renovado automáticamente en la respuesta")

    return response



def redirect_authenticated_users():
    """
    Middleware que redirige usuarios YA autenticados que intentan acceder a login/registro.
    """

    # Solo aplicar a rutas de autenticación
    if request.endpoint not in {'auth.frm_login', 'auth.frm_registro', 'pages.frm_bienvenido'}:
        return None

    # Verificar si ya está autenticado
    if 'user_id' in session:
        jwt_payload = verify_jwt_from_cookie()

        if jwt_payload and jwt_payload.get('user_id') == session.get('user_id'):
            print(f"✅ Usuario autenticado intentando acceder a {request.endpoint}, redirigiendo a home")
            return redirect(url_for('pages.frm_home'))
        else:
            # JWT inválido - limpiar sesión
            session.clear()

    return None



if __name__ == '__main__':
    app.run(debug=True)