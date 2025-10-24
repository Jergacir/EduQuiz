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
        if (!inventoryId) return alert('ID de inventario faltante');

        try {
            const formData = new FormData();
            formData.append('inventory_id', inventoryId);
            const response = await fetch('/api/inventario/equipar', { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok && data.success) {
                actualizarEstadoEquipado(inventoryId, data.equipada);
                // Si el servidor devuelve la nueva URL de la foto de perfil, actualizar el avatar en el header inmediatamente
                try {
                    console.log('[INV AVATAR UPDATE] response:', data);
                    const newUrl = data.url_foto_perfil || data.url_avatar;
                    if (newUrl) {
                        // Añadir cache-buster para forzar recarga del recurso (evita mostrar imagen antigua en caché)
                        const finalUrl = newUrl + (newUrl.indexOf('?') === -1 ? '?cb=' + Date.now() : '&cb=' + Date.now());
                        // Buscar todos los elementos de avatar y actualizar el src
                        document.querySelectorAll('img.profile-img').forEach(img => {
                            try {
                                if (img.getAttribute('src') !== finalUrl) img.setAttribute('src', finalUrl);
                            } catch (e) { /* noop */ }
                        });
                        // También intentar actualizar elementos que usen background-image (por si acaso)
                        document.querySelectorAll('.profile-img-bg').forEach(el => {
                            try { el.style.backgroundImage = 'url("' + finalUrl + '")'; } catch (e) {}
                        });
                    }
                } catch (e) {
                    console.warn('[INV AVATAR UPDATE] no se pudo actualizar el DOM del avatar', e);
                }
            } else {
                alert('Error: ' + (data.message || 'No se pudo cambiar el estado'));
            }
        } catch (err) {
            console.error('Error al equipar:', err);
            alert('Error en la petición. Revisa la consola.');
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
