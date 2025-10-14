// Variable que contendrá los datos del usuario logueado (obtenidos del backend)
let datosUsuarioLogueado = {}; 

// Variable que contendrá los datos REALES (obtenidos del backend) para la administración
let listaUsuarios = []; 

let usuarioEditandoId = null; // Para rastrear qué usuario estamos editando

/**
 * [NUEVA FUNCIÓN] Obtiene los datos del perfil del usuario logueado de la API.
 */
async function obtenerDatosPerfil() {
    try {
        const response = await fetch('/api/perfil'); // Llama a la ruta para el perfil actual
        
        if (response.status === 401) {
            console.error("Error 401: Sesión expirada o no iniciada.");
            return null;
        }

        if (!response.ok) {
            throw new Error(`Error al obtener el perfil: ${response.statusText}`);
        }
        
        datosUsuarioLogueado = await response.json(); 
        return datosUsuarioLogueado;

    } catch (error) {
        console.error("Fallo al cargar los datos del perfil desde la API:", error);
        return null;
    }
}


/**
 * Función para cargar los datos del objeto REAL en la interfaz de perfil.
 */
async function cargarDatosPerfil() {
    // Si los datos no se han cargado aún, intentamos obtenerlos
    if (Object.keys(datosUsuarioLogueado).length === 0) {
        await obtenerDatosPerfil();
    }
    
    // Verificamos si la carga fue exitosa
    if (datosUsuarioLogueado && datosUsuarioLogueado.usuario_id) {
        document.getElementById('nombre').value = datosUsuarioLogueado.nombre || '';
        document.getElementById('username').value = datosUsuarioLogueado.username || '';
        document.getElementById('correo').value = datosUsuarioLogueado.correo || '';
        document.getElementById('cant_monedas').textContent = datosUsuarioLogueado.cant_monedas || 0;

        // Mapeo del tipo de usuario
        const tipoMap = { 'A': 'Alumno', 'P': 'Profesor', 'G': 'Gestor' }; 
        const tipo = tipoMap[datosUsuarioLogueado.tipo_usuario] || 'Desconocido';
        // Asumiendo que 'tipo_usuario' en el perfil SIEMPRE debe ser readonly/deshabilitado.
        const tipoUsuarioInput = document.getElementById('tipo_usuario');
        tipoUsuarioInput.value = tipo;
        tipoUsuarioInput.setAttribute('readonly', true); // Aseguramos que sea readonly
        tipoUsuarioInput.classList.add('input-no-editable'); // Añadimos clase para opacidad
    } else {
        console.error("No se pudieron cargar los datos del usuario logueado.");
        // Opcional: Mostrar mensaje al usuario
    }
}

/**
 * Habilita la edición de un campo de entrada.
 */
function habilitarEdicion(id) {
    const input = document.getElementById(id);
    if (input) {
        input.removeAttribute('readonly');
        input.classList.remove('input-no-editable'); // Quitar opacidad al habilitar
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

    // Ocultar formulario de gestión al cambiar de pestaña
    document.getElementById('form-gestion-usuario').style.display = 'none';
    usuarioEditandoId = null;

    // Cargar la tabla de usuarios cuando se selecciona la pestaña de administración
    if (targetTab === 'administracion') {
        obtenerYRenderizarUsuarios(); // <--- LLAMADA CLAVE A LA API
    }
    
    // Recargar perfil si volvemos a la pestaña de perfil
    if (targetTab === 'perfil') {
        cargarDatosPerfil();
    }
}

/**
 * Maneja el envío del formulario de perfil (Actualización vía API).
 * NOTA: Aquí asumimos que los campos de contraseña están en la pestaña "contrasena" y no en "perfil".
 */
async function manejarGuardarPerfil(event) {
    event.preventDefault();
    const nuevoNombre = document.getElementById('nombre').value;
    const nuevoUsername = document.getElementById('username').value;
    const nuevoCorreo = document.getElementById('correo').value;
    
    // Se elimina la lógica de contraseñas de esta función, asumiendo que solo está en la pestaña "contrasena"
    const contrasenaActual = ''; 
    const nuevaContrasena = ''; 

    if (!nuevoNombre || !nuevoUsername || !nuevoCorreo) {
        console.error("Todos los campos obligatorios deben estar llenos.");
        return;
    }

    const perfilData = {
        nombre: nuevoNombre,
        username: nuevoUsername,
        correo: nuevoCorreo,
    };

    try {
        const response = await fetch('/api/perfil', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(perfilData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Error al actualizar perfil: ${response.statusText}`);
        }

        // Actualizar el objeto local
        datosUsuarioLogueado.nombre = nuevoNombre;
        datosUsuarioLogueado.username = nuevoUsername;
        datosUsuarioLogueado.correo = nuevoCorreo;

        // Deshabilitar edición y aplicar opacidad
        const usernameInput = document.getElementById('username');
        const correoInput = document.getElementById('correo');

        usernameInput.setAttribute('readonly', 'true');
        correoInput.setAttribute('readonly', 'true');
        
        usernameInput.classList.add('input-no-editable');
        correoInput.classList.add('input-no-editable');

        console.log(data.message || "¡Perfil actualizado con éxito!");

    } catch (error) {
        console.error("Fallo al actualizar el perfil:", error.message);
    }
}

/* --- FUNCIONES DE ADMINISTRACIÓN --- */

/**
 * OBTENER DATOS DEL BACKEND y renderizar la tabla.
 */
async function obtenerYRenderizarUsuarios() {
    try {
        const response = await fetch('/api/usuarios'); // Llama a la ruta de la API
        
        if (response.status === 401) {
             console.error("Error 401: Sesión expirada o no iniciada.");
             return;
        }

        if (response.status === 403) {
            console.error("Error 403: No tiene permisos para acceder a la administración.");
            document.querySelector('#tabla-usuarios tbody').innerHTML = '<tr><td colspan="9">No tienes permisos para ver la administración de usuarios.</td></tr>';
            return;
        }
        
        if (!response.ok) {
            throw new Error(`Error al obtener usuarios: ${response.statusText}`);
        }
        
        listaUsuarios = await response.json(); 
        renderizarTablaUsuarios();

    } catch (error) {
        console.error("Fallo al cargar la lista de usuarios desde la API:", error);
    }
}

/**
 * Renderiza la tabla de usuarios con la lista actual.
 */function renderizarTablaUsuarios() {
    const tbody = document.querySelector('#tabla-usuarios tbody');
    tbody.innerHTML = ''; 

    listaUsuarios.forEach(usuario => {
        const fila = tbody.insertRow();
        const tipoMap = { 'A': 'Alumno', 'P': 'Profesor', 'G': 'Gestor' };
        
        const esVigente = usuario.vigencia === 1 || usuario.vigencia === true; 
        const estadoVigencia = esVigente ? 'VIGENTE' : 'NO VIGENTE';
        
        fila.insertCell().textContent = usuario.usuario_id;
        fila.insertCell().textContent = usuario.username;
        fila.insertCell().textContent = usuario.nombre;
        fila.insertCell().textContent = usuario.correo;
        fila.insertCell().textContent = tipoMap[usuario.tipo_usuario] || usuario.tipo_usuario;
        fila.insertCell().textContent = usuario.cant_monedas || 0; 
        fila.insertCell().textContent = usuario.dni || '';
        
        // Columna Vigencia
        const vigenciaCell = fila.insertCell();
        vigenciaCell.innerHTML = `<span style="color: ${esVigente ? 'green' : 'red'}; font-weight: bold;">${estadoVigencia}</span>`;


        // Celda de acciones
        const accionesCell = fila.insertCell();
        accionesCell.classList.add('acciones-tabla');

        const btnEditar = document.createElement('button');
        btnEditar.textContent = 'Editar';
        btnEditar.classList.add('btn-editar');
        btnEditar.onclick = () => cargarParaEdicion(usuario.usuario_id);
        
        // --- Lógica condicional para Dar de Baja o Dar de Alta ---
        if (esVigente) {
            const btnDarDeBaja = document.createElement('button');
            btnDarDeBaja.textContent = 'Dar de Baja';
            btnDarDeBaja.classList.add('btn-dar-baja'); 
            btnDarDeBaja.onclick = () => {
                const usernameAInactivar = listaUsuarios.find(u => u.usuario_id === usuario.usuario_id)?.username || usuario.usuario_id;
                if (window.confirm(`¿Estás seguro de que quieres dar de baja (inactivar) al usuario "${usernameAInactivar}" (ID: ${usuario.usuario_id})?`)) {
                    eliminarUsuario(usuario.usuario_id);  // DELETE /api/usuarios/<id> (vigente=0)
                }
            };
            accionesCell.appendChild(btnDarDeBaja);
        } else {
            const btnDarDeAlta = document.createElement('button');
            btnDarDeAlta.textContent = 'Dar de Alta';
            btnDarDeAlta.classList.add('btn-dar-alta'); 
            btnDarDeAlta.onclick = () => {
                const usernameAActivar = listaUsuarios.find(u => u.usuario_id === usuario.usuario_id)?.username || usuario.usuario_id;
                if (window.confirm(`¿Estás seguro de que quieres dar de alta (activar) al usuario "${usernameAActivar}" (ID: ${usuario.usuario_id})?`)) {
                    activarUsuario(usuario.usuario_id); // PUT /api/usuarios/<id>/activar (vigente=1)
                }
            };
            accionesCell.appendChild(btnDarDeAlta);
        }

        accionesCell.appendChild(btnEditar);
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
    const formGestion = document.getElementById('form-gestion-usuario');
    
    document.getElementById('form-titulo').textContent = 'Editar';
    formGestion.style.display = 'block';

    document.getElementById('gestion-usuario_id').value = usuario.usuario_id || '';
    document.getElementById('gestion-nombre').value = usuario.nombre || '';
    document.getElementById('gestion-username').value = usuario.username || '';
    document.getElementById('gestion-correo').value = usuario.correo || '';
    document.getElementById('gestion-dni').value = usuario.dni || ''; 
    document.getElementById('gestion-tipo_usuario').value = usuario.tipo_usuario || '';
    
    // 🔑 CLAVE: CARGAR ESTADO DE VIGENCIA EN EL SELECT
    const vigenciaValue = usuario.vigencia === 1 || usuario.vigencia === true ? 'true' : 'false';
    document.getElementById('gestion-vigencia').value = vigenciaValue;
    
    
    // 🛠️ CLAVE: Establecer `readonly` Y CLASE PARA OPACIDAD
    
    // Campos que NO se pueden modificar (ID, Correo, DNI, Tipo de Usuario)
    const camposNoEditables = [
        document.getElementById('gestion-usuario_id'),
        document.getElementById('gestion-correo'),
        document.getElementById('gestion-dni'),
        document.getElementById('gestion-tipo_usuario')
    ];

    camposNoEditables.forEach(input => {
        if (input) {
            input.setAttribute('readonly', true);
            // 💡 Añadir clase CSS para el estilo opaco
            input.classList.add('input-no-editable'); 
        }
    });
    
    // 🔑 El campo de CONTRASEÑA NO existe en el HTML, por lo que no es necesario ocultarlo.
    
    // Campos que SÍ se pueden modificar (Nombre, Username, Vigencia)
    document.getElementById('gestion-nombre').removeAttribute('readonly'); 
    document.getElementById('gestion-username').removeAttribute('readonly'); 
    document.getElementById('gestion-nombre').classList.remove('input-no-editable'); 
    document.getElementById('gestion-username').classList.remove('input-no-editable'); 


    formGestion.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Función que llama a la API para INACTIVAR (Dar de Baja) a un usuario.
 */
async function eliminarUsuario(usuarioId) {
    try {
        const response = await fetch(`/api/usuarios/${usuarioId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Fallo al dar de baja al usuario.'); 
        }

        console.log(data.message);
        await obtenerYRenderizarUsuarios(); 
    } catch (error) {
        console.error('Error al dar de baja (inactivar) al usuario:', error.message);
    }
}

/**
 * Función que llama a la API para ACTIVAR (Dar de Alta) a un usuario.
 */
async function activarUsuario(usuarioId) {
    try {
        const response = await fetch(`/api/usuarios/${usuarioId}/activar`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Fallo en la activación del usuario.');
        }

        console.log(data.message);
        await obtenerYRenderizarUsuarios(); 
    } catch (error) {
        console.error('Error al dar de alta (activar) al usuario:', error.message);
    }
}

/**
 * Maneja el envío del formulario de gestión de usuarios (SOLO EDICIÓN).
 */
async function manejarGuardarGestion(event) {
    event.preventDefault();

    const id = document.getElementById('gestion-usuario_id').value;
    const nombre = document.getElementById('gestion-nombre').value;
    const username = document.getElementById('gestion-username').value;
    
    const vigenciaString = document.getElementById('gestion-vigencia').value;
    const vigencia = vigenciaString === 'true'; 
    
    // VALIDACIÓN CLAVE
    if (!id || !nombre || !username) {
        console.error("Para editar, ID, Nombre y Username deben estar llenos."); 
        return;
    }

    // 🛠️ CLAVE: SOLO ENVIAMOS LOS CAMPOS PERMITIDOS POR EL BACKEND
    const userData = {
        nombre,
        username,
        vigencia 
    };
    
    let url = `/api/usuarios/${id}`;
    
    try {
        console.log(`Petición PUT a ${url} con datos:`, userData);
        
        const response = await fetch(url, { 
            method: 'PUT', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(userData) 
        });

        const data = await response.json();

        if (!response.ok) {
             throw new Error(data.error || `Error al actualizar: ${response.status} ${response.statusText}`);
        }
        
        console.log(data.message || `¡Usuario ${username} actualizado con éxito!`); 
        
        // Simular éxito y recargar
        document.getElementById('form-gestion-usuario').reset();
        document.getElementById('form-gestion-usuario').style.display = 'none';
        usuarioEditandoId = null;
        await obtenerYRenderizarUsuarios(); 
        
    } catch (error) {
        console.error("Fallo en la gestión del usuario:", error.message);
        console.error(`Error al guardar: ${error.message}`); 
    }
}

/**
 * Inicializa los listeners de eventos al cargar el DOM.
 */
document.addEventListener('DOMContentLoaded', async () => {
    // 🔑 CAMBIO: Inicialmente intenta obtener y cargar el perfil de la API
    await cargarDatosPerfil(); 
    
    // 1. Listeners para Pestañas
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', cambiarPestana);
    });

    // 2. Listeners para Perfil Propio
    document.getElementById('form-perfil').addEventListener('submit', manejarGuardarPerfil);
    document.getElementById('cancelar').addEventListener('click', () => {
        // Recargar el perfil desde el objeto actual (o la API si es necesario)
        cargarDatosPerfil();
        
        // Re-deshabilitar y aplicar opacidad a los campos que solo se editan con el icono.
        const usernameInput = document.getElementById('username');
        const correoInput = document.getElementById('correo');

        usernameInput.setAttribute('readonly', 'true');
        correoInput.setAttribute('readonly', 'true');

        usernameInput.classList.add('input-no-editable');
        correoInput.classList.add('input-no-editable');
        
        console.log("Cambios de perfil cancelados.");
        // Opcional: Limpiar campos de contraseña si existen en el HTML
        if (document.getElementById('contrasena_actual')) document.getElementById('contrasena_actual').value = '';
        if (document.getElementById('nueva_contrasena')) document.getElementById('nueva_contrasena').value = '';
    });

    // 3. Listeners para Administración
    const formGestion = document.getElementById('form-gestion-usuario');
    const btnCancelarGestion = document.getElementById('btn-cancelar-gestion');

    // Oculta el formulario de gestión
    btnCancelarGestion.addEventListener('click', () => {
        formGestion.reset();
        formGestion.style.display = 'none';
        usuarioEditandoId = null;
        
        // 💡 Quitar clases de opacidad si se van a reusar los campos (aunque en este caso no afecta)
        document.getElementById('gestion-usuario_id').classList.remove('input-no-editable');
        document.getElementById('gestion-correo').classList.remove('input-no-editable');
        document.getElementById('gestion-dni').classList.remove('input-no-editable');
        document.getElementById('gestion-tipo_usuario').classList.remove('input-no-editable');
        
        // Quitar readonly para reusar el formulario (si aplica)
        document.getElementById('gestion-usuario_id').removeAttribute('readonly'); 
        document.getElementById('gestion-correo').removeAttribute('readonly');
        document.getElementById('gestion-dni').removeAttribute('readonly');
        document.getElementById('gestion-tipo_usuario').removeAttribute('readonly'); 
    });

    // Maneja la creación/edición al guardar (Ahora solo edición)
    formGestion.addEventListener('submit', manejarGuardarGestion);
    
});