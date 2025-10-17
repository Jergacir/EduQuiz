document.addEventListener('DOMContentLoaded', () => {
    const partidaId = document.body.dataset.partidaId;
    
    // --- Referencias del DOM ---
    const formatCards = document.querySelectorAll('.format-card');
    const selectAllCheckbox = document.getElementById('selectAll');
    const fieldCheckboxes = document.querySelectorAll('.fields-grid input[type="checkbox"]');
    const btnExportar = document.getElementById('btnExportar');
    const statusMessage = document.getElementById('export-status-message');

    // --- Estado Inicial ---
    let formatoSeleccionado = 'csv'; // Por defecto es CSV

    // --- Lógica para seleccionar formato ---
    formatCards.forEach(card => {
        card.addEventListener('click', () => {
            // 1. Quitar selección de todos
            formatCards.forEach(c => c.classList.remove('selected'));
            
            // 2. Marcar el clickeado
            card.classList.add('selected');
            
            // 3. Actualizar el estado
            formatoSeleccionado = card.dataset.format;
        });
    });

    // --- Lógica para seleccionar todos los campos ---
    selectAllCheckbox.addEventListener('change', (e) => {
        fieldCheckboxes.forEach(checkbox => {
            checkbox.checked = e.target.checked;
        });
    });

    // Sincronizar 'Seleccionar Todos' con el estado de los campos individuales
    fieldCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const todosSeleccionados = Array.from(fieldCheckboxes).every(cb => cb.checked);
            selectAllCheckbox.checked = todosSeleccionados;
        });
    });

    // --- Lógica del Botón Exportar ---
    btnExportar.addEventListener('click', async () => {
        // 1. Obtener campos seleccionados
        const camposSeleccionados = Array.from(fieldCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.field);
        
        if (camposSeleccionados.length === 0) {
            statusMessage.textContent = 'Por favor, selecciona al menos un campo para exportar.';
            statusMessage.style.color = 'red';
            statusMessage.classList.remove('hidden');
            return;
        }

        statusMessage.classList.add('hidden');
        btnExportar.disabled = true;
        btnExportar.innerHTML = '<i class="icon-loading"></i> Procesando...'; // Asumiendo un icono de carga

        try {
            const response = await fetch(`/api/exportar_partida/${partidaId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    formato: formatoSeleccionado,
                    campos: camposSeleccionados
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                statusMessage.textContent = data.mensaje;
                statusMessage.style.color = '#059669'; // Éxito
                statusMessage.classList.remove('hidden');

                // En una implementación real, aquí iniciarías la descarga:
                // window.location.href = data.download_url;

            } else {
                statusMessage.textContent = 'Error: ' + (data.error || 'Ocurrió un error en el servidor.');
                statusMessage.style.color = 'red';
                statusMessage.classList.remove('hidden');
            }

        } catch (error) {
            console.error('Error al exportar:', error);
            statusMessage.textContent = 'Error de conexión. Inténtalo de nuevo.';
            statusMessage.style.color = 'red';
            statusMessage.classList.remove('hidden');
        } finally {
            btnExportar.disabled = false;
            btnExportar.innerHTML = '<i class="icon-download"></i> Exportar Resultados';
        }
    });

});