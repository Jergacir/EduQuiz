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

// Variable que AHORA contendrá los datos REALES (obtenidos del backend)
let listaUsuarios = []; 

let usuarioEditandoId = null; // Para rastrear qué usuario estamos editando

// ... (cargarDatosPerfil, habilitarEdicion, manejarGuardarPerfil permanecen iguales) ...

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
 * Maneja el cambio entre las pestañas de configuración.
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
        obtenerYRenderizarUsuarios(); // <--- LLAMADA CLAVE A LA API
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
        // Reemplazar alert()
        console.error("Todos los campos obligatorios deben estar llenos.");
        return;
    }

    datosUsuarioLogueado.nombre = nuevoNombre;
    datosUsuarioLogueado.username = nuevoUsername;
    datosUsuarioLogueado.correo = nuevoCorreo;
    
    // NOTA: Para guardar el perfil, se necesitaría otra ruta POST/PUT en main.py

    document.getElementById('username').setAttribute('readonly', 'true');
    document.getElementById('correo').setAttribute('readonly', 'true');

    // Reemplazar alert()
    console.log("¡Perfil actualizado con éxito!");
}

/* --- FUNCIONES DE ADMINISTRACIÓN --- */

/**
 * OBTENER DATOS DEL BACKEND y renderizar la tabla.
 */
async function obtenerYRenderizarUsuarios() {
    try {
        const response = await fetch('/api/usuarios'); // Llama a la nueva ruta en main.py
        
        if (response.status === 401) {
             console.error("Error 401: Sesión expirada o no iniciada.");
             return;
        }

        if (response.status === 403) {
            console.error("Error 403: No tiene permisos para acceder a la administración.");
            // Opcional: limpiar la tabla para no mostrar datos
            document.querySelector('#tabla-usuarios tbody').innerHTML = '<tr><td colspan="6">No tienes permisos para ver la administración de usuarios.</td></tr>';
            return;
        }
        
        if (!response.ok) {
            throw new Error(`Error al obtener usuarios: ${response.statusText}`);
        }
        
        // Asignamos la data obtenida del servidor a la variable global
        listaUsuarios = await response.json(); 
        
        renderizarTablaUsuarios(); // Una vez obtenidos los datos, se pinta la tabla

    } catch (error) {
        console.error("Fallo al cargar la lista de usuarios desde la API:", error);
    }
}

/**
 * Renderiza la tabla de usuarios con la lista actual (ahora listaUsuarios viene del backend).
 */
function renderizarTablaUsuarios() {
    const tbody = document.querySelector('#tabla-usuarios tbody');
    tbody.innerHTML = ''; // Limpiar la tabla

    listaUsuarios.forEach(usuario => {
        const fila = tbody.insertRow();
        const tipoMap = { 'E': 'Estudiante', 'P': 'Profesor', 'A': 'Admin', 'G': 'Gestor' };

        fila.insertCell().textContent = usuario.usuario_id;
        fila.insertCell().textContent = usuario.username;
        fila.insertCell().textContent = usuario.nombre;
        fila.insertCell().textContent = usuario.correo;
        fila.insertCell().textContent = tipoMap[usuario.tipo_usuario] || usuario.tipo_usuario;
        fila.insertCell().textContent = usuario.cant_monedas || 0; // Mostrar 0 si no hay monedas

        // Celda de acciones
        const accionesCell = fila.insertCell();
        accionesCell.classList.add('acciones-tabla');

        const btnEditar = document.createElement('button');
        btnEditar.textContent = 'Editar';
        btnEditar.classList.add('btn-editar');
        btnEditar.onclick = () => cargarParaEdicion(usuario.usuario_id);
        
        // --- INICIO: Código del botón Eliminar que preguntaste ---
        const btnEliminar = document.createElement('button');
        btnEliminar.textContent = 'Eliminar';
        btnEliminar.classList.add('btn-eliminar');
        // ¡Esta línea es la clave! Conecta el clic con la función asíncrona que elimina.
        btnEliminar.onclick = () => eliminarUsuario(usuario.usuario_id); 

        accionesCell.appendChild(btnEditar);
        accionesCell.appendChild(btnEliminar);
        // --- FIN: Código del botón Eliminar ---
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
 * Elimina un usuario de la lista haciendo una llamada DELETE a la API del backend.
 * @param {number} id - El ID del usuario a eliminar.
 */
async function eliminarUsuario(id) {
    // 1. CONFIRMACIÓN
    const usernameAEliminar = listaUsuarios.find(u => u.usuario_id === id)?.username || id;
    if (!confirm(`¿Estás seguro de que quieres eliminar al usuario "${usernameAEliminar}" (ID: ${id})? Esta acción es irreversible.`)) {
        return; // El usuario canceló la eliminación
    }

    try {
        // 2. LLAMADA A LA API DELETE
        const response = await fetch(`/api/usuarios/${id}`, {
            method: 'DELETE',
            // No se necesita body en una petición DELETE simple
        });

        const data = await response.json();

        if (response.status === 403 && data.error.includes("propia cuenta")) {
            // Manejar la restricción de auto-eliminación que pusimos en main.py
            alert(data.error); 
            return;
        }

        if (!response.ok) {
            // Si la respuesta no es 2xx, manejar el error devuelto por el backend
            throw new Error(data.error || `Error al eliminar: ${response.status} ${response.statusText}`);
        }

        // 3. ÉXITO: Recargar la tabla para reflejar los cambios
        console.log(`Usuario con ID ${id} eliminado exitosamente.`);
        alert(`¡Usuario ${usernameAEliminar} eliminado con éxito!`);
        
        // La clave para actualizar es volver a obtener los datos del servidor
        await obtenerYRenderizarUsuarios(); 

    } catch (error) {
        console.error("Fallo en la eliminación del usuario:", error);
        alert(`Error al eliminar el usuario: ${error.message}`);
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
    
    // VALIDACIÓN BÁSICA DE CAMPOS OBLIGATORIOS
    if (!nombre || !username || !correo || !tipo_usuario) {
        console.error("Todos los campos de usuario son obligatorios.");
        return;
    }

    // El objeto de datos que se enviaría al backend
    const userData = {
        nombre,
        username,
        correo,
        tipo_usuario,
        contrasena: contrasena || undefined // Solo incluir contraseña si se proporciona
    };

    if (id) {
        // LÓGICA DE ACTUALIZACIÓN (PUT o PATCH)
        console.log(`Simulación: Petición PUT a /api/usuarios/${id}`, userData);
        
        // Simulación: Actualizar la lista local después de una respuesta exitosa
        const usuarioIndex = listaUsuarios.findIndex(u => u.usuario_id == id);
        if (usuarioIndex !== -1) {
            // Actualizar datos locales (solo para simulación)
            listaUsuarios[usuarioIndex] = { ...listaUsuarios[usuarioIndex], ...userData };
            console.log(`Simulación: Usuario ${username} actualizado localmente.`);
        }
    } else {
        // LÓGICA DE CREACIÓN (POST)
        if (!contrasena) {
            console.error("La contraseña es obligatoria para un nuevo usuario.");
            return;
        }
        console.log("Simulación: Petición POST a /api/usuarios", userData);
        
        // Simulación: Agregar a la lista local después de una respuesta exitosa
        const nuevoId = listaUsuarios.length > 0 ? Math.max(...listaUsuarios.map(u => u.usuario_id)) + 1 : 1;
        const nuevoUsuario = {
             usuario_id: nuevoId,
             cant_monedas: 0,
             ...userData
         };
         listaUsuarios.push(nuevoUsuario);
         console.log(`Simulación: Usuario ${username} creado con ID ${nuevoId}.`);
    }

    // Limpiar y ocultar formulario, y actualizar la tabla
    document.getElementById('form-gestion-usuario').reset();
    document.getElementById('form-gestion-usuario').style.display = 'none';
    usuarioEditandoId = null;
    obtenerYRenderizarUsuarios(); // Recargar la lista del backend (o en este caso, renderizar la lista simulada actualizada)
}

// ... (El resto de la inicialización permanece igual) ...

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
        console.log("Cambios de perfil cancelados.");
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
