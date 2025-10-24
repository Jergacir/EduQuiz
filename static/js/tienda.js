document.addEventListener('DOMContentLoaded', function () {
    console.log('[INFO] tienda.js initialized');
    // --- Referencias Comunes ---
    const btnAccesorios = document.getElementById('btn-crud-accesorios');
    const btnSkins = document.getElementById('btn-crud-skins');
    const modalAccesorio = document.getElementById('modal-accesorio');
    const modalSkin = document.getElementById('modal-skin');
    const cerrarModales = document.querySelectorAll('.cerrar-modal');

    // Si los botones no existen (usuario sin permisos), salir sin intentar bindear eventos
    if (!modalAccesorio || !modalSkin) {
        // No hay interfaces CRUD visibles; evitar errores posteriores
        console.log('[INFO] CRUD de tienda no disponible para este usuario o modal ausente.');
    }

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
                    <button type="button" class="btn-accion btn-editar" data-id="${item.id}" data-tipo="${tipo}">✏️ Editar</button>
                    <button type="button" class="btn-accion btn-eliminar" data-id="${item.id}" data-tipo="${tipo}">🗑️ Eliminar</button>
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

    if (btnAccesorios) btnAccesorios.addEventListener('click', () => abrirModal(modalAccesorio, 'accesorios'));
    if (btnSkins) btnSkins.addEventListener('click', () => abrirModal(modalSkin, 'skins'));

    cerrarModales.forEach(span => {
        span.addEventListener('click', function () {
            const modal = span.closest('.modal');
            if (!modal) return;
            const tipo = modal.id.includes('accesorio') ? 'accesorios' : 'skins';
            cerrarModal(modal, tipo);
        });
    });

    window.addEventListener('click', function (event) {
        if (modalAccesorio && event.target === modalAccesorio) cerrarModal(modalAccesorio, 'accesorios');
        if (modalSkin && event.target === modalSkin) cerrarModal(modalSkin, 'skins');
    });

    // --- Lógica de Transición de Vistas CRUD (Lista vs Formulario) ---

    function mostrarVista(tipo, vista, datos = null) {
        // Definimos el prefijo basado en el tipo para asegurar consistencia con el HTML
        let prefijo = '';
        let tipoSingular = '';

        if (tipo === 'accesorios') {
            prefijo = 'acc';
            tipoSingular = 'accesorio';
        } else if (tipo === 'skins') {
            prefijo = 'skin';
            tipoSingular = 'skin';
        } else {
            console.error(`Tipo desconocido: ${tipo}`);
            return;
        }

        const listaVista = document.getElementById(`${prefijo}-lista-vista`);
        const formVista = document.getElementById(`${prefijo}-form-vista`);

        if (!listaVista || !formVista) {
            console.error(`Error de JavaScript: No se encontró el DIV de vista para ${prefijo}.`);
            return;
        }

        const formTitulo = document.getElementById(`${prefijo}-form-titulo`);
        const formSubmitBtn = document.getElementById(`btn-${prefijo}-submit`);
        const formId = document.getElementById(`${prefijo}-id`);
        const form = document.getElementById(`form-${prefijo}`);

        if (vista === 'lista') {
            listaVista.classList.remove('oculto');
            formVista.classList.add('oculto');
            if (form) form.reset();
            cargarDatosCRUD(tipo);
        } else if (vista === 'form') {
            listaVista.classList.add('oculto');
            formVista.classList.remove('oculto');

            if (datos) {
                if (formTitulo) formTitulo.textContent = `Editar ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}: ${datos.nombre}`;
                if (formSubmitBtn) formSubmitBtn.textContent = 'Guardar Cambios';
                if (formId) formId.value = datos.id || '';

                const nombreInput = document.getElementById(`${prefijo}-nombre`);
                const urlInput = document.getElementById(`${prefijo}-url`);
                const precioInput = document.getElementById(`${prefijo}-precio`);

                if (nombreInput) nombreInput.value = datos.nombre || '';
                if (urlInput) urlInput.value = datos.url_imagen || '';
                if (precioInput) precioInput.value = datos.precio || 0;
            } else {
                if (formTitulo) formTitulo.textContent = `Agregar Nuevo ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}`;
                if (formSubmitBtn) formSubmitBtn.textContent = `Crear ${tipoSingular.charAt(0).toUpperCase() + tipoSingular.slice(1)}`;
                if (formId) formId.value = '';
                if (form) form.reset();
            }
        }
    }

    // Eventos de botones para cambiar de vista (Crear/Volver)
    const btnAccAbrir = document.getElementById('btn-acc-abrir-crear');
    const btnAccVolver = document.getElementById('btn-acc-volver-lista');
    const btnSkinAbrir = document.getElementById('btn-skin-abrir-crear');
    const btnSkinVolver = document.getElementById('btn-skin-volver-lista');

    if (btnAccAbrir) btnAccAbrir.addEventListener('click', () => mostrarVista('accesorios', 'form'));
    if (btnAccVolver) btnAccVolver.addEventListener('click', () => mostrarVista('accesorios', 'lista'));
    if (btnSkinAbrir) btnSkinAbrir.addEventListener('click', () => mostrarVista('skins', 'form'));
    if (btnSkinVolver) btnSkinVolver.addEventListener('click', () => mostrarVista('skins', 'lista'));


    // --- Lógica para Botones de Acciones (Asignación de Eventos) ---

    function asignarEventosAccion() {
        const editarBtns = document.querySelectorAll('.btn-editar');
        const eliminarBtns = document.querySelectorAll('.btn-eliminar');
        console.log('[DEBUG] asignarEventosAccion called - editarBtns:', editarBtns.length, 'eliminarBtns:', eliminarBtns.length);
        // Evento para Editar
        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', async function () {
                const id_dbg = this.getAttribute('data-id');
                const tipo_dbg = this.getAttribute('data-tipo');
                console.log('[DEBUG] btn-editar clicked', id_dbg, tipo_dbg);
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
                const id_dbg = this.getAttribute('data-id');
                const tipo_dbg = this.getAttribute('data-tipo');
                console.log('[DEBUG] btn-eliminar clicked', id_dbg, tipo_dbg);
                const id = this.getAttribute('data-id');
                const tipo = this.getAttribute('data-tipo');
                const nombre = this.closest('tr').cells[1].textContent;

                mostrarConfirmacion(
                    `⚠️ ¿Estás seguro de que quieres eliminar el ${tipo.slice(0, -1)} '${nombre}' (ID ${id})? Esta acción no se puede deshacer.`,
                    async () => {
                        if (tipo === 'accesorios') {
                            try {
                                const url = `/api/tienda/accesorios/eliminar/${id}`;
                                console.log('[DEBUG] DELETE accessory ->', url);
                                const response = await fetch(url, { method: 'POST' });
                                const data = await response.json();
                                console.log('[DEBUG] response', response.status, data);
                                if (data.success) {
                                    alert(`✅ ${data.message}`);
                                    cargarDatosCRUD(tipo);
                                    if (modalAccesorio) cerrarModal(modalAccesorio, 'accesorios');
                                } else {
                                    alert(`❌ Error al eliminar: ${data.message || JSON.stringify(data)}`);
                                }
                            } catch (error) {
                                console.error(error);
                                alert('Error al eliminar accesorio.');
                            }
                        } else {
                            try {
                                const url = `/api/tienda/skin/eliminar/${id}`;
                                console.log('[DEBUG] DELETE skin ->', url);
                                const response = await fetch(url, { method: 'POST' });
                                const data = await response.json();
                                console.log('[DEBUG] response', response.status, data);
                                if (data.success) {
                                    alert(`✅ ${data.message}`);
                                    cargarDatosCRUD(tipo);
                                    if (modalSkin) cerrarModal(modalSkin, 'skins');
                                } else {
                                    alert(`❌ Error al eliminar: ${data.message || JSON.stringify(data)}`);
                                }
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

    /// Accesorio (solo si el formulario existe)
    const formAccesorioEl = document.getElementById('form-accesorio');
    if (formAccesorioEl) {
        formAccesorioEl.addEventListener('submit', function (event) {
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
                        console.log('[DEBUG] submit accessory form ->', url);
                        for (let pair of formData.entries()) console.log('  ', pair[0], pair[1]);
                        const response = await fetch(url, { method: 'POST', body: formData });
                        const data = await response.json();
                        console.log('[DEBUG] response', response.status, data);
                        if (data.success) {
                            alert(`✅ Accesorio ${accion} con éxito. ID: ${data.id || id}`);
                            mostrarVista('accesorios', 'lista');
                            cargarDatosCRUD('accesorios');
                            if (modalAccesorio) cerrarModal(modalAccesorio, 'accesorios');
                        } else {
                            alert(`❌ Error al ${accion.toLowerCase()}: ${data.message || JSON.stringify(data)}`);
                        }
                    } catch (err) {
                        console.error(err);
                        alert(`Error al ${accion.toLowerCase()}. Revisa la consola y la pestaña Network para más detalles.`);
                    }
                }
            );
        });
    }

    // Skin
    const formSkinEl = document.getElementById('form-skin');
    if (formSkinEl) {
        formSkinEl.addEventListener('submit', function (event) {
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
                    console.log('[DEBUG] submit skin form ->', url);
                    for (let pair of formData.entries()) console.log('  ', pair[0], pair[1]);
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const data = await response.json();
                    console.log('[DEBUG] response', response.status, data);
                    if (data.success) {
                        alert(`✅ Skin ${accion} con éxito. ID: ${data.id || id}`);
                        mostrarVista('skins', 'lista');
                        cargarDatosCRUD('skins');
                        if (modalSkin) cerrarModal(modalSkin, 'skins');

                    } else {
                        alert(`❌ Error al ${accion.toLowerCase()}: ${data.message || JSON.stringify(data)}`);
                    }
                } catch (err) {
                    console.error(err);
                    alert(`Error al ${accion.toLowerCase()}. Revisa la consola y la pestaña Network para más detalles.`);
                }
            }
        );
        });
    } else {
        console.log('[INFO] form-skin no presente en esta vista, omitiendo bindings.');
    }

    // Referencias
    const modalConfirm = document.getElementById('modal-confirm');
    const modalConfirmText = document.getElementById('modal-confirm-text');
    const btnConfirmOk = document.getElementById('modal-confirm-ok');
    const btnConfirmCancel = document.getElementById('modal-confirm-cancel');

    // Result modals (success / error)
    const modalSuccess = document.getElementById('modal-success');
    const modalSuccessText = document.getElementById('modal-success-text');
    const modalSuccessTitle = document.getElementById('modal-success-title');
    const modalSuccessOk = document.getElementById('modal-success-ok');

    const modalError = document.getElementById('modal-error');
    const modalErrorText = document.getElementById('modal-error-text');
    const modalErrorTitle = document.getElementById('modal-error-title');
    const modalErrorOk = document.getElementById('modal-error-ok');

    // Helpers para mostrar/ocultar modales de resultado
    function showSuccessModal(title, text) {
        try {
            if (modalSuccessTitle) modalSuccessTitle.textContent = title || 'Éxito';
            if (modalSuccessText) modalSuccessText.textContent = text || '';
            if (modalSuccess) {
                modalSuccess.classList.remove('oculto');
                try { modalSuccess.style.display = 'flex'; } catch (e) {}
            }
        } catch (e) { console.warn('[MODAL] showSuccessModal error', e); }
    }

    function hideSuccessModal() {
        try { if (modalSuccess) { modalSuccess.classList.add('oculto'); modalSuccess.style.display = 'none'; } } catch (e) {}
    }

    function showErrorModal(title, text) {
        try {
            if (modalErrorTitle) modalErrorTitle.textContent = title || 'Error';
            if (modalErrorText) modalErrorText.textContent = text || '';
            if (modalError) {
                modalError.classList.remove('oculto');
                try { modalError.style.display = 'flex'; } catch (e) {}
            }
        } catch (e) { console.warn('[MODAL] showErrorModal error', e); }
    }

    function hideErrorModal() {
        try { if (modalError) { modalError.classList.add('oculto'); modalError.style.display = 'none'; } } catch (e) {}
    }

    // Bind cierre de modales de resultado
    try {
        if (modalSuccessOk) modalSuccessOk.addEventListener('click', hideSuccessModal);
        if (modalErrorOk) modalErrorOk.addEventListener('click', hideErrorModal);
        // Cerrar si se hace click fuera del contenido
        if (modalSuccess) modalSuccess.addEventListener('click', function (ev) { if (ev.target === modalSuccess) hideSuccessModal(); });
        if (modalError) modalError.addEventListener('click', function (ev) { if (ev.target === modalError) hideErrorModal(); });
    } catch (e) { console.warn('[MODAL] binding result modal buttons failed', e); }

    function mostrarConfirmacion(mensaje, callbackAceptar) {
    // Si no existe el modal en esta vista, usar fallback con confirm() y ejecutar callback directamente
    if (!modalConfirm || !modalConfirmText || !btnConfirmOk || !btnConfirmCancel) {
        console.warn('[WARN] modalConfirm o sus controles no están presentes, usando fallback window.confirm');
        try {
            const ok = window.confirm(mensaje);
            if (ok) {
                Promise.resolve(callbackAceptar()).catch(e => console.error('[ERROR] callbackAceptar (fallback):', e));
            }
        } catch (e) {
            console.error('[ERROR] fallback confirm failed:', e);
        }
        return;
    }

    modalConfirmText.textContent = mensaje;
    console.log('[DEBUG] mostrarConfirmacion -> show modal');
    // Forzar el estilo display para evitar reglas CSS que pongan display:none en .modal
    modalConfirm.classList.remove('oculto');
    try { modalConfirm.style.display = 'flex'; } catch (e) {}

        // Limpiar listeners anteriores (si existían, los almacenamos en propiedades para remover)
        try {
            if (btnConfirmOk._handler) btnConfirmOk.removeEventListener('click', btnConfirmOk._handler);
            if (btnConfirmCancel._handler) btnConfirmCancel.removeEventListener('click', btnConfirmCancel._handler);
        } catch (e) {
            // ignore
        }

        // Para diagnóstico: registrar clicks dentro del modal
        try {
            if (!modalConfirm._diagAttached) {
                modalConfirm.addEventListener('click', function (ev) {
                    console.log('[DEBUG] modal click target:', ev.target && ev.target.id ? ev.target.id : ev.target);
                });
                modalConfirm._diagAttached = true;
            }
        } catch (e) { console.warn('[WARN] no se pudo agregar diagnostic listener en modalConfirm', e); }

        if (!btnConfirmOk || !btnConfirmCancel) {
            console.warn('[WARN] botones de confirmación no encontrados, ejecutando callback directamente');
            try {
                Promise.resolve(callbackAceptar()).catch(e => console.error('[ERROR] callbackAceptar (direct):', e));
            } catch (e) {
                console.error('[ERROR] callbackAceptar threw (direct):', e);
            }
            return;
        }

        // Cuando se acepta (usamos addEventListener y guardamos el handler para poder removerlo luego)
        const okHandler = async function () {
            console.log('[DEBUG] modal-confirm OK clicked');
                try {
                    await Promise.resolve(callbackAceptar());
                    console.log('[DEBUG] callbackAceptar resolved');
                } catch (e) {
                    console.error('[ERROR] callbackAceptar threw:', e);
                } finally {
                    // Ocultar modal
                    try { modalConfirm.style.display = 'none'; } catch (e) {}
                    modalConfirm.classList.add('oculto');
                }
        };
        btnConfirmOk.addEventListener('click', okHandler);
        btnConfirmOk._handler = okHandler;

        // Cuando se cancela
        const cancelHandler = function () {
            console.log('[DEBUG] modal-confirm Cancel clicked');
            try { modalConfirm.style.display = 'none'; } catch (e) {}
            modalConfirm.classList.add('oculto');
        };
        btnConfirmCancel.addEventListener('click', cancelHandler);
        btnConfirmCancel._handler = cancelHandler;
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
            <img src="${imagen}" alt="${nombre}" onerror="this.onerror=null;this.src='../static/img/default.png';">
        </div>
        <p class="item-nombre">${nombre}</p>
        <button class="btn-comprar">
            <i class="icono">🪙</i> ${precio}
        </button>
    `;

        return card;
    }

    // Handler global para clicks en botones de comprar (incluye botones renderizados en servidor)
    document.body.addEventListener('click', async function (ev) {
        const btn = ev.target.closest && ev.target.closest('.btn-comprar');
        if (!btn) return;
        // Si ya está marcado como adquirido, no hacer nada
        if (btn.classList.contains('adquirido') || btn.disabled) return;

        const tipo = btn.getAttribute('data-tipo');
        const id = btn.getAttribute('data-id');
        if (!tipo || !id) {
            console.warn('[tienda] botón comprar sin data-tipo/data-id');
            return;
        }

        // Confirmación usando el modal estilo app (mostrarConfirmacion está implementado más arriba)
        mostrarConfirmacion(
            `⚠️ ¿Deseas comprar este ítem por ${btn.getAttribute('data-precio') || ''} monedas?`,
            async () => {
                try {
                    const payload = { tipo: tipo, id: id };
                    const response = await fetch('/api/tienda/comprar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        showErrorModal('Error de compra', data.message || 'No se pudo completar la compra.');
                        return;
                    }

                    if (data.adquirido) {
                        // Actualizar botón a estado 'Adquirido'
                        btn.classList.add('adquirido');
                        btn.disabled = true;
                        btn.innerHTML = '<i class="icono">🪙</i> Adquirido';

                        // Actualizar saldo mostrado si viene en la respuesta
                        if (data.nuevo_saldo !== undefined) {
                            const saldoEl = document.getElementById('cant-monedas-display');
                            if (saldoEl) saldoEl.textContent = data.nuevo_saldo;
                        }

                        // Mostrar modal de éxito
                        try { showSuccessModal('Compra realizada', 'Tu compra se realizó correctamente.'); } catch (e) { console.warn(e); }
                    } else {
                        showErrorModal('Compra', data.message || 'Respuesta inesperada del servidor.');
                    }

                } catch (err) {
                    console.error('Error realizando compra:', err);
                    showErrorModal('Error de red', 'Error de red al intentar la compra.');
                }
            }
        );
    });

    // --- Inicialización del slider de precio (noUiSlider preferido, fallback al doble input) ---
    (function initPriceSlider() {
    // --- Constantes de Configuración ---
    const MIN_PRICE = 0;
    const MAX_PRICE = 2000;
    const DEFAULT_START_PRICE = 0;
    const DEFAULT_END_PRICE = 500;
    const SUBMIT_DEBOUNCE_MS = 300; // 300ms de espera antes de enviar el form

    // --- Elementos del DOM ---
    const priceSliderEl = document.getElementById('price-slider');
    const minDisplay = document.getElementById('range-min-display');
    const maxDisplay = document.getElementById('range-max-display');
    const minInput = document.getElementById('min_price_input');
    const maxInput = document.getElementById('max_price_input');
    const filtersForm = document.getElementById('filters-form');

    // --- Funciones Helper ---

    /**
     * Helper para parsear valores iniciales desde inputs (si vienen por querystring)
     */
    const parseInitial = (el, fallback) => {
        if (!el) return fallback;
        const v = parseInt(el.value, 10);
        return isNaN(v) ? fallback : v;
    };

    /**
     * Helper Debounce: Retrasa la ejecución de una función
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Función para enviar el formulario
     */
    const submitFiltersForm = () => {
        try {
            if (filtersForm) filtersForm.submit();
        } catch (e) {
            console.warn('No se pudo enviar el formulario automáticamente.', e);
        }
    };
    
    // Función de envío con debounce
    const debouncedSubmit = debounce(submitFiltersForm, SUBMIT_DEBOUNCE_MS);

    /**
     * Formatea el valor máximo para mostrar (ej: 1000+)
     */
    const formatMaxDisplay = (value) => {
        return (value >= MAX_PRICE) ? `${value}+` : value;
    };

    // --- Lógica Principal ---

    // 1. Intento con noUiSlider (Librería)
    if (window.noUiSlider && priceSliderEl) {
        try {
            const startMin = parseInitial(minInput, DEFAULT_START_PRICE);
            const startMax = parseInitial(maxInput, DEFAULT_END_PRICE);

            if (priceSliderEl.noUiSlider) {
                priceSliderEl.noUiSlider.destroy();
            }

            noUiSlider.create(priceSliderEl, {
                start: [startMin, startMax],
                connect: true,
                // Se desactivan los tooltips para evitar números flotantes desalineados sobre el slider
                tooltips: false,
                range: { min: MIN_PRICE, max: MAX_PRICE },
                step: 1,
                format: {
                    to: v => Math.round(v),
                    from: v => Number(v)
                }
            });

            // Evento 'update' (mientras se mueve)
            priceSliderEl.noUiSlider.on('update', function (values) {
                const a = Math.round(values[0]);
                const b = Math.round(values[1]);
                if (minDisplay) minDisplay.textContent = a;
                if (maxDisplay) maxDisplay.textContent = formatMaxDisplay(b);
                if (minInput) minInput.value = a;
                if (maxInput) maxInput.value = b;
            });

            // Evento 'change' (al soltar) -> Envía formulario con debounce
            priceSliderEl.noUiSlider.on('change', debouncedSubmit);

        } catch (e) {
            console.warn('[WARN] noUiSlider init failed, falling back to native ranges', e);
        }
        return; // Termina si noUiSlider se inicializó
    }

    // 2. Fallback (Inputs Nativos)
    try {
        const rangeMin = document.getElementById('range-min');
        const rangeMax = document.getElementById('range-max');
        const container = rangeMin ? rangeMin.parentElement : null;

        if (!rangeMin || !rangeMax || !minDisplay || !maxDisplay || !minInput || !maxInput || !container) {
            return; // Salir si faltan elementos
        }

        // Valores iniciales coherentes
        let minVal = parseInitial(minInput, parseInt(rangeMin.value || DEFAULT_START_PRICE, 10));
        let maxVal = parseInitial(maxInput, parseInt(rangeMax.value || DEFAULT_END_PRICE, 10));
        if (minVal > maxVal) [minVal, maxVal] = [maxVal, minVal]; // Swap

        // Settear valores iniciales
        rangeMin.value = minVal;
        rangeMax.value = maxVal;
        rangeMin.min = MIN_PRICE;
        rangeMin.max = MAX_PRICE;
        rangeMax.min = MIN_PRICE;
        rangeMax.max = MAX_PRICE;

        const updateUI = () => {
            let a = parseInt(rangeMin.value, 10);
            let b = parseInt(rangeMax.value, 10);

            // Asegurar que min no pase a max y viceversa
            if (a > b) {
                if (document.activeElement === rangeMin) {
                    rangeMin.value = b;
                    a = b;
                } else {
                    rangeMax.value = a;
                    b = a;
                }
            }

            // Actualizar displays e inputs hidden
            minDisplay.textContent = a;
            maxDisplay.textContent = formatMaxDisplay(b);
            minInput.value = a;
            maxInput.value = b;

            // *** MEJORA: Actualizar variables CSS en lugar de style.background ***
            const rangeWidth = MAX_PRICE - MIN_PRICE;
            const percentA = ((a - MIN_PRICE) / rangeWidth) * 100;
            const percentB = ((b - MIN_PRICE) / rangeWidth) * 100;

            container.style.setProperty('--min-percent', `${percentA}%`);
            container.style.setProperty('--max-percent', `${percentB}%`);
        };

        // Listeners para 'input' (actualiza UI mientras se mueve)
        rangeMin.addEventListener('input', updateUI);
        rangeMax.addEventListener('input', updateUI);
        
        // Listeners para 'change' (envía form al soltar)
        rangeMin.addEventListener('change', debouncedSubmit);
        rangeMax.addEventListener('change', debouncedSubmit);

        // Inicializar UI
        updateUI();

    } catch (e) {
        console.warn('[WARN] slider fallback failed', e);
    }
})();

    // --- Auto-submit para selects de filtros (tienda e inventario) ---
    (function enableAutoSubmitFilters() {
        try {
            // Tienda
            const filtersForm = document.getElementById('filters-form');
            if (filtersForm) {
                const selectCat = filtersForm.querySelector('select[name="categoria"]');
                const btnFiltrar = filtersForm.querySelector('.btn-filtrar');
                if (selectCat) {
                    selectCat.addEventListener('change', function (ev) {
                        console.log('[AUTO-FILTER] tienda select categoria changed ->', ev.target.value);
                        try {
                            if (typeof filtersForm.requestSubmit === 'function') filtersForm.requestSubmit();
                            else filtersForm.submit();
                        } catch (e) {
                            console.warn('No se pudo enviar filters-form automáticamente', e);
                            // Fallback: reconstruir querystring mínimo
                            try {
                                const val = encodeURIComponent(ev.target.value || '');
                                const action = filtersForm.getAttribute('action') || window.location.pathname;
                                window.location.href = action + (action.includes('?') ? '&' : '?') + 'categoria=' + val;
                            } catch (e2) { console.warn('Fallback de redirección falló', e2); }
                        }
                    });
                }
                // Ocultar el botón si existe (no es necesario ahora)
                if (btnFiltrar) btnFiltrar.style.display = 'none';
            }

            // Inventario
            const filtersFormInv = document.getElementById('filters-form-inv');
            if (filtersFormInv) {
                const selectCatInv = filtersFormInv.querySelector('select[name="categoria"]');
                const btnFiltrarInv = filtersFormInv.querySelector('.btn-filtrar');
                if (selectCatInv) {
                    selectCatInv.addEventListener('change', function (ev) {
                        console.log('[AUTO-FILTER] inventario select categoria changed ->', ev.target.value);
                        try {
                            if (typeof filtersFormInv.requestSubmit === 'function') filtersFormInv.requestSubmit();
                            else filtersFormInv.submit();
                        } catch (e) {
                            console.warn('No se pudo enviar filters-form-inv automáticamente', e);
                            try {
                                const val = encodeURIComponent(ev.target.value || '');
                                const action = filtersFormInv.getAttribute('action') || window.location.pathname;
                                window.location.href = action + (action.includes('?') ? '&' : '?') + 'categoria=' + val;
                            } catch (e2) { console.warn('Fallback de redirección (inv) falló', e2); }
                        }
                    });
                }
                if (btnFiltrarInv) btnFiltrarInv.style.display = 'none';
            }
        } catch (e) { console.warn('[WARN] enableAutoSubmitFilters failed', e); }
    })();
});