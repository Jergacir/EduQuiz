from flask import Blueprint, render_template, redirect, url_for, session, flash
import db as dbmod

pages_bp = Blueprint('pages', __name__, template_folder='../../templates')


@pages_bp.route('/')
def frm_bienvenido():
    return render_template('bienvenido.html')


@pages_bp.route('/home')
def frm_home():
    # Obtener usuario logueado (si existe) para la plantilla
    logged = {}
    conexion = dbmod.obtenerConexion()
    public_quizzes = []
    popular_quizzes = []
    community_quizzes = []
    try:
        if conexion:
            if 'user_id' in session:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT usuario_id, username, nombre, cant_monedas, tipo_usuario, COALESCE(url_foto_perfil,'') AS url_foto_perfil, COALESCE(url_avatar,'') AS url_avatar FROM usuario WHERE usuario_id=%s", (session['user_id'],))
                    row = cursor.fetchone()
                    logged = row or {}

            # Obtener cuestionarios públicos (mostrar en home)
            # 1) Top 8 más populares (más clonados)
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT c.cuestionario_id, c.nombre_cuestionario, c.descripcion, c.url_img_cuestionario, c.usuario_id,
                           u.username as username_quiz, c.publico,
                           (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas,
                           (SELECT COUNT(*) FROM cuestionario ch WHERE ch.origen_cuestionario_id = c.cuestionario_id AND ch.estado = 1) AS num_clones
                    FROM cuestionario c INNER JOIN usuario u ON c.usuario_id=u.usuario_id
                    WHERE c.publico = 1 AND c.estado = 1
                    ORDER BY num_clones DESC, c.cuestionario_id DESC
                    LIMIT 8
                """)
                popular_quizzes = cursor.fetchall() or []

            # 2) Resto de cuestionarios públicos (excluir los que ya salen en populares)
            with conexion.cursor() as cursor:
                if popular_quizzes:
                    ids = ','.join(str(r['cuestionario_id']) for r in popular_quizzes)
                    # Usamos NOT IN para excluir los populares
                    sql = f"""
                        SELECT c.cuestionario_id, c.nombre_cuestionario, c.descripcion, c.url_img_cuestionario, c.usuario_id,
                               u.username as username_quiz, c.publico,
                               (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas,
                               (SELECT COUNT(*) FROM cuestionario ch WHERE ch.origen_cuestionario_id = c.cuestionario_id AND ch.estado = 1) AS num_clones
                        FROM cuestionario c INNER JOIN usuario u ON c.usuario_id=u.usuario_id
                        WHERE c.publico = 1 AND c.estado = 1 AND c.cuestionario_id NOT IN ({ids})
                        ORDER BY c.cuestionario_id DESC
                        LIMIT 100
                    """
                    cursor.execute(sql)
                else:
                    cursor.execute("""
                        SELECT c.cuestionario_id, c.nombre_cuestionario, c.descripcion, c.url_img_cuestionario, c.usuario_id,
                               u.username as username_quiz, c.publico,
                               (SELECT COUNT(*) FROM pregunta p WHERE p.cuestionario_id = c.cuestionario_id) AS num_preguntas,
                               (SELECT COUNT(*) FROM cuestionario ch WHERE ch.origen_cuestionario_id = c.cuestionario_id AND ch.estado = 1) AS num_clones
                        FROM cuestionario c INNER JOIN USUARIO u ON c.usuario_id=u.usuario_id
                        WHERE c.publico = 1 AND c.estado = 1
                        ORDER BY c.cuestionario_id DESC
                        LIMIT 100
                    """)
                community_quizzes = cursor.fetchall() or []
    except Exception as e:
        print(f"Error cargando home data: {e}")

    return render_template('home.html', logged_in_user=logged,
                           popular_quizzes=popular_quizzes,
                           community_quizzes=community_quizzes)


@pages_bp.route('/probarconexion')
def probarconexion():
    from main import obtenerConexion
    connection = obtenerConexion()
    if connection is None:
        return "<p>Error al conectar a la base de datos</p>"
    else:
        return "<p>Conexión exitosa</p>"


@pages_bp.route('/errorsistema')
def frm_error():
    return render_template('errorsistema.html')


@pages_bp.route('/editar_cuestionario/<int:cuestionario_id>')
def frm_edicioncuestionario(cuestionario_id):
    return render_template('editarcuestionario.html', cuestionario_id=cuestionario_id)


@pages_bp.route('/ver_cuestionario/<int:cuestionario_id>')
def frm_ver_cuestionario(cuestionario_id):
    return render_template('visualizarCuestionario.html', cuestionario_id=cuestionario_id)
