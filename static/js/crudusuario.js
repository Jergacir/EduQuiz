// Objeto simulado de datos del usuario logueado (EXISTENTE)
const datosUsuarioLogueado = {
    usuario_id: 1, // ID del usuario actual
    username: "joe_developer_chatgpt",
    nombre: "Joe Villarreal Mejia",
    contrasena: "hash_seguro", 
    correo: "DNI@usat.pe",
    tipo_usuario: "A", // Le daremos tipo 'A' (Admin) para tener acceso a la administración.
    cant_monedas: 10000
};

// ARRAY SIMULADO DE TODOS LOS USUARIOS (Tabla USUARIO2)
let listaUsuarios = [
    { usuario_id: 1, username: "joe_developer_chatgpt", nombre: "Joe Villarreal Mejia", contrasena: "1234", correo: "DNI@usat.pe", tipo_usuario: "A", cant_monedas: 10000 },
    { usuario_id: 2, username: "maria_estudiante", nombre: "María Gonzales Perez", contrasena: "5678", correo: "maria@mail.com", tipo_usuario: "E", cant_monedas: 500 },
    { usuario_id: 3, username: "carlos_profe", nombre: "Carlos Salas Ruiz", contrasena: "abcd", correo: "carlos@mail.com", tipo_usuario: "P", cant_monedas: 2500 }
];

let usuarioEditandoId = null; // Para rastrear qué usuario estamos editando

/**
 * Función para cargar los datos del objeto simulado en la interfaz de perfil (EXISTENTE).
 */
function cargarDatosPerfil() {
    document.getElementById('nombre').value = datosUsuarioLogueado.nombre;
    document.getElementById('username').value = datosUsuarioLogueado.username;
    document.getElementById('correo').value = datosUsuarioLogueado.correo;
    document.getElementById('cant_monedas').textContent = datosUsuarioLogueado.cant_monedas;

    // Mapeo del tipo de usuario
    const tipoMap = { 'E': 'Estudiante', 'P': 'Profesor', 'A': 'Administrador' };
    const tipo = tipoMap[datosUsuarioLogueado.tipo_usuario] || 'Desconocido';
    document.getElementById('tipo_usuario').value = tipo;
}

/**
 * Habilita la edición de un campo de entrada (EXISTENTE).
 */
function habilitarEdicion(id) {
    const input = document.getElementById(id);
    if (input) {
        input.removeAttribute('readonly');
        input.focus();
    }
}

/**
 * Maneja el cambio entre las pestañas de configuración (ACTUALIZADO).
 */
function cambiarPestana(event) {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const targetTab = event.currentTarget.getAttribute('data-tab');

    tabButtons.forEach(btn => btn.classList.remove('activo'));
    tabContents.forEach(content => content.classList.remove('activo'));

    event.currentTarget.classList.add('activo');
    document.getElementById(targetTab).classList.add('activo');

    // Cargar la tabla de usuarios cuando se selecciona la pestaña de administración
    if (targetTab === 'administracion') {
        renderizarTablaUsuarios();
    }
}

/**
 * Maneja el envío del formulario de perfil (EXISTENTE).
 */
function manejarGuardarPerfil(event) {
    event.preventDefault();
    // ... (Lógica de guardado de perfil propia) ...
    const nuevoNombre = document.getElementById('nombre').value;
    const nuevoUsername = document.getElementById('username').value;
    const nuevoCorreo = document.getElementById('correo').value;

    if (!nuevoNombre || !nuevoUsername || !nuevoCorreo) {
        alert("Todos los campos obligatorios deben estar llenos.");
        return;
    }

    datosUsuarioLogueado.nombre = nuevoNombre;
    datosUsuarioLogueado.username = nuevoUsername;
    datosUsuarioLogueado.correo = nuevoCorreo;
    
    // Actualizar el usuario en la lista general también
    const index = listaUsuarios.findIndex(u => u.usuario_id === datosUsuarioLogueado.usuario_id);
    if(index !== -1) {
        listaUsuarios[index].nombre = nuevoNombre;
        listaUsuarios[index].username = nuevoUsername;
        listaUsuarios[index].correo = nuevoCorreo;
    }

    document.getElementById('username').setAttribute('readonly', 'true');
    document.getElementById('correo').setAttribute('readonly', 'true');

    alert("¡Perfil actualizado con éxito!");
}

/* --- FUNCIONES DE ADMINISTRACIÓN --- */

/**
 * Renderiza la tabla de usuarios con la lista actual.
 */
function renderizarTablaUsuarios() {
    const tbody = document.querySelector('#tabla-usuarios tbody');
    tbody.innerHTML = ''; // Limpiar la tabla

    listaUsuarios.forEach(usuario => {
        const fila = tbody.insertRow();
        const tipoMap = { 'E': 'Estudiante', 'P': 'Profesor', 'A': 'Admin' };

        fila.insertCell().textContent = usuario.usuario_id;
        fila.insertCell().textContent = usuario.username;
        fila.insertCell().textContent = usuario.nombre;
        fila.insertCell().textContent = usuario.correo;
        fila.insertCell().textContent = tipoMap[usuario.tipo_usuario] || usuario.tipo_usuario;
        fila.insertCell().textContent = usuario.cant_monedas;

        // Celda de acciones
        const accionesCell = fila.insertCell();
        accionesCell.classList.add('acciones-tabla');

        const btnEditar = document.createElement('button');
        btnEditar.textContent = 'Editar';
        btnEditar.classList.add('btn-editar');
        btnEditar.onclick = () => cargarParaEdicion(usuario.usuario_id);
        
        const btnEliminar = document.createElement('button');
        btnEliminar.textContent = 'Eliminar';
        btnEliminar.classList.add('btn-eliminar');
        btnEliminar.onclick = () => eliminarUsuario(usuario.usuario_id);

        accionesCell.appendChild(btnEditar);
        accionesCell.appendChild(btnEliminar);
    });
}

/**
 * Prepara el formulario para editar un usuario existente.
 * @param {number} id - El ID del usuario a editar.
 */
function cargarParaEdicion(id) {
    const usuario = listaUsuarios.find(u => u.usuario_id === id);
    if (!usuario) return;

    usuarioEditandoId = id;
    document.getElementById('form-titulo').textContent = 'Editar';
    document.getElementById('form-gestion-usuario').style.display = 'block';

    document.getElementById('gestion-usuario_id').value = usuario.usuario_id;
    document.getElementById('gestion-nombre').value = usuario.nombre;
    document.getElementById('gestion-username').value = usuario.username;
    document.getElementById('gestion-correo').value = usuario.correo;
    document.getElementById('gestion-tipo_usuario').value = usuario.tipo_usuario;
    document.getElementById('gestion-contrasena').value = ''; // La contraseña se maneja por separado
    
    // Enfocar el formulario
    document.getElementById('form-gestion-usuario').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Elimina un usuario de la lista.
 * @param {number} id - El ID del usuario a eliminar.
 */
function eliminarUsuario(id) {
    if (id === datosUsuarioLogueado.usuario_id) {
        alert("¡No puedes eliminar tu propia cuenta desde esta interfaz!");
        return;
    }
    if (confirm(`¿Estás seguro de que deseas eliminar al usuario con ID ${id}?`)) {
        listaUsuarios = listaUsuarios.filter(u => u.usuario_id !== id);
        renderizarTablaUsuarios();
        alert(`Usuario con ID ${id} eliminado.`);
    }
}

/**
 * Maneja el envío del formulario de creación/edición de usuarios (CRUD).
 */
function manejarGuardarGestion(event) {
    event.preventDefault();

    const id = document.getElementById('gestion-usuario_id').value;
    const nombre = document.getElementById('gestion-nombre').value;
    const username = document.getElementById('gestion-username').value;
    const correo = document.getElementById('gestion-correo').value;
    const tipo_usuario = document.getElementById('gestion-tipo_usuario').value.toUpperCase();
    const contrasena = document.getElementById('gestion-contrasena').value;

    if (id) {
        // LÓGICA DE ACTUALIZACIÓN
        const usuarioIndex = listaUsuarios.findIndex(u => u.usuario_id == id);
        if (usuarioIndex !== -1) {
            listaUsuarios[usuarioIndex].nombre = nombre;
            listaUsuarios[usuarioIndex].username = username;
            listaUsuarios[usuarioIndex].correo = correo;
            listaUsuarios[usuarioIndex].tipo_usuario = tipo_usuario;
            if (contrasena) {
                listaUsuarios[usuarioIndex].contrasena = contrasena; // Simulación de cambio
            }
            alert(`Usuario ${username} actualizado.`);
        }
    } else {
        // LÓGICA DE CREACIÓN
        const nuevoId = listaUsuarios.length > 0 ? Math.max(...listaUsuarios.map(u => u.usuario_id)) + 1 : 1;
        if (!contrasena) {
             alert("La contraseña es obligatoria para un nuevo usuario.");
             return;
        }

        const nuevoUsuario = {
            usuario_id: nuevoId,
            username: username,
            nombre: nombre,
            contrasena: contrasena,
            correo: correo,
            tipo_usuario: tipo_usuario,
            cant_monedas: 0
        };
        listaUsuarios.push(nuevoUsuario);
        alert(`Usuario ${username} creado con ID ${nuevoId}.`);
    }

    // Limpiar y ocultar formulario, y actualizar la tabla
    document.getElementById('form-gestion-usuario').reset();
    document.getElementById('form-gestion-usuario').style.display = 'none';
    usuarioEditandoId = null;
    renderizarTablaUsuarios();
}

/**
 * Inicializa los listeners de eventos al cargar el DOM (ACTUALIZADO).
 */
document.addEventListener('DOMContentLoaded', () => {
    cargarDatosPerfil();
    
    // 1. Listeners para Pestañas
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', cambiarPestana);
    });

    // 2. Listeners para Perfil Propio
    document.getElementById('form-perfil').addEventListener('submit', manejarGuardarPerfil);
    document.getElementById('cancelar').addEventListener('click', () => {
        cargarDatosPerfil();
        document.getElementById('username').setAttribute('readonly', 'true');
        document.getElementById('correo').setAttribute('readonly', 'true');
        alert("Cambios de perfil cancelados.");
    });

    // 3. Listeners para Administración
    const formGestion = document.getElementById('form-gestion-usuario');
    const btnNuevo = document.getElementById('btn-nuevo-usuario');
    const btnCancelarGestion = document.getElementById('btn-cancelar-gestion');

    // Muestra el formulario vacío para crear un nuevo usuario
    btnNuevo.addEventListener('click', () => {
        usuarioEditandoId = null;
        formGestion.reset();
        document.getElementById('form-titulo').textContent = 'Crear';
        formGestion.style.display = 'block';
        document.getElementById('gestion-contrasena').placeholder = "Contraseña obligatoria";
        formGestion.scrollIntoView({ behavior: 'smooth' });
    });

    // Oculta el formulario de gestión
    btnCancelarGestion.addEventListener('click', () => {
        formGestion.reset();
        formGestion.style.display = 'none';
        usuarioEditandoId = null;
    });

    // Maneja la creación/edición al guardar
    formGestion.addEventListener('submit', manejarGuardarGestion);
    
    // Nota: La tabla no se renderiza hasta que se hace clic en la pestaña "Administración"
});