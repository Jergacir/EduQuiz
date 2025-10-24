// ======================================================
// EXPORTAR RESULTADOS CON GOOGLE DRIVE - EDUQUIZ
// Versión con autenticación manual de Gmail
// ======================================================

document.addEventListener('DOMContentLoaded', () => {
    const partidaId = document.body.dataset.partidaId;
    const formatCards = document.querySelectorAll('.format-card');
    const selectAllCheckbox = document.getElementById('selectAll');
    const fieldCheckboxes = document.querySelectorAll('.fields-grid input[type="checkbox"]');
    const btnExportar = document.getElementById('btnExportar');
    const gmailInput = document.getElementById('gmailInput');
    const subirADriveCheckbox = document.getElementById('subirADrive');
    const driveStatusBox = document.getElementById('driveStatusBox');

    let formatoSeleccionado = 'csv';
    let googleAccessToken = null;
    let googleUserEmail = null;

    // ===== SELECCIÓN DE FORMATO =====
    formatCards.forEach(card => {
        card.addEventListener('click', () => {
            formatCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            formatoSeleccionado = card.dataset.format;
            mostrarToast(`📄 Formato seleccionado: ${formatoSeleccionado.toUpperCase()}`);
        });
    });

    // ===== SELECCIONAR TODOS =====
    selectAllCheckbox.addEventListener('change', e => {
        fieldCheckboxes.forEach(cb => cb.checked = e.target.checked);
    });

    fieldCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            selectAllCheckbox.checked = Array.from(fieldCheckboxes).every(c => c.checked);
        });
    });

    // ===== VALIDAR EMAIL DE GMAIL =====
    gmailInput.addEventListener('blur', () => {
        const email = gmailInput.value.trim();
        if (email && !email.endsWith('@gmail.com')) {
            mostrarToast('⚠️ Debe ser un correo @gmail.com', 'error');
            gmailInput.style.borderColor = '#dc3545';
        } else {
            gmailInput.style.borderColor = '#ced4da';
        }
    });

    // ===== CUANDO MARCA EL CHECKBOX DE DRIVE =====
    subirADriveCheckbox.addEventListener('change', async (e) => {
        if (e.target.checked) {
            const email = gmailInput.value.trim();

            if (!email) {
                mostrarToast('⚠️ Ingresa tu correo de Gmail primero', 'error');
                e.target.checked = false;
                gmailInput.focus();
                return;
            }

            if (!email.endsWith('@gmail.com')) {
                mostrarToast('⚠️ Debe ser una cuenta @gmail.com', 'error');
                e.target.checked = false;
                gmailInput.focus();
                return;
            }

            // Autenticar con Google
            await autenticarConGoogle(email);
        } else {
            // Desconectar
            googleAccessToken = null;
            googleUserEmail = null;
            driveStatusBox.style.display = 'none';
        }
    });

    // ===== EXPORTAR =====
    btnExportar.addEventListener('click', async () => {
        const camposSeleccionados = Array.from(fieldCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.field);

        if (camposSeleccionados.length === 0) {
            mostrarToast('⚠️ Selecciona al menos un campo para exportar.', 'error');
            return;
        }

        btnExportar.disabled = true;
        btnExportar.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando archivo...';

        try {
            const payload = {
                formato: formatoSeleccionado,
                campos: camposSeleccionados
            };

            // Si está marcado para subir a Drive y hay token
            if (subirADriveCheckbox.checked) {
                if (googleAccessToken) {
                    payload.subir_a_drive = true;
                    payload.drive_tipo = 'google_drive';
                    payload.access_token = googleAccessToken;
                    payload.user_email = googleUserEmail;
                } else {
                    mostrarToast('⚠️ Conéctate a Google Drive primero', 'error');
                    btnExportar.disabled = false;
                    btnExportar.innerHTML = '<i class="fa-solid fa-download"></i> Exportar Resultados';
                    return;
                }
            }

            const response = await fetch(`/api/exportar_partida/${partidaId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const contentType = response.headers.get('Content-Type') || '';

            // Si la respuesta no es 2xx, intentar leer texto/JSON y mostrar error
            if (!response.ok) {
                let text = '';
                try {
                    // Intentar JSON primero
                    if (contentType.includes('application/json')) {
                        const data = await response.json();
                        text = data.error || data.message || JSON.stringify(data);
                    } else {
                        text = await response.text();
                    }
                } catch (e) {
                    text = `Error del servidor (status ${response.status})`;
                }
                console.error('Export error response:', response.status, text);
                mostrarToast(`❌ Error del servidor: ${text}`, 'error');
                return;
            }

            // Si es JSON (respuesta de Drive u otros mensajes)
            if (contentType.includes('application/json')) {
                const data = await response.json();

                // Aceptar ambas formas: {status: 'success'} o {success: true}
                const okDrive = data.status === 'success' || data.success === true;

                if (okDrive) {
                    mostrarToast('✅ Archivo subido a Google Drive correctamente.');

                    if (data.drive_url) {
                        setTimeout(() => {
                            if (confirm('¿Deseas abrir el archivo en Google Drive?')) {
                                window.open(data.drive_url, '_blank');
                            }
                        }, 500);
                    }
                } else {
                    const err = data.error || data.message || JSON.stringify(data);
                    mostrarToast(`❌ ${err}`, 'error');
                }
            }
            // Si la respuesta es HTML (página de error), no descargarla como archivo
            else if (contentType.includes('text/html')) {
                const text = await response.text();
                console.error('HTML error response:', text);
                mostrarToast('❌ Error inesperado del servidor. Revisa la consola para más detalles.', 'error');
            }
            else {
                // Es descarga directa (blob)
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                const extension = formatoSeleccionado === 'excel' ? 'xlsx' : formatoSeleccionado;
                a.download = `resultados_partida_${partidaId}.${extension}`;

                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);

                mostrarToast('✅ Archivo descargado correctamente.');
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

// ======================================================
// AUTENTICACIÓN CON GOOGLE
// ======================================================

async function autenticarConGoogle(email) {
    try {
        mostrarToast('🔄 Conectando con Google Drive...', 'info');

        // Construir URL manualmente (fallback si el endpoint falla)
        const CLIENT_ID = '52705894161-h0iaill994m2somatd50kh4drlt3dsve.apps.googleusercontent.com';
        const REDIRECT_URI = 'http://localhost:5000/api/auth/google_drive/callback';
        const SCOPE = 'https://www.googleapis.com/auth/drive.file';

        const params = new URLSearchParams({
            client_id: CLIENT_ID,
            redirect_uri: REDIRECT_URI,
            response_type: 'code',
            scope: SCOPE,
            access_type: 'offline',
            prompt: 'consent',
            login_hint: email
        });

        const auth_url = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;

        // Abrir ventana de autenticación
        const authWindow = window.open(
            auth_url,
            'GoogleAuth',
            'width=600,height=700,left=200,top=100'
        );

        if (!authWindow) {
            throw new Error('Por favor permite las ventanas emergentes');
        }

        // Escuchar respuesta
        const messageHandler = (event) => {
            // Verificar que el mensaje viene de nuestro dominio
            if (event.origin !== window.location.origin) {
                return;
            }

            if (event.data.type === 'google_auth_success') {
                window.googleAccessToken = event.data.access_token;
                window.googleUserEmail = email;

                mostrarEstadoConectado(email);
                mostrarToast('✅ Conectado a Google Drive');

                // Remover listener
                window.removeEventListener('message', messageHandler);

                if (authWindow && !authWindow.closed) {
                    authWindow.close();
                }
            } else if (event.data.type === 'google_auth_error') {
                window.removeEventListener('message', messageHandler);
                throw new Error(event.data.error || 'Error de autenticación');
            }
        };

        window.addEventListener('message', messageHandler);

        // Timeout de 5 minutos
        setTimeout(() => {
            if (authWindow && !authWindow.closed) {
                authWindow.close();
                window.removeEventListener('message', messageHandler);
                mostrarToast('⏱️ Tiempo de espera agotado', 'error');
                document.getElementById('subirADrive').checked = false;
            }
        }, 300000);

    } catch (error) {
        console.error('Error autenticando:', error);
        mostrarToast(`❌ ${error.message}`, 'error');
        document.getElementById('subirADrive').checked = false;
    }
}

// ======================================================
// MOSTRAR ESTADO DE CONEXIÓN
// ======================================================

function mostrarEstadoConectado(email) {
    const driveStatusBox = document.getElementById('driveStatusBox');

    driveStatusBox.className = 'drive-status-box connected';
    driveStatusBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fa-solid fa-check-circle" style="color: #28a745; font-size: 1.2rem;"></i>
                <div>
                    <strong style="color: #155724;">Conectado a Google Drive</strong>
                    <p style="margin: 4px 0 0; font-size: 0.9rem; color: #155724;">${email}</p>
                </div>
            </div>
            <i class="fa-brands fa-google-drive" style="font-size: 2rem; color: #4285F4;"></i>
        </div>
    `;
    driveStatusBox.style.display = 'block';
}

// ======================================================
// NOTIFICACIÓN (Toast)
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