// ======================================================
// EXPORTAR RESULTADOS - EDUQUIZ
// ======================================================

document.addEventListener('DOMContentLoaded', () => {
    const partidaId = document.body.dataset.partidaId;
    const formatCards = document.querySelectorAll('.format-card');
    const selectAllCheckbox = document.getElementById('selectAll');
    const fieldCheckboxes = document.querySelectorAll('.fields-grid input[type="checkbox"]');
    const btnExportar = document.getElementById('btnExportar');
    const statusMessage = document.getElementById('export-status-message');

    let formatoSeleccionado = 'csv';

    // Selección de formato
    formatCards.forEach(card => {
        card.addEventListener('click', () => {
            formatCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            formatoSeleccionado = card.dataset.format;
            mostrarToast(`📄 Formato seleccionado: ${formatoSeleccionado.toUpperCase()}`);
        });
    });

    // Seleccionar todos
    selectAllCheckbox.addEventListener('change', e => {
        fieldCheckboxes.forEach(cb => cb.checked = e.target.checked);
    });

    // Sincronizar el estado de "Seleccionar todos"
    fieldCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            selectAllCheckbox.checked = Array.from(fieldCheckboxes).every(c => c.checked);
        });
    });

    // Exportar
    btnExportar.addEventListener('click', async () => {
        const camposSeleccionados = Array.from(fieldCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.field);

        if (camposSeleccionados.length === 0) {
            mostrarToast('⚠️ Selecciona al menos un campo para exportar.', 'error');
            return;
        }

        btnExportar.disabled = true;
        btnExportar.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando...';

        try {
            const response = await fetch(`/api/exportar_partida/${partidaId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    formato: formatoSeleccionado,
                    campos: camposSeleccionados
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                mostrarToast('✅ Exportación completada correctamente.');
                // window.location.href = data.download_url;
            } else {
                mostrarToast('❌ Error al exportar resultados.', 'error');
            }
        } catch (error) {
            mostrarToast('🚫 Error de conexión.', 'error');
        } finally {
            btnExportar.disabled = false;
            btnExportar.innerHTML = '<i class="fa-solid fa-download"></i> Exportar Resultados';
        }
    });
});

// ======================================================
// NOTIFICACIÓN (Toast estilo EduQuiz)
// ======================================================

function mostrarToast(mensaje, tipo = 'success') {
    const toast = document.createElement('div');
    toast.className = `eduquiz-toast ${tipo}`;
    toast.textContent = mensaje;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('visible'), 100);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

const style = document.createElement('style');
style.innerHTML = `
.eduquiz-toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: #2D3047;
    color: #fff;
    padding: 12px 20px;
    border-radius: 10px;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.4s ease;
    font-weight: 600;
    z-index: 9999;
}
.eduquiz-toast.visible {
    opacity: 1;
    transform: translateY(0);
}
.eduquiz-toast.error {
    background: #d32f2f;
}
@media (max-width: 768px) {
    .eduquiz-toast {
        right: 50%;
        transform: translate(50%, 20px);
        max-width: 90%;
        text-align: center;
    }
    .eduquiz-toast.visible {
        transform: translate(50%, 0);
    }
}
`;
document.head.appendChild(style);
