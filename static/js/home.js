document.addEventListener('DOMContentLoaded', function() {
    const logoutLink = document.getElementById('btn-cerrar-sesion');

    if (logoutLink) {
        // Captura el evento click en el enlace de cerrar sesión
        logoutLink.addEventListener('click', function(event) {
            // 1. Previene la navegación inmediata del enlace
            event.preventDefault(); 
            
            // 2. Muestra la ventana de confirmación (el 'confirm' que solicitaste)
            // NOTA: Usamos window.confirm() aquí para la confirmación simple.
            const confirmacion = window.confirm("¿Estás seguro de que quieres cerrar la sesión?");
            
            // 3. Si el usuario presiona Aceptar (true), navega a la URL
            if (confirmacion) {
                window.location.href = logoutLink.href;
            }
            // Si el usuario presiona Cancelar (false), el script termina y no pasa nada.
        });
    }

    // Delegación: escuchar clicks en botones Obtener
        document.body.addEventListener('click', async function (e) {
            var btn = e.target.closest('.btn-get');
            if (!btn) return;
            e.preventDefault();
            var id = btn.getAttribute('data-id');
            if (!id) return;

            try {
                var resp = await fetch('/api/cuestionarios/clone/' + encodeURIComponent(id), {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                var data = null;
                try { data = await resp.json(); } catch (err) { /* ignore JSON parse error */ }

                if (resp.ok && data && data.status === 'ok') {
                    showCloneModal('¡Listo!', 'Se ha clonado el cuestionario en tu cuenta.');
                } else if (resp.status === 401) {
                    // no autorizado -> pedir login
                    showCloneModal('No autorizado', 'Debes iniciar sesión para clonar el cuestionario. Serás redirigido al login.', true, '{{ url_for("auth.frm_login") }}');
                } else {
                    var msg = (data && (data.error || data.message)) || 'No se pudo clonar el cuestionario.';
                    showCloneModal('Error', msg);
                }
            } catch (err) {
                console.error('Error clonando cuestionario:', err);
                showCloneModal('Error de conexión', 'No se pudo conectar al servidor. Intenta nuevamente.');
            }
        });

        function showCloneModal(title, message, redirect, url) {
            var modal = document.getElementById('clone-modal');
            if (!modal) return;
            document.getElementById('clone-modal-title').textContent = title || 'Información';
            document.getElementById('clone-modal-msg').textContent = message || '';
            var viewLink = document.getElementById('clone-modal-view');
            var closeBtn = document.getElementById('clone-modal-close');
            // mostrar modal
            modal.classList.remove('hidden');
            modal.setAttribute('aria-hidden', 'false');

            function cleanup() {
                modal.classList.add('hidden');
                modal.setAttribute('aria-hidden', 'true');
                closeBtn.removeEventListener('click', onClose);
            }

            function onClose(e) {
                cleanup();
                if (redirect && url) window.location.href = url;
            }

            closeBtn.addEventListener('click', onClose);
            // Si el usuario pulsa ver, redirige inmediatamente
            viewLink.addEventListener('click', function () { cleanup(); });
        }
});