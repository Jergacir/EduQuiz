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
});