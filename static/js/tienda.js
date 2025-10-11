document.addEventListener('DOMContentLoaded', function () {
    // --- Referencias Comunes ---
    const btnAccesorios = document.getElementById('btn-crud-accesorios');
    const btnSkins = document.getElementById('btn-crud-skins');
    const modalAccesorio = document.getElementById('modal-accesorio');
    const modalSkin = document.getElementById('modal-skin');
    const cerrarModales = document.querySelectorAll('.cerrar-modal');

    // Función para dibujar las filas de la tabla
    function dibujarTabla(items, tablaId, tipo) {
        const tbody = document.querySelector(`#${tablaId} tbody`);
        tbody.innerHTML = ''; // Limpiar contenido actual

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4">No hay ${tipo} registrados en la base de datos.</td></tr>`;
            return;
        }

        items.forEach(item => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.nombre}</td>
                <td>${item.precio} 🪙</td>
                <td>
                    <button class="btn-accion btn-editar" data-id="${item.id}" data-tipo="${tipo}">✏️ Editar</button>
                    <button class="btn-accion btn-eliminar" data-id="${item.id}" data-tipo="${tipo}">🗑️ Eliminar</button>
                </td>
            `;
        });

        // Vuelve a asignar los eventos a los nuevos botones
        asignarEventosAccion();
    }

    // Función para obtener y cargar datos desde el backend
    async function cargarDatosCRUD(tipo) {
        const apiUrl = `/api/tienda/${tipo}`;
        const tablaId = `tabla-${tipo}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                // Si el servidor responde con error 403 (Prohibido) o 401 (No autorizado)
                const errorData = await response.json();
                const tbody = document.querySelector(`#${tablaId} tbody`);
                tbody.innerHTML = `<tr><td colspan="4">Error: ${errorData.error || 'No se pudo cargar la lista.'}</td></tr>`;
                console.error(`Error al cargar ${tipo}:`, errorData.error);
                return;
            }
            const data = await response.json();
            dibujarTabla(data, tablaId, tipo);
        } catch (error) {
            console.error(`Error de red al obtener ${tipo}:`, error);
            const tbody = document.querySelector(`#${tablaId} tbody`);
            tbody.innerHTML = `<tr><td colspan="4">Error de conexión con el servidor.</td></tr>`;
        }
    }


    // --- Lógica de Apertura/Cierre del Modal Principal ---
    function abrirModal(modal, tipo) {
        modal.style.display = 'block';
        // 🚨 Cargar datos al abrir el modal de CRUD
        cargarDatosCRUD(tipo);
    }

    function cerrarModal(modal, tipo) {
        modal.style.display = 'none';
        // Asegurarse de que al cerrar siempre vuelva a la vista de lista
        if (tipo) mostrarVista(tipo, 'lista');
    }

    btnAccesorios.addEventListener('click', () => abrirModal(modalAccesorio, 'accesorios'));
    btnSkins.addEventListener('click', () => abrirModal(modalSkin, 'skins'));

    cerrarModales.forEach(span => {
        span.addEventListener('click', function () {
            const modal = span.closest('.modal');
            const tipo = modal.id.includes('accesorio') ? 'accesorios' : 'skins';
            cerrarModal(modal, tipo);
        });
    });

    window.addEventListener('click', function (event) {
        if (event.target === modalAccesorio) cerrarModal(modalAccesorio, 'accesorios');
        if (event.target === modalSkin) cerrarModal(modalSkin, 'skins');
    });

    // --- Lógica de Transición de Vistas CRUD (Lista vs Formulario) ---

    function mostrarVista(tipo, vista, datos = null) {
        // 💡 SOLUCIÓN: Definimos el prefijo basado en el tipo para asegurar consistencia con el HTML
        let prefijo = '';
        let tipoSingular = '';

        if (tipo === 'accesorios') {
            prefijo = 'acc';
            tipoSingular = 'accesorio'; // Usado para textos (títulos)
        } else if (tipo === 'skins') {
            prefijo = 'skin';
            tipoSingular = 'skin'; // Usado para textos (títulos)
        } else {
            console.error(`Tipo desconocido: ${tipo}`);
            return;
        }

        // Buscamos los elementos usando el prefijo ('acc' o 'skin')
        const listaVista = document.getElementById(`${prefijo}-lista-vista`);
        const formVista = document.getElementById(`${prefijo}-form-vista`);

        // **VERIFICACIÓN CRÍTICA**: Si el elemento no existe, detenemos la ejecución.
        if (!listaVista || !formVista) {
            // Este error ya no debería aparecer si el HTML tiene 'acc-' y 'skin-'
            console.error(`Error de JavaScript: No se encontró el DIV de vista para ${prefijo}.`);
            return;
        }

        const formTitulo = document.getElementById(`${prefijo}-form-titulo`);
        const formSubmitBtn = document.getElementById(`btn-${prefijo}-submit`);
        const formId = document.getElementById(`${prefijo}-id`);
        const form = document.getElementById(`form-${prefijo}`);

        // Lógica de Ocultar/Mostrar
        if (vista === 'lista') {
            // Mostrar la lista
            listaVista.classList.remove('oculto');
            formVista.classList.add('oculto');

            if (form) form.reset();
            cargarDatosCRUD(tipo); // Recargar la lista al volver

        } else if (vista === 'form') {
            // Mostrar el formulario (CREAR/EDITAR)
            listaVista.classList.add('oculto');
            formVista.classList.remove('oculto');

            if (datos) { // Modo Editar
                if (formTitulo) formTitulo.textContent = `Editar ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}: ${datos.nombre}`;
                if (formSubmitBtn) formSubmitBtn.textContent = 'Guardar Cambios';
                if (formId) formId.value = datos.id;

                // Asignar valores a los campos de input si existen
                const nombreInput = document.getElementById(`${prefijo}-nombre`);
                const urlInput = document.getElementById(`${prefijo}-url`);
                const precioInput = document.getElementById(`${prefijo}-precio`);

                if (nombreInput) nombreInput.value = datos.nombre || '';
                if (urlInput) urlInput.value = datos.url_imagen || '';
                if (precioInput) precioInput.value = datos.precio || 0;

            } else { // Modo Crear
                if (formTitulo) formTitulo.textContent = `Agregar Nuevo ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}`;
                if (formSubmitBtn) formSubmitBtn.textContent = `Crear ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}`;
                if (formId) formId.value = '';
                if (form) form.reset();
            }
        }
    }

    // Eventos de botones para cambiar de vista (Crear/Volver)
    document.getElementById('btn-acc-abrir-crear').addEventListener('click', () => mostrarVista('accesorios', 'form'));
    document.getElementById('btn-acc-volver-lista').addEventListener('click', () => mostrarVista('accesorios', 'lista'));
    document.getElementById('btn-skin-abrir-crear').addEventListener('click', () => mostrarVista('skins', 'form'));
    document.getElementById('btn-skin-volver-lista').addEventListener('click', () => mostrarVista('skins', 'lista'));


    // --- Lógica para Botones de Acciones (Asignación de Eventos) ---

    function asignarEventosAccion() {
        // Evento para Editar
        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', async function () {
                const id = this.getAttribute('data-id');
                const tipo = this.getAttribute('data-tipo');
                const nombre = this.closest('tr').cells[1].textContent;
                const precio = parseInt(this.closest('tr').cells[2].textContent);

                if (tipo === 'accesorios') { // Lógica específica para Accesorios
                    try {
                        // Petición GET al backend para obtener el accesorio completo (incluyendo url_imagen)
                        const response = await fetch(`/api/tienda/accesorios/${id}`);
                        const data = await response.json();

                        if (response.ok) {
                            // data ya contiene {id, nombre, precio, url_imagen}
                            mostrarVista(tipo, 'form', data);
                        } else {
                            alert(`❌ Error al cargar accesorio: ${data.message}`);
                        }
                    } catch (error) {
                        console.error('Error al obtener accesorio:', error);
                        alert('Hubo un error de conexión al cargar los datos del accesorio.');
                    }
                }else{
                    try {
                        //Petición GET al backend para obtener el accesorio completo (incluyendo url_imagen)
                        const response = await fetch(`/api/tienda/skin/${id}`);
                        const data = await response.json();

                        if (response.ok) {
                            // data ya contiene {id, nombre, precio, url_imagen}
                            mostrarVista(tipo, 'form', data);
                        } else {
                            alert(`❌ Error al cargar  skin: ${data.message}`);
                        }
                    } catch (error) {
                        console.error('Error al obtener skin:', error);
                        alert('Hubo un error de conexión al cargar los datos del skin.');
                    }
                }

            });
        });

        // Evento para Eliminar
        document.querySelectorAll('.btn-eliminar').forEach(btn => {
            btn.addEventListener('click', async function () { // Agregamos 'async'
                const id = this.getAttribute('data-id');
                const tipo = this.getAttribute('data-tipo');
                const nombre = this.closest('tr').cells[1].textContent;

                if (confirm(`⚠️ ¿Estás seguro de que quieres eliminar el ${tipo.slice(0, -1)} '${nombre}' (ID ${id})? Esta acción no se puede deshacer.`)) {
                    if (tipo === 'accesorios') {
                        try {
                            // Lógica de ELIMINAR (DELETE) para accesorios
                            const response = await fetch(`/api/tienda/accesorios/eliminar/${id}`, {
                                method: 'DELETE'
                            });

                            const data = await response.json();

                            if (data.success) {
                                alert(`✅ ${data.message}`);
                                cargarDatosCRUD(tipo); // Recargar la lista
                            } else {
                                alert(`❌ Error al eliminar: ${data.message}`);
                            }
                        } catch (error) {
                            console.error('Error de red/servidor al eliminar:', error);
                            alert('Hubo un error de conexión al intentar eliminar el accesorio.');
                        }
                    } else {
                        try {
                            // Lógica de ELIMINAR (DELETE) para skins
                            const response = await fetch(`/api/tienda/skin/eliminar/${id}`, {
                                method: 'DELETE'
                            });

                            const data = await response.json();

                            if (data.success) {
                                alert(`✅ ${data.message}`);
                                cargarDatosCRUD(tipo); // Recargar la lista
                            } else {
                                alert(`❌ Error al eliminar: ${data.message}`);
                            }
                        } catch (error) {
                            console.error('Error de red/servidor al eliminar:', error);
                            alert('Hubo un error de conexión al intentar eliminar el skin.');
                        }
                    }
                }
            });
        });
    }

    // --- Lógica de Formulario (Simulación de Envío) ---
    // Mantener la lógica de simulación de envío, pero ahora usa la función de recarga
    document.getElementById('form-accesorio').addEventListener('submit', async function (event) {
        event.preventDefault();

        const form = event.target;
        const id = document.getElementById('acc-id').value;
        const formData = new FormData(form);

        let url = '/api/tienda/accesorios/crear';
        let method = 'POST';
        let accion = 'Crear';

        // 💡 Lógica de Actualizar (Editar)
        if (id) {
            url = `/api/tienda/accesorios/editar/${id}`;
            method = 'POST';
            accion = 'Actualizar';
        }

        try {
            const response = await fetch(url, {
                method: method,
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                alert(`✅ Accesorio ${accion} con éxito. ID: ${data.accesorio_id || id}`);
                // Vuelve y recarga la lista de accesorios
                mostrarVista('accesorios', 'lista');
            } else {
                alert(`❌ Error al ${accion.toLowerCase()} accesorio: ${data.message}`);
            }

        } catch (error) {
            console.error('Error de red/servidor:', error);
            alert(`Hubo un error de conexión al intentar ${accion.toLowerCase()} el accesorio.`);
        }
    });

    document.getElementById('form-skin').addEventListener('submit', async function (event) {
        event.preventDefault();

        const form = event.target;
        const id = document.getElementById('skin-id').value;
        const formData = new FormData(form);

        let url = '/api/tienda/skin/crear';
        let method = 'POST';
        let accion = 'Crear';

        // 💡 Lógica de Actualizar (Editar)
        if (id) {
            url = `/api/tienda/skin/editar/${id}`;
            method = 'POST';
            accion = 'Actualizar';
        }

        try {
            const response = await fetch(url, {
                method: method,
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                alert(`✅ Skin ${accion} con éxito. ID: ${data.skin_id || id}`);
                // Vuelve y recarga la lista de skins
                mostrarVista('skins', 'lista');
            } else {
                alert(`❌ Error al ${accion.toLowerCase()} skin: ${data.message}`);
            }

        } catch (error) {
            console.error('Error de red/servidor:', error);
            alert(`Hubo un error de conexión al intentar ${accion.toLowerCase()} el accesorio.`);
        }
    });
});