// static/js/previapartida.js - AJAX POLLING (Sin WebSockets)
document.addEventListener("DOMContentLoaded", () => {
    // Si la página se recarga directamente (sin pasar desde config), limpiar el flag
    if (performance.navigation.type === performance.navigation.TYPE_RELOAD) {
        localStorage.removeItem("userInteractedWithAudio");
    }
    console.log("🎮 previapartida.js cargado (AJAX Polling Mode)");

    const body = document.body;
    const loggedUser = JSON.parse(body.dataset.loggedUser || "null");
    const isGroupGame = JSON.parse(body.dataset.isGroupGame || "false");
    const numGrupos = parseInt(body.dataset.numGrupos || "3");
    const codigoPartida = document.querySelector(".game-code")?.textContent.trim();

    console.log("📋 Config:", { loggedUser, isGroupGame, numGrupos, codigoPartida });

    // ===================================================================
    // MÚSICA DE FONDO
    // ===================================================================
    const musicaActiva = localStorage.getItem("musicaActiva");
    const cancionGuardada = localStorage.getItem("cancionActual");
    let musicaActual = null;

    const userInteracted = localStorage.getItem("userInteractedWithAudio");
    // Verificamos si ya hay música en reproducción (guardada)
    // Función genérica para iniciar música
    function iniciarMusica() {
        if (!window.musicaGlobal && musicaActiva === "true" && cancionGuardada) {
            const audio = new Audio(cancionGuardada);
            audio.loop = true;
            audio.volume = 0.4;
            audio.play()
                .then(() => console.log("🎧 Música iniciada:", cancionGuardada))
                .catch(err => console.warn("⚠️ Error al reproducir audio:", err));
            window.musicaGlobal = audio;
        }
    }

    // === CASO 1: Usuario ya interactuó en la página anterior (automático) ===
    if (musicaActiva === "true" && cancionGuardada && userInteracted === "true") {
        console.log("✅ Reproduciendo automáticamente (usuario ya interactuó).");
        iniciarMusica();
    }

    // === CASO 2: Primera vez o recarga (espera interacción) ===
    else if (musicaActiva === "true" && cancionGuardada) {
        console.log("🟡 Esperando interacción del usuario para iniciar música...");
        function handleFirstInteraction() {
            iniciarMusica();
            document.removeEventListener("click", handleFirstInteraction);
            document.removeEventListener("keydown", handleFirstInteraction);
            // Guardamos que ya interactuó (para futuras cargas)
            localStorage.setItem("userInteractedWithAudio", "true");
        }
        document.addEventListener("click", handleFirstInteraction);
        document.addEventListener("keydown", handleFirstInteraction);
    }
    // ===================================================================
    // BOTÓN COPIAR CÓDIGO
    // ===================================================================
    const copyBtn = document.querySelector(".copy-icon");
    if (copyBtn) {
        copyBtn.addEventListener("click", () => {
            const code = document.querySelector(".game-code").textContent.trim();
            navigator.clipboard.writeText(code)
                .then(() => {
                    alert(`✅ Código copiado: ${code}`);
                    console.log("📋 Código copiado al portapapeles");
                })
                .catch(err => console.error("❌ Error al copiar:", err));
        });
    }

    // ===================================================================
    // BOTÓN INICIAR PARTIDA
    // ===================================================================
    const startBtn = document.querySelector(".start-game-button");
    if (startBtn) {
        startBtn.addEventListener("click", () => {
            console.log("🚀 Iniciando partida...");
            if (musicaActual) {
                musicaActual.pause();
                musicaActual = null;
            }
            localStorage.removeItem("cancionActual");
            localStorage.removeItem("musicaActiva");
            // Aquí puedes redirigir o cambiar el estado de la partida
        });
    }

    // ===================================================================
    // PREPARAR VISTA DE GRUPOS (si es grupal)
    // ===================================================================
    if (isGroupGame) {
        const groupView = document.getElementById('group-view');
        if (groupView) {
            groupView.innerHTML = '';

            // 1. Crear el grupo especial "SIN ASIGNAR" (Grupo ID 0)
            const colNoGroup = document.createElement('div');
            colNoGroup.classList.add('group-column', 'no-group');
            // Usaremos el ID 0 o 'null' para identificar este grupo
            colNoGroup.dataset.grupoId = '0'; 
            colNoGroup.innerHTML = `<h3 class="group-title no-group-title">Sin Asignar (0)</h3>`;
            groupView.appendChild(colNoGroup);

            // 2. Crear los grupos normales (Grupo ID 1 hasta numGrupos)
            for (let i = 1; i <= numGrupos; i++) {
                const col = document.createElement('div');
                col.classList.add('group-column');
                col.dataset.grupoId = i;
                col.innerHTML = `<h3 class="group-title">Grupo ${String(i).padStart(2, '0')}</h3>`;
                groupView.appendChild(col);
            }
        }
    }

    // ===================================================================
    // RENDERIZAR PARTICIPANTES EN LA UI
    // ===================================================================
    function renderParticipantes(participantes) {
        const individualView = document.getElementById('individual-view');
        const groupView = document.getElementById('group-view');

        // ... (código para MODO INDIVIDUAL sin cambios)
        if (!isGroupGame && individualView) {
            // ... (código sin cambios)
            return;
        }


        // MODO GRUPAL
        if (isGroupGame && groupView) {
            // Limpiar todas las columnas de grupo
            const columnas = groupView.querySelectorAll('.group-column');
            columnas.forEach(col => {
                // Preservar el título, pero limpiar participantes
                const titulo = col.querySelector('.group-title');
                col.innerHTML = '';
                if (titulo) col.appendChild(titulo);
            });

            participantes.forEach(usuario => {
                // Si grupo_id es NULL, lo mapeamos al grupo 0 ("Sin Asignar")
                const grupoId = usuario.grupo_id || '0'; 
                let targetColumn;

                // La condición para el grupo objetivo ahora incluye el grupo 0
                if (grupoId == '0') {
                    targetColumn = groupView.querySelector(`[data-grupo-id="0"]`);
                } else if (grupoId >= 1 && grupoId <= numGrupos) {
                    targetColumn = groupView.querySelector(`[data-grupo-id="${grupoId}"]`);
                }

                // Si el grupo es válido o es el grupo "Sin Asignar"
                if (!targetColumn) {
                    // Esto podría pasar si el grupoId es mayor que numGrupos, lo ignoramos
                    console.warn(`Participante ${usuario.nombre} tiene grupo_id ${usuario.grupo_id} inválido o no renderizable.`);
                    return;
                }

                const tarjeta = document.createElement("div");
                tarjeta.classList.add("tarjeta-usuario", "usuario-en-grupo");
                tarjeta.title = usuario.nombre;

                // Solo permitimos designar líder si el participante YA está en un grupo (grupoId > 0)
                const esLider = usuario.lider_id === usuario.participante_id;
                const iconoLider = esLider ?
                    `<span class="lider-icon" title="Líder del grupo">🏁</span>` : '';

                tarjeta.innerHTML = `
                    <div class="usuario-info">
                        <img src="${usuario.url_avatar || '/static/img/default-avatar.png'}" alt="Avatar">
                        <span>${usuario.nombre}</span>
                        ${iconoLider}
                    </div>
                `;

                // Si es profesor, permitir designar líder (solo si está en un grupo asignado)
                if (loggedUser && loggedUser.tipo_usuario === 'P' && grupoId > 0) {
                    tarjeta.style.cursor = 'pointer';
                    tarjeta.addEventListener('click', async () => {
                        if (confirm(`¿Designar a ${usuario.nombre} como líder del grupo ${grupoId}?`)) {
                            await designarLider(grupoId, usuario.participante_id);
                        }
                    });
                } else if (grupoId == '0') {
                    // Estilo distinto o simplemente no es clickeable si está "Sin Asignar"
                    tarjeta.style.backgroundColor = '#f0f0f0'; 
                }

                targetColumn.appendChild(tarjeta);
            });
        }
    }

    // ===================================================================
    // AJAX POLLING: CONSULTAR PARTICIPANTES PERIÓDICAMENTE
    // ===================================================================
    let pollingInterval = null;
    let lastTimestamp = 0;
    let isPolling = false;

    async function pollParticipantes() {
        // Evitar múltiples llamadas simultáneas
        if (isPolling) {
            console.log("⏳ Polling en progreso, esperando...");
            return;
        }

        isPolling = true;

        try {
            const response = await fetch(`/api/partida/${codigoPartida}/poll`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.participantes) {
                // Solo actualizar si hubo cambios (comparar timestamp)
                if (data.timestamp !== lastTimestamp) {
                    console.log(`🔄 Actualización detectada (${data.total} participantes)`);
                    lastTimestamp = data.timestamp;
                    renderParticipantes(data.participantes);
                }
            } else {
                console.warn("⚠️ Respuesta sin datos válidos:", data);
            }

        } catch (error) {
            console.error("❌ Error en polling:", error);
            // No detener el polling en caso de error temporal
        } finally {
            isPolling = false;
        }
    }

    // ===================================================================
    // DESIGNAR LÍDER (solo profesor)
    // ===================================================================
    async function designarLider(grupoId, participanteId) {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/designar_lider`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    grupo_id: grupoId,
                    lider_participante_id: participanteId
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log("✅ Líder designado correctamente");
                // Forzar actualización inmediata
                await pollParticipantes();
            } else {
                alert("❌ Error al designar líder: " + (data.message || "Error desconocido"));
            }

        } catch (error) {
            console.error("❌ Error al designar líder:", error);
            alert("Error de conexión al designar líder");
        }
    }

    // ===================================================================
    // INICIAR POLLING
    // ===================================================================
    if (!codigoPartida) {
        console.error("❌ No se encontró código de partida");
    } else {
        console.log("🔄 Iniciando AJAX Polling cada 3 segundos...");

        // Primera carga inmediata
        pollParticipantes();

        // Polling cada 3 segundos (ajustable según necesidades)
        pollingInterval = setInterval(pollParticipantes, 3000);
    }

    // ===================================================================
    // LIMPIAR AL SALIR
    // ===================================================================
    window.addEventListener('beforeunload', () => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            console.log("🛑 Polling detenido");
        }
        if (musicaActual) {
            musicaActual.pause();
        }
    });

    // ===================================================================
    // CONFIGURAR VISTA INICIAL
    // ===================================================================
    if (isGroupGame) {
        const individualView = document.getElementById('individual-view');
        const groupView = document.getElementById('group-view');
        if (individualView) individualView.style.display = 'none';
        if (groupView) groupView.style.display = 'flex';
    } else {
        const individualView = document.getElementById('individual-view');
        const groupView = document.getElementById('group-view');
        if (individualView) individualView.style.display = 'flex';
        if (groupView) groupView.style.display = 'none';
    }

    console.log("✅ previapartida.js configurado correctamente");
});