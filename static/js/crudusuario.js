// =========================================================
// Variables de Estado Global
// =========================================================
let datosUsuarioLogueado = {}; // Contiene los datos del usuario logueado
let listaUsuarios = []; // Contiene la lista de usuarios para la administración
let usuarioEditandoId = null; // Para rastrear qué usuario estamos editando
async function obtenerDatosPerfil() {
    try {
        // Usando el endpoint: /api/perfil (Asegúrate de que esta ruta coincida con tu backend)
        const response = await fetch('/api/perfil'); 
        
        // 🔑 VERIFICACIÓN 1: Muestra el estado de la respuesta
        console.log("DEBUG API: Estado de la respuesta:", response.status, response.statusText);
        
        if (response.status === 401) {
            console.error("Error 401: Sesión expirada o no iniciada.");
            return null;
        }

        if (!response.ok) {
            // Muestra más detalles si no es un 401 pero falla
            const errorBody = await response.text(); 
            throw new Error(`Error al obtener el perfil: ${response.statusText}. Cuerpo: ${errorBody.substring(0, 100)}`);
        }
        
        datosUsuarioLogueado = await response.json(); 
        
        // 🔑 VERIFICACIÓN 2: MUESTRA LOS DATOS RECIBIDOS EN CONSOLA
        console.log("DEBUG PERFIL: Datos del usuario logueado (JSON):", datosUsuarioLogueado);
        
        return datosUsuarioLogueado;

    } catch (error) {
        console.error("Fallo al cargar los datos del perfil desde la API:", error);
        return null;
    }
}
// ---------------------------------------------------------------------
/**
 * Función para cargar los datos del objeto REAL en la interfaz de perfil y en el Header.
 * Esta función no necesita cambios, ya que obtenerDatosPerfil() ahora verifica los datos.
 */
async function cargarDatosPerfil() {
    // Si los datos no se han cargado aún, intentamos obtenerlos
    if (Object.keys(datosUsuarioLogueado).length === 0) {
        await obtenerDatosPerfil();
    }
    
    // 🔑 VERIFICACIÓN 3: Muestra qué datos se intentarán renderizar
    console.log("DEBUG RENDER: Intentando renderizar el objeto:", datosUsuarioLogueado);
    
    // Verificamos si la carga fue exitosa
    if (datosUsuarioLogueado && datosUsuarioLogueado.usuario_id) {
        // 1. Rellenar campos del formulario 'Editar perfil' (con guards, algunos campos pueden no existir según rol)
        const elUsuarioId = document.getElementById('usuario_id');
        const elNombre = document.getElementById('nombre');
        const elUsername = document.getElementById('username');
        const elCorreo = document.getElementById('correo');

        if (elUsuarioId) elUsuarioId.value = datosUsuarioLogueado.usuario_id || '';
        if (elNombre) elNombre.value = datosUsuarioLogueado.nombre || '';
        if (elUsername) elUsername.value = datosUsuarioLogueado.username || '';
        if (elCorreo) elCorreo.value = datosUsuarioLogueado.correo || '';

        // 2.b URL DE FOTO DE PERFIL (preview + campo)
        const urlFotoInput = document.getElementById('url_foto_perfil');
        const urlFotoPreview = document.getElementById('url_foto_perfil_preview');
        const fotoUrl = datosUsuarioLogueado.url_foto_perfil || datosUsuarioLogueado.url_avatar || '';
        if (urlFotoInput) urlFotoInput.value = fotoUrl;
        if (urlFotoPreview) urlFotoPreview.src = fotoUrl || '/static/img/avatar.jpeg';

        // 2.c Actualizar imagen de perfil en header (todas las ocurrencias) con cache-buster
        try {
            const imgs = document.querySelectorAll('.profile-img');
            imgs.forEach(img => {
                const src = fotoUrl || img.getAttribute('src') || '/static/img/avatar.jpeg';
                // Añadir cache-buster corto
                const cacheBusted = src + (src.includes('?') ? '&' : '?') + 'v=' + Date.now();
                img.src = cacheBusted;
            });
        } catch (e) {
            console.warn('No se pudo actualizar la imagen de header:', e);
        }

        // 2. Rellenar campos no editables (DNI)
        document.getElementById('dni').value = datosUsuarioLogueado.dni || 'N/A';

        // 3. Monedas (Display en Formulario y Header)
        const cantMonedas = datosUsuarioLogueado.cant_monedas || 0;
        
        // Actualiza el display de monedas DENTRO del formulario
        const cantMonedasDisplay = document.getElementById('cant_monedas_display');
        if (cantMonedasDisplay) cantMonedasDisplay.textContent = `${cantMonedas} 🪙`;
        
        // CORRECCIÓN: Actualiza el contador de monedas en el HEADER
        const cantMonedasHeader = document.getElementById('cant_monedas');
        if (cantMonedasHeader) cantMonedasHeader.textContent = cantMonedas; 
        
        // 4. Tipo de Usuario (Mapeo)
        const tipoMap = { 'A': 'Alumno', 'P': 'Profesor', 'G': 'Gestor' }; 
        const tipo = tipoMap[datosUsuarioLogueado.tipo_usuario] || 'Desconocido';
        const tipoUsuarioInput = document.getElementById('tipo_usuario');
        if (tipoUsuarioInput) tipoUsuarioInput.value = tipo;

        // 5. Vigencia (Mapeo)
        const esVigente = datosUsuarioLogueado.vigencia === 1 || datosUsuarioLogueado.vigencia === true;
        const vigenciaTexto = esVigente ? 'Vigente (Activo)' : 'No Vigente (Inactivo)';
        const vigenciaInput = document.getElementById('vigencia');
        if (vigenciaInput) vigenciaInput.value = vigenciaTexto;
        
        // 6. CORRECCIÓN: Actualizar Nombre de Usuario en el HEADER (usando el nuevo ID)
        const headerNombreElement = document.getElementById('header_perfil_nombre');
        if (headerNombreElement) {
            headerNombreElement.textContent = datosUsuarioLogueado.username || 'Mi Perfil';
        }
        
        // 7. Asegurar las clases de deshabilitado (Se ha añadido una pequeña validación por si el elemento no existe)
        const idsADeshabilitar = ['usuario_id', 'dni', 'tipo_usuario', 'vigencia'];
        idsADeshabilitar.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('input-deshabilitado');
        });
        
    } else {
        console.error("No se pudieron cargar los datos del usuario logueado. Objeto final:", datosUsuarioLogueado);
    }
}

/**
 * Muestra un modal de confirmación y devuelve una Promise<boolean>.
 * Usa los elementos añadidos en la plantilla: #modal-confirm
 */
/**
 * Mostrar el modal usado en `solicitar_restablecer.html` si está disponible.
 * Devuelve una Promise que se resuelve cuando el usuario cierra/acepta el modal.
 * Para confirmaciones sencillas usamos el mismo modal (aceptar/ok).
 */
function showModalAsync(title, message, options) {
    return new Promise((resolve) => {
        // Si existe la función global showModal (ui_modal.js), la usamos
        if (typeof window.showModal === 'function') {
            try {
                window.showModal(title, message, { onClose: function () { resolve(true); } });
                return;
            } catch (e) {
                console.warn('showModal fallo, fallback a native', e);
            }
        }

        // Fallbacks: si se pasa opción de confirm, usar confirm(), sino alert()
        if (options && options.confirm) {
            const ok = window.confirm(message);
            resolve(!!ok);
        } else {
            window.alert(message);
            resolve(true);
        }
    });
}

/**
 * Muestra un modal de mensaje simple.
 */
function showMessageModal(title, message) {
    // Reuse showModal if available for consistent UX
    return showModalAsync(title, message);
}

/**
 * 🔑 NUEVO: Maneja el proceso de Dar de Baja (Inactivar) la cuenta propia.
 */
async function manejarDarDeBajaPropia() {
    const usuarioId = datosUsuarioLogueado.usuario_id;
    const username = datosUsuarioLogueado.username;

    if (!usuarioId) {
        console.error("Error: No se encontró el ID del usuario logueado.");
        return;
    }

    // ⚠️ Importante: Reemplazar window.confirm() con un modal UI personalizado 
    // en una aplicación real.
    if (!window.confirm(`¿Estás SEGURO de que quieres dar de BAJA tu propia cuenta (${username})? Esto la inactivará, pero podrás reactivarla contactando a un administrador.`)) {
        console.log("Inactivación de cuenta cancelada por el usuario.");
        return;
    }

    try {
        // Llama al mismo endpoint DELETE usado por el administrador
        const response = await fetch(`/api/usuarios/${usuarioId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (!response.ok) {
            // Manejar la restricción del backend (ej. Gestor no puede darse de baja)
            console.error(data.error || `Fallo al dar de baja la cuenta: ${response.statusText}`); 
            // ⚠️ Aquí podrías mostrar un mensaje de error más amigable al usuario.
            
            // Si es un 403 (Prohibido/Restricción de Gestor), recargamos el perfil 
            // por si acaso y salimos.
            if (response.status === 403) {
                alert(`Error: ${data.error}. No se pudo inactivar la cuenta.`);
                await cargarDatosPerfil();
            }
            return;
        }

        // Éxito: La cuenta ha sido inactivada.
        console.log(data.message || "¡Cuenta inactivada exitosamente!");
        alert("¡Tu cuenta ha sido inactivada exitosamente! Se cerrará la sesión.");

        // Forzar recarga de datos (mostrará como No Vigente)
        await cargarDatosPerfil();

        // Opcional y recomendado: Redirigir a la página de inicio o cerrar sesión.
        // window.location.href = '/logout'; 

    } catch (error) {
        console.error('Error durante la inactivación de la cuenta:', error.message);
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

    // Primero: si el usuario subió un archivo, enviarlo al endpoint de upload
    let uploadedUrl = null;
    const fileInput = document.getElementById('url_foto_perfil_file');
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append('foto', fileInput.files[0]);
        try {
            const uploadResp = await fetch('/api/perfil/upload', {
                method: 'POST',
                body: formData
            });
            const uploadData = await uploadResp.json();
            if (!uploadResp.ok) {
                throw new Error(uploadData.error || 'Error al subir la imagen de perfil.');
            }
            uploadedUrl = uploadData.url_foto_perfil;
        } catch (err) {
            console.error('Error al subir la imagen de perfil:', err.message || err);
            // Mostrar mensaje al usuario y abortar la operación de guardado
            alert('No se pudo subir la imagen de perfil. Intenta nuevamente.');
            return;
        }
    }

    const perfilData = {
        nombre: nuevoNombre,
        username: nuevoUsername,
        correo: nuevoCorreo,
        // Priorizar la URL resultante de la subida si existe
        url_foto_perfil: uploadedUrl || (document.getElementById('url_foto_perfil') && document.getElementById('url_foto_perfil').value) || undefined,
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
        // Actualizar url_foto_perfil local y en header si fue retornada
        if (data.url_foto_perfil) {
            datosUsuarioLogueado.url_foto_perfil = data.url_foto_perfil;
            const imgs = document.querySelectorAll('.profile-img');
            imgs.forEach(img => {
                const cacheBusted = data.url_foto_perfil + (data.url_foto_perfil.includes('?') ? '&' : '?') + 'v=' + Date.now();
                img.src = cacheBusted;
            });
            // También actualizar preview si existe
            const preview = document.getElementById('url_foto_perfil_preview');
            if (preview) preview.src = data.url_foto_perfil;
        } else {
            // Si backend no devolvió la URL, usar la que el usuario puso en el input
            const inputUrl = document.getElementById('url_foto_perfil') ? document.getElementById('url_foto_perfil').value : null;
            if (inputUrl) {
                const imgs = document.querySelectorAll('.profile-img');
                imgs.forEach(img => {
                    const cacheBusted = inputUrl + (inputUrl.includes('?') ? '&' : '?') + 'v=' + Date.now();
                    img.src = cacheBusted;
                });
                const preview = document.getElementById('url_foto_perfil_preview');
                if (preview) preview.src = inputUrl;
                datosUsuarioLogueado.url_foto_perfil = inputUrl;
            }
        }

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
        // Leer parámetros de UI (si están definidos) o usar valores por defecto
        const page = window.currentUsuariosPage || 1;
        const per_page = window.usuariosPerPage || 20;
        const response = await fetch(`/api/usuarios?page=${page}&per_page=${per_page}`); // Llama a la ruta de la API
        
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
        
        const payload = await response.json();
        // Si la API devuelve el formato paginado
        if (payload && payload.users) {
            listaUsuarios = payload.users;
            // Guardar metadatos
            window.currentUsuariosPage = payload.page || 1;
            window.usuariosPerPage = payload.per_page || per_page;
            window.usuariosTotal = payload.total || 0;
            window.usuariosTotalPages = payload.total_pages || 1;
        } else if (Array.isArray(payload)) {
            // Compatibilidad: API antigua devolvía una lista
            listaUsuarios = payload;
            window.currentUsuariosPage = 1;
            window.usuariosPerPage = listaUsuarios.length;
            window.usuariosTotal = listaUsuarios.length;
            window.usuariosTotalPages = 1;
        } else {
            listaUsuarios = [];
        }
        renderizarTablaUsuarios();
        renderizarPaginacion();

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

// Renderiza controles de paginación simples
function renderizarPaginacion() {
    const container = document.getElementById('paginacion-usuarios');
    if (!container) return;

    const page = window.currentUsuariosPage || 1;
    const total_pages = window.usuariosTotalPages || 1;

    container.innerHTML = '';

    const prev = document.createElement('button');
    prev.textContent = 'Anterior';
    prev.disabled = page <= 1;
    prev.onclick = async () => {
        if (page <= 1) return;
        window.currentUsuariosPage = page - 1;
        await obtenerYRenderizarUsuarios();
    };

    const next = document.createElement('button');
    next.textContent = 'Siguiente';
    next.disabled = page >= total_pages;
    next.onclick = async () => {
        if (page >= total_pages) return;
        window.currentUsuariosPage = page + 1;
        await obtenerYRenderizarUsuarios();
    };

    const info = document.createElement('span');
    info.textContent = ` Página ${page} de ${total_pages} `;

    container.appendChild(prev);
    container.appendChild(info);
    container.appendChild(next);
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


// =========================================================
// NUEVA FUNCIÓN PARA CONFIRMACIÓN
// =========================================================
/**
 * Pide confirmación y, si es afirmativa, llama a la función asíncrona 
 * que maneja la baja por API (fetch DELETE).
 */
function confirmarYManejarBaja() {
    const username = datosUsuarioLogueado.username || "este usuario";
    
    const mensaje = `¿Estás ABSOLUTAMENTE SEGURO de que quieres dar de BAJA tu cuenta (${username})? Esta acción la marcará como 'No Vigente' y te desconectará del sistema.`;
    
    if (window.confirm(mensaje)) {
        // Si el usuario confirma, llamamos a la función asíncrona de la API
        manejarDarDeBajaPropia(); 
    } else {
        console.log("Acción de baja de cuenta cancelada por el usuario.");
    }
}


/**
 * Función para Dar de Baja (Inactivar) la cuenta propia usando la API DELETE.
 * (La copio de tu código original para referencia, verifica que esté allí)
 */
// =========================================================
// Función Asíncrona (CORREGIDA)
// =========================================================
async function manejarDarDeBajaPropia() {
    const usuarioId = datosUsuarioLogueado.usuario_id;

    if (!usuarioId) {
        alert("Error: No se encontró el ID del usuario logueado para dar de baja.");
        return;
    }

    try {
        // Llama a la ruta de Flask /baja_cuenta con método POST
        const response = await fetch(`/baja_cuenta`, {
            method: 'POST',
            // Correcto: no se envían headers JSON.
        });

        // Correcto: se elimina el parsing de JSON.

        if (response.redirected) {
            console.log("Baja exitosa. El servidor está redirigiendo para cerrar sesión.");
            
            // 🔑 CLAVE: Forzar la navegación del navegador a la ruta de logout
            // que es el destino final de la redirección de Flask.
            window.location.href = '/logout'; 
            
            return;
        } 
        
        // Si no hay redirección (Flask retorna a 'crud_usuarios'):
        if (!response.ok) {
            // Manejo de errores de red o servidor no cubiertos.
            console.error(`Respuesta del servidor no exitosa: ${response.status}`);
            alert('Ocurrió un error al procesar la baja de la cuenta. Revisa los mensajes en pantalla.');
        } else {
            // Caso donde la cuenta ya estaba inactiva (Flask redirigió a crud_usuarios con un 'flash')
            alert("El proceso de baja ha terminado. Revisa si hay mensajes de estado en la página.");
        }


    } catch (error) {
        console.error('Error durante la inactivación de la cuenta:', error.message);
        alert('Ocurrió un error de red o interno al intentar dar de baja la cuenta.');
    }
}

// Llama a esta función al cargar los datos del perfil si no usas el hidden input en el formulario.
// Si usas el hidden input como en la sección 1, solo la función `confirmarBaja()` es necesaria.

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

    // Live preview para URL de foto de perfil (si existe el campo)
    const urlFotoInput = document.getElementById('url_foto_perfil');
    if (urlFotoInput) {
        urlFotoInput.addEventListener('input', (e) => {
            const preview = document.getElementById('url_foto_perfil_preview');
            if (preview) preview.src = e.target.value || '/static/img/avatar.jpeg';
        });
    }

    // Preview para archivo local seleccionado
    const fileInput = document.getElementById('url_foto_perfil_file');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const preview = document.getElementById('url_foto_perfil_preview');
            const file = e.target.files && e.target.files[0];
            if (file && preview) {
                try {
                    const objectUrl = URL.createObjectURL(file);
                    preview.src = objectUrl;
                    // Liberar el objectURL cuando la imagen cargue
                    preview.onload = () => { URL.revokeObjectURL(objectUrl); };
                } catch (err) {
                    console.warn('No se pudo crear preview local:', err);
                }
            } else if (preview) {
                // Si se deseleccionó, volver a la URL que esté en el campo
                const urlInput = document.getElementById('url_foto_perfil');
                preview.src = (urlInput && urlInput.value) ? urlInput.value : '/static/img/avatar.jpeg';
            }
        });
    }

    // Manejo del formulario de cambio de contraseña
    const formContrasena = document.getElementById('form-contrasena');
    if (formContrasena) {
        formContrasena.addEventListener('submit', async (e) => {
            e.preventDefault();
            const actual = document.getElementById('contrasena_actual') ? document.getElementById('contrasena_actual').value : '';
            const nueva = document.getElementById('nueva_contrasena') ? document.getElementById('nueva_contrasena').value : '';
            const confirmar = document.getElementById('confirmar_nueva_contrasena') ? document.getElementById('confirmar_nueva_contrasena').value : '';

            if (!actual || !nueva || !confirmar) {
                await showMessageModal('Error', 'Completa todos los campos.');
                return;
            }
            // Validación avanzada estilo restablecer.html: longitud y composición
            const errors = [];
            if (nueva.length < 8) errors.push('Debe tener al menos 8 caracteres.');
            if (!/[A-Z]/.test(nueva)) errors.push('Debe contener al menos una letra Mayúscula.');
            if (!/[a-z]/.test(nueva)) errors.push('Debe contener al menos una letra Minúscula.');
            if (!/[0-9]/.test(nueva)) errors.push('Debe contener al menos un número.');
            if (!/[!@#$%^&*()_+\-=[\]{};:\"\\|,.<>/?]/.test(nueva)) errors.push('Debe contener al menos un carácter especial (ej. !@#$%).');
            if (nueva !== confirmar) errors.push('La nueva contraseña y la confirmación no coinciden.');

            if (errors.length > 0) {
                // Mostrar detalles en modal (mismo estilo que restablecer)
                const detalle = 'La contraseña no cumple los requisitos:\n- ' + errors.join('\n- ');
                await showModalAsync('Contraseña inválida', detalle);
                return;
            }

            const confirmed = await showModalAsync('Confirmación', '¿Confirma que desea cambiar su contraseña?', { confirm: true });
            if (!confirmed) return;

            try {
                const resp = await fetch('/api/perfil/password', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contrasena_actual: actual, nueva_contrasena: nueva })
                });
                const data = await resp.json();
                if (!resp.ok) {
                    await showMessageModal('Error', data.error || 'No se pudo cambiar la contraseña.');
                    return;
                }
                // Éxito
                document.getElementById('contrasena_actual').value = '';
                document.getElementById('nueva_contrasena').value = '';
                document.getElementById('confirmar_nueva_contrasena').value = '';
                await showMessageModal('Éxito', data.message || 'Contraseña cambiada correctamente.');
            } catch (err) {
                console.error('Error cambiando contraseña:', err);
                await showMessageModal('Error', 'Error de red o servidor. Intenta más tarde.');
            }
        });

        const btnCancelarContrasena = document.getElementById('btn-cancelar-contrasena');
        if (btnCancelarContrasena) btnCancelarContrasena.addEventListener('click', () => {
            formContrasena.reset();
        });
    }

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
