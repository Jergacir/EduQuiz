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
        if (tipo) {
            mostrarVista(tipo, 'lista');
            actualizarCards(tipo); // 🔥 recargar los cards de la tienda
        }
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
                } else {
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

                mostrarConfirmacion(
                    `⚠️ ¿Estás seguro de que quieres eliminar el ${tipo.slice(0, -1)} '${nombre}' (ID ${id})? Esta acción no se puede deshacer.`,
                    async () => {
                        if (tipo === 'accesorios') {
                            try {
                                const response = await fetch(`/api/tienda/accesorios/eliminar/${id}`, { method: 'POST' });
                                const data = await response.json();
                                if (data.success) {
                                    alert(`✅ ${data.message}`);
                                    cargarDatosCRUD(tipo);
                                     cerrarModal(modalAccesorio, 'accesorios');
                                } else alert(`❌ Error al eliminar: ${data.message}`);
                            } catch (error) {
                                console.error(error);
                                alert('Error al eliminar accesorio.');
                            }
                        } else {
                            try {
                                const response = await fetch(`/api/tienda/skin/eliminar/${id}`, { method: 'POST' });
                                const data = await response.json();
                                if (data.success) {
                                    alert(`✅ ${data.message}`);
                                    cargarDatosCRUD(tipo);
                                     cerrarModal(modalAccesorio, 'skins');
                                } else alert(`❌ Error al eliminar: ${data.message}`);
                            } catch (error) {
                                console.error(error);
                                alert('Error al eliminar skin.');
                            }
                        }
                    }
                );
            });
        });
    }

    /// Accesorio
    document.getElementById('form-accesorio').addEventListener('submit', function (event) {
        event.preventDefault();
        const form = event.target;
        const id = document.getElementById('acc-id').value;
        const formData = new FormData(form);
        const accion = id ? 'Actualizar' : 'Crear';
        const url = id ? `/api/tienda/accesorios/editar/${id}` : '/api/tienda/accesorios/crear';

        mostrarConfirmacion(
            `⚠️ ¿Deseas ${accion.toLowerCase()} este accesorio?`,
            async () => {
                try {
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const data = await response.json();
                    if (data.success) {
                        alert(`✅ Accesorio ${accion} con éxito. ID: ${data.accesorio_id || id}`);
                        mostrarVista('accesorios', 'lista');
                        cargarDatosCRUD('accesorios');
                         cerrarModal(modalAccesorio, 'accesorios');
                    } else {
                        alert(`❌ Error al ${accion.toLowerCase()}: ${data.message}`);
                    }
                } catch (err) {
                    console.error(err);
                    alert(`Error al ${accion.toLowerCase()}.`);
                }
            }
        );
    });

    // Skin
    document.getElementById('form-skin').addEventListener('submit', function (event) {
        event.preventDefault();
        const form = event.target;
        const id = document.getElementById('skin-id').value;
        const formData = new FormData(form);
        const accion = id ? 'Actualizar' : 'Crear';
        const url = id ? `/api/tienda/skin/editar/${id}` : '/api/tienda/skin/crear';

        mostrarConfirmacion(
            `⚠️ ¿Deseas ${accion.toLowerCase()} este skin?`,
            async () => {
                try {
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const data = await response.json();
                    if (data.success) {
                        alert(`✅ Skin ${accion} con éxito. ID: ${data.skin_id || id}`);
                        mostrarVista('skins', 'lista');
                        cargarDatosCRUD('skins');
                        cerrarModal(modalAccesorio, 'skins');

                    } else {
                        alert(`❌ Error al ${accion.toLowerCase()}: ${data.message}`);
                    }
                } catch (err) {
                    console.error(err);
                    alert(`Error al ${accion.toLowerCase()}.`);
                }
            }
        );
    });

    // Referencias
    const modalConfirm = document.getElementById('modal-confirm');
    const modalConfirmText = document.getElementById('modal-confirm-text');
    const btnConfirmOk = document.getElementById('modal-confirm-ok');
    const btnConfirmCancel = document.getElementById('modal-confirm-cancel');

    function mostrarConfirmacion(mensaje, callbackAceptar) {
        modalConfirmText.textContent = mensaje;
        modalConfirm.classList.remove('oculto');

        // Limpiar listeners anteriores
        btnConfirmOk.onclick = null;
        btnConfirmCancel.onclick = null;

        // Cuando se acepta
        btnConfirmOk.onclick = () => {
            callbackAceptar();
            modalConfirm.classList.add('oculto');
        };

        // Cuando se cancela
        btnConfirmCancel.onclick = () => {
            modalConfirm.classList.add('oculto');
        };
    }


    async function actualizarCards(tipo) {
        const contenedor = tipo === 'skins'
            ? document.getElementById('skins-container')
            : document.getElementById('accesorios-container');

        try {
            // Llamada limpia, sin caché
            const response = await fetch(`/api/tienda/${tipo}?_=${Date.now()}`, { cache: 'no-store' });
            if (!response.ok) throw new Error('Error al obtener datos');
            const data = await response.json();

            // 🔥 Limpiar todo antes de volver a pintar
            contenedor.innerHTML = '';

            if (data.length === 0) {
                contenedor.innerHTML = `<p class="text-gray-500 text-center">No hay ${tipo} disponibles.</p>`;
                return;
            }

            // 🔁 Volver a crear todos los cards con los nuevos datos
            data.forEach(item => {
                const card = crearCard(item, tipo);
                contenedor.appendChild(card);
            });

            console.log(`Datos recibidos de ${tipo}:`, data);

        } catch (err) {
            console.error(`Error al actualizar ${tipo}:`, err);
        }
    }

    function crearCard(item, tipo) {
        const card = document.createElement('div');
        card.className = 'item-card';

        // Colores diferentes para skins y accesorios (como en tu HTML original)
        const fondo = tipo === 'skins' ? '#cce5ff' : '#d1e7dd';

        const imagen = item.url_imagen || item.imagen_url || '../static/img/default.png';
        const nombre = item.nombre || 'Sin nombre';
        const precio = item.precio || 0;

        card.innerHTML = `
        <div class="item-imagen" style="background-color: ${fondo};">
            <img src="${imagen}" alt="${nombre}">
        </div>
        <p class="item-nombre">${nombre}</p>
        <button class="btn-comprar">
            <i class="icono">🪙</i> ${precio}
        </button>
    `;

        return card;
    }

});