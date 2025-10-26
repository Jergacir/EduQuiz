document.addEventListener('DOMContentLoaded', () => {
    const partidaId = document.body.dataset.partidaId;
    const formatCards = document.querySelectorAll('.format-card');
    const selectAllCheckbox = document.getElementById('selectAll');
    const fieldCheckboxes = document.querySelectorAll('.fields-grid input[type="checkbox"]');
    const btnExportar = document.getElementById('btnExportar');
    const emailInput = document.getElementById('emailInput');
    const enviarPorEmailCheckbox = document.getElementById('enviarPorEmail');
    const emailStatusBox = document.getElementById('emailStatusBox');

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

    // Seleccionar todos los campos
    selectAllCheckbox.addEventListener('change', e => {
        fieldCheckboxes.forEach(cb => cb.checked = e.target.checked);
    });

    // Mejorar feedback visual
    emailInput.addEventListener('blur', () => {
        const email = emailInput.value.trim();
        
        if (!email) return; // No validar si está vacío
        
        if (!validarEmail(email)) {
            mostrarToast('⚠️ Email inválido. Usa formato válido (ej: profesor@usat.edu.pe)', 'error');
            emailInput.style.borderColor = '#dc3545';
        } else {
            emailInput.style.borderColor = '#28a745'; // Verde para indicar válido
            
            // Detectar tipo de correo y mostrar ícono
            if (email.includes('@gmail.com')) {
                mostrarIconoProveedor('gmail');
            } else if (email.includes('@usat.edu.pe') || email.includes('@usat.pe')) {
                mostrarIconoProveedor('outlook');
            }
        }
    });

    // EXPORTAR
    btnExportar.addEventListener('click', async () => {
        const camposSeleccionados = Array.from(fieldCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.field);

        if (camposSeleccionados.length === 0) {
            mostrarToast('⚠️ Selecciona al menos un campo', 'error');
            return;
        }

        btnExportar.disabled = true;
        btnExportar.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando...';

        const payload = {
            formato: formatoSeleccionado,
            campos: camposSeleccionados
        };

        // Si el checkbox está marcado y hay email válido
        if (enviarPorEmailCheckbox.checked) {
            const email = emailInput.value.trim();
            
            if (!email || !validarEmail(email)) {
                mostrarToast('⚠️ Ingresa un email válido primero', 'error');
                btnExportar.disabled = false;
                btnExportar.innerHTML = '<i class="fa-solid fa-download"></i> Exportar Resultados';
                return;
            }
            
            payload.enviar_por_email = true;
            payload.email_destinatario = email;
        }

        try {
            const response = await fetch(`/api/exportar_partida/${partidaId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const contentType = response.headers.get('Content-Type') || '';

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text);
            }

            // Si es JSON (se envió por email)
            if (contentType.includes('application/json')) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    emailStatusBox.innerHTML = `
                        <div style="color: #28a745;">
                            <i class="fa-solid fa-check-circle"></i>
                            <strong>¡Listo!</strong> Revisa tu bandeja de entrada en: <strong>${payload.email_destinatario}</strong>
                        </div>
                    `;
                    emailStatusBox.style.display = 'block';
                    mostrarToast('✅ Email enviado correctamente');
                    
                    // Opción para abrir el link directamente
                    if (data.drive_url && confirm('¿Deseas abrir el archivo ahora?')) {
                        window.open(data.drive_url, '_blank');
                    }
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            } 
            // Si es descarga directa (blob)
            else {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `resultados_partida_${partidaId}.${formatoSeleccionado === 'excel' ? 'xlsx' : formatoSeleccionado}`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                mostrarToast('✅ Archivo descargado');
            }

        } catch (error) {
            console.error('Error:', error);
            mostrarToast(`❌ ${error.message}`, 'error');
        } finally {
            btnExportar.disabled = false;
            btnExportar.innerHTML = '<i class="fa-solid fa-download"></i> Exportar Resultados';
        }
    });
});

function mostrarIconoProveedor(tipo) {
    const statusBox = document.getElementById('emailStatusBox');
    const iconos = {
        'gmail': '<i class="fa-brands fa-google" style="color: #EA4335;"></i> Gmail detectado',
        'outlook': '<i class="fa-brands fa-microsoft" style="color: #0078D4;"></i> Outlook detectado'
    };
    
    statusBox.innerHTML = `<div style="color: #28a745;">${iconos[tipo]}</div>`;
    statusBox.style.display = 'block';
}

function validarEmail(email) {
    // Validación básica de formato
    const formatoValido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    
    // Dominios permitidos (opcional, para restricción institucional)
    const dominiosPermitidos = ['@gmail.com', '@usat.edu.pe', '@usat.pe'];
    const tienesDominioPermitido = dominiosPermitidos.some(dominio => email.endsWith(dominio));
    
    // Si quieres aceptar CUALQUIER email válido, solo usa formatoValido
    // Si quieres restringir a dominios institucionales, usa ambas condiciones
    return formatoValido; // O: formatoValido && tienesDominioPermitido
}

// Toast de notificaciones
function mostrarToast(mensaje, tipo = 'success') {
    const toast = document.createElement('div');
    toast.className = `eduquiz-toast ${tipo}`;
    toast.textContent = mensaje;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('visible'), 100);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ======================================================
// ESTILOS
// ======================================================

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
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.eduquiz-toast.visible {
    opacity: 1;
    transform: translateY(0);
}

.eduquiz-toast.error {
    background: #dc3545;
}

.eduquiz-toast.info {
    background: #17a2b8;
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