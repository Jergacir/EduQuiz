// JS para tabs de inventario (accesorios/skins)
document.addEventListener('DOMContentLoaded', function() {
    const tabAccesorios = document.getElementById('tab-accesorios');
    const tabSkins = document.getElementById('tab-skins');
    const accesoriosSection = document.getElementById('accesorios-section');
    const skinsSection = document.getElementById('skins-section');
    if (tabAccesorios && tabSkins && accesoriosSection && skinsSection) {
        tabAccesorios.addEventListener('click', function() {
            tabAccesorios.classList.add('active');
            tabSkins.classList.remove('active');
            accesoriosSection.style.display = '';
            skinsSection.style.display = 'none';
            tabAccesorios.style.background = '#0d9488';
            tabSkins.style.background = '#fff';
        });
        tabSkins.addEventListener('click', function() {
            tabSkins.classList.add('active');
            tabAccesorios.classList.remove('active');
            accesoriosSection.style.display = 'none';
            skinsSection.style.display = '';
            tabSkins.style.background = '#0d9488';
            tabAccesorios.style.background = '#fff';
        });
    }

    // Manejar equipamiento: delegación de eventos en el contenedor
    function actualizarEstadoEquipado(inventoryId, equipada) {
        // actualizar todos los botones dentro del contenedor
        document.querySelectorAll(`[data-inventory-id]`).forEach(el => {
            const btn = el.querySelector('.btn-equipar');
            if (!btn) return;
            const id = btn.getAttribute('data-inventory-id');
            // Si este botón corresponde a la skin que cambió de estado
            if (String(id) === String(inventoryId)) {
                btn.textContent = equipada ? 'Equipada' : 'Equipar';
                btn.setAttribute('aria-pressed', equipada ? 'true' : 'false');
                // Deshabilitar el botón si la skin quedó equipada, habilitar si fue des-equipada
                try {
                    btn.disabled = equipada ? true : false;
                } catch (e) { /* noop */ }
                // Añadir clase visual para indicar estado equipado (fallback: también ajustar estilos inline)
                if (equipada) {
                    btn.classList.add('equipped');
                    try { btn.style.backgroundColor = '#0d9488'; btn.style.color = '#fff'; } catch (e) {}
                } else {
                    btn.classList.remove('equipped');
                    try { btn.style.backgroundColor = ''; btn.style.color = ''; } catch (e) {}
                }
            } else {
                // Si es otra skin y se equipó una skin nueva, desmarcar y asegurarse de que esté habilitada
                if (btn.getAttribute('data-tipo') === 'skin' && equipada) {
                    btn.textContent = 'Equipar';
                    btn.setAttribute('aria-pressed', 'false');
                    try { btn.disabled = false; } catch (e) {}
                    btn.classList.remove('equipped');
                    try { btn.style.backgroundColor = ''; btn.style.color = ''; } catch (e) {}
                }
            }
        });
    }

    document.body.addEventListener('click', async function (ev) {
        const btn = ev.target.closest && ev.target.closest('.btn-equipar');
        if (!btn) return;
        ev.preventDefault();
        const inventoryId = btn.getAttribute('data-inventory-id');
        if (!inventoryId) {
            try {
                if (typeof window.showModal === 'function') window.showModal('Error', 'ID de inventario faltante');
                else if (window.alert) window.alert('ID de inventario faltante');
            } catch (e) { console.warn('notify failed', e); if (window.alert) window.alert('ID de inventario faltante'); }
            return;
        }

        try {
            const formData = new FormData();
            formData.append('inventory_id', inventoryId);
            const response = await fetch('/api/inventario/equipar', { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok && data.success) {
                actualizarEstadoEquipado(inventoryId, data.equipada);

                // Mostrar modal cuando la skin ha sido equipada
                try {
                    const tipo = btn.getAttribute('data-tipo');
                    if (tipo === 'skin' && data.equipada) {
                        const title = 'Skin equipada';
                        const message = 'Has equipado la skin correctamente.';
                        if (typeof window.showModal === 'function') {
                            // ui_modal.js showModal(title, message, options)
                            try { window.showModal(title, message, { okText: 'Aceptar' }); } catch (e) { alert(message); }
                        } else {
                            alert(message);
                        }
                    }
                } catch (e) { console.warn('No se pudo mostrar modal de skin equipada', e); }

                // No actualizamos el avatar del header desde aquí: el usuario puede mantener su foto de perfil
                // separada de las skins. El backend actualiza solo `url_avatar` en sesión/BD si es necesario,
                // pero no forzamos cambios visuales en el header desde el cliente para respetar la UX.
            } else {
                const msg = 'Error: ' + (data.message || 'No se pudo cambiar el estado');
                try {
                    if (typeof window.showModal === 'function') window.showModal('Error', msg);
                    else if (window.alert) window.alert(msg);
                } catch (e) { console.warn('notify failed', e); if (window.alert) window.alert(msg); }
            }
        } catch (err) {
            console.error('Error al equipar:', err);
            try {
                if (typeof window.showModal === 'function') window.showModal('Error', 'Error en la petición. Revisa la consola.');
                else if (window.alert) window.alert('Error en la petición. Revisa la consola.');
            } catch (e) { console.warn('notify failed', e); if (window.alert) window.alert('Error en la petición. Revisa la consola.'); }
        }
    });

    // --- Auto-submit del combo de categoría en Inventario ---
    try {
        const filtersFormInv = document.getElementById('filters-form-inv');
        if (filtersFormInv) {
            const selectCatInv = filtersFormInv.querySelector('select[name="categoria"]');
            if (selectCatInv) {
                selectCatInv.addEventListener('change', function (ev) {
                    console.log('[INV AUTO-FILTER] categoria changed ->', ev.target.value);
                    try {
                        if (typeof filtersFormInv.requestSubmit === 'function') filtersFormInv.requestSubmit();
                        else filtersFormInv.submit();
                    } catch (e) {
                        console.warn('[INV AUTO-FILTER] submit failed, redirecting fallback', e);
                        try {
                            const val = encodeURIComponent(ev.target.value || '');
                            const action = filtersFormInv.getAttribute('action') || window.location.pathname;
                            // preserve existing query params except categoria
                            const url = new URL(action, window.location.origin);
                            // merge existing params from current location
                            window.location.href = url.pathname + (url.search ? url.search + '&' : '?') + 'categoria=' + val;
                        } catch (e2) { console.warn('[INV AUTO-FILTER] fallback redirect failed', e2); }
                    }
                });
            }
        }
    } catch (e) { console.warn('[INV AUTO-FILTER] init failed', e); }
});
