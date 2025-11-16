"""Minimal bootstrap for EduQuiz.

Initializes the Flask app, extensions, and registers blueprints from
the controllers package. Exposes obtenerConexion and a few simple
decorators used by the controllers.
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from functools import wraps
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecreto123')

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


login_required = _make_login_decorator('auth.frm_login')
gestor_required = _make_login_decorator('auth.frm_login')
profesor_required = _make_login_decorator('auth.frm_login')


def _register_blueprints(app):
    names = ['auth', 'usuarios', 'tienda', 'cuestionarios', 'partidas', 'pages', 'modificarcontrasena', 'apiv1']
    for name in names:
        try:
            # If controllers/<name>.py exists, load it directly (avoids importing a package
            # controllers/<name>/__init__.py which may not contain the full blueprint).
            module_path = os.path.join(os.path.dirname(__file__), 'controllers', f'{name}.py')
            if os.path.isfile(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(f'controllers.{name}_module', module_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            else:
                # Fall back to normal import (package or module)
                mod = __import__(f'controllers.{name}', fromlist=[f'{name}_bp'])
            bp = getattr(mod, f'{name}_bp', None)
            if bp:
                app.register_blueprint(bp)
        except Exception as e:
            print(f"[main] could not register controllers.{name}: {e}", file=sys.stderr)


_init_extensions(app)
_register_blueprints(app)


@app.context_processor
def inject_user_data():
    """Inyecta `logged_in_user` en el contexto de todas las plantillas.

    Devuelve un diccionario con valores por defecto si no hay sesión activa,
    o los datos del usuario si existe una sesión válida. Esto evita
    errores `UndefinedError: 'logged_in_user' is undefined` en plantillas.
    """
    from flask import session as _session
    # Valores por defecto seguros para las plantillas
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
                    return {'logged_in_user': default_user}

                # Normalizar tipos
                if 'vigencia' in row:
                    row['vigencia'] = bool(row.get('vigencia'))
                if 'cant_monedas' in row and row.get('cant_monedas') is None:
                    row['cant_monedas'] = 0

                return {'logged_in_user': row}

    except Exception as e:
        print(f"[main] inject_user_data error: {e}", file=sys.stderr)
        return {'logged_in_user': default_user}

if __name__ == '__main__':
    app.run(debug=True)