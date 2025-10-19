from flask import Blueprint, render_template, redirect, url_for, request, flash

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

@auth_bp.route('/login')
def frm_login():
    return render_template('login.html')

@auth_bp.route('/registro')
def frm_registro():
    return render_template('registro.html')

@auth_bp.route('/logout')
def logout():
    # Esta es una versión de placeholder; la lógica real vive en main.py hasta migrarla
    flash('Sesión cerrada (placeholder).', 'success')
    return redirect(url_for('auth.frm_login'))
