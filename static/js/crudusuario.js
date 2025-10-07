// Objeto simulado de datos de usuario basado en la tabla USUARIO2
const datosUsuario = {
    usuario_id: 42,
    username: "joe_developer_chatgpt",
    nombre: "Joe Villarreal Mejia",
    contrasena: "hash_seguro", // La contraseña no se muestra
    correo: "DNI@usat.pe",
    tipo_usuario: "E", // 'E' para Estudiante
    cant_monedas: 10000
};

/**
 * Función para cargar los datos del objeto simulado en la interfaz.
 */
function cargarDatosPerfil() {
    document.getElementById('nombre').value = datosUsuario.nombre;
    document.getElementById('username').value = datosUsuario.username;
    document.getElementById('correo').value = datosUsuario.correo;
    document.getElementById('cant_monedas').textContent = datosUsuario.cant_monedas;

    // Lógica simple para mostrar el tipo de usuario (mapeo 'E' -> 'Estudiante')
    const tipo = datosUsuario.tipo_usuario === 'E' ? 'Estudiante' : 'Otro';
    document.getElementById('tipo_usuario').value = tipo;
}

/**
 * Habilita la edición de un campo de entrada.
 * @param {string} id - El ID del campo de entrada a habilitar.
 */
function habilitarEdicion(id) {
    const input = document.getElementById(id);
    if (input) {
        input.removeAttribute('readonly');
        input.focus(); // Coloca el foco en el campo para que el usuario pueda escribir
    }
}

/**
 * Maneja el cambio entre las pestañas de configuración.
 * @param {Event} event - El evento de clic en el botón de la pestaña.
 */
function cambiarPestana(event) {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const targetTab = event.currentTarget.getAttribute('data-tab');

    // Desactivar todas las pestañas y contenidos
    tabButtons.forEach(btn => btn.classList.remove('activo'));
    tabContents.forEach(content => content.classList.remove('activo'));

    // Activar la pestaña y el contenido seleccionados
    event.currentTarget.classList.add('activo');
    document.getElementById(targetTab).classList.add('activo');
}

/**
 * Maneja el envío del formulario de perfil.
 * @param {Event} event - El evento de envío del formulario.
 */
function manejarGuardar(event) {
    event.preventDefault(); // Evita el envío tradicional del formulario (recarga de página)

    // Recoger los datos del formulario
    const nuevoNombre = document.getElementById('nombre').value;
    const nuevoUsername = document.getElementById('username').value;
    const nuevoCorreo = document.getElementById('correo').value;

    // Validación simple
    if (!nuevoNombre || !nuevoUsername || !nuevoCorreo) {
        alert("Todos los campos obligatorios deben estar llenos.");
        return;
    }

    // SIMULACIÓN de envío de datos al servidor
    console.log("Datos a enviar al servidor (simulado):", {
        nombre: nuevoNombre,
        username: nuevoUsername,
        correo: nuevoCorreo
        // En una aplicación real, aquí se enviarían vía AJAX/Fetch
    });

    // Actualizar los datos simulados y deshabilitar la edición
    datosUsuario.nombre = nuevoNombre;
    datosUsuario.username = nuevoUsername;
    datosUsuario.correo = nuevoCorreo;
    document.getElementById('username').setAttribute('readonly', 'true');
    document.getElementById('correo').setAttribute('readonly', 'true');

    alert("¡Perfil actualizado con éxito!");
}

/**
 * Inicializa los listeners de eventos al cargar el DOM.
 */
document.addEventListener('DOMContentLoaded', () => {
    cargarDatosPerfil();

    // Event listeners para el cambio de pestañas
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', cambiarPestana);
    });

    // Event listener para el formulario de guardado
    document.getElementById('form-perfil').addEventListener('submit', manejarGuardar);
    
    // Event listener para el botón "Cancelar"
    document.getElementById('cancelar').addEventListener('click', () => {
        // Recargar los datos originales y deshabilitar la edición
        cargarDatosPerfil();
        document.getElementById('username').setAttribute('readonly', 'true');
        document.getElementById('correo').setAttribute('readonly', 'true');
        alert("Cambios cancelados.");
    });
});