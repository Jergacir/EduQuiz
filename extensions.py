from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


def init_app(app):
    """Inicializa extensiones que necesitan la app."""
    bcrypt.init_app(app)
