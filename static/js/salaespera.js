// static/js/salaespera.js - AJAX POLLING (Sin WebSockets)
document.addEventListener("DOMContentLoaded", () => {
    console.log("👥 salaespera.js iniciado (AJAX Polling Mode)");

    // ===================================================================
    // OBTENER DATOS DEL DOM
    // ===================================================================
    const usuarioId = document.body.dataset.usuarioId;
    const tipoUsuario = document.body.dataset.tipoUsuario;
    const codigoPartida = document.body.dataset.codigoPartida;
    const numGrupos = parseInt(document.body.dataset.numGrupos || "3");

    console.log("📋 Configuración:", { usuarioId, tipoUsuario, codigoPartida, numGrupos });

    // Solo alumnos participan en la sala de espera
    if (tipoUsuario !== 'A') {
        console.log("⛔ Usuario no es alumno, no se activa sala de espera");
        return;
    }

    // ===================================================================
    // VARIABLES DE POLLING
    // ===================================================================
    let pollingInterval = null;
    let lastTimestamp = 0;
    let isPolling = false;

    // ===================================================================
    // CREAR TARJETAS DE GRUPOS DINÁMICAMENTE
    // ===================================================================
    const gruposContenedor = document.querySelector('.grupos-contenedor');
    if (gruposContenedor) {
        gruposContenedor.innerHTML = '';

        for (let i = 0; i < numGrupos; i++) {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta-grupo';
            tarjeta.dataset.grupoId = i + 1;
            tarjeta.innerHTML = `
                <div class="encabezado-grupo">Grupo ${String(i + 1).padStart(2, '0')}</div>
                <div class="lista-usuarios"></div>
                <button class="boton-unirse">
                    <span class="icono-mas">+</span> Unirse al equipo
                </button>
            `;
            gruposContenedor.appendChild(tarjeta);

            // Evento para unirse al grupo
            const botonUnirse = tarjeta.querySelector('.boton-unirse');
            botonUnirse.addEventListener('click', () => {
                unirseAGrupo(i + 1);
            });
        }
    }

    // ===================================================================
    // FUNCIÓN: UNIRSE A UN GRUPO
    // ===================================================================
    async function unirseAGrupo(grupoSeleccionado) {
        console.log(`📍 Uniéndose al grupo ${grupoSeleccionado}...`);

        try {
            const response = await fetch(`/api/partida/${codigoPartida}/unirse_grupo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    usuario_id: usuarioId,
                    grupo_id: grupoSeleccionado
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log(`✅ Unido al grupo ${grupoSeleccionado}`);
                // Forzar actualización inmediata
                await pollParticipantes();
            } else {
                alert("❌ Error al unirse al grupo: " + (data.message || "Error desconocido"));
            }

        } catch (error) {
            console.error("❌ Error al unirse al grupo:", error);
            alert("Error de conexión al unirse al grupo");
        }
    }

    // ===================================================================
    // FUNCIÓN: POLLING DE PARTICIPANTES
    // ===================================================================
    async function pollParticipantes() {
        if (isPolling) {
            console.log("⏳ Polling en progreso...");
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
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {

                // ⭐️ AÑADIR/VERIFICAR LÓGICA DE REDIRECCIÓN AQUÍ ⭐️
                // Compatibilidad: el backend puede devolver 'estado' o 'estado_partida'
                const estadoPartida = data.estado || data.estado_partida || null;
                console.log('Estado de partida (poll):', estadoPartida);

                // Aceptar varios valores que significan inicio de la cuenta regresiva / juego
                if (estadoPartida === 'en_juego' || estadoPartida === 'en_curso' || estadoPartida === 'cuenta_regresiva') {
                    console.log("¡El profesor ha iniciado la partida! Redirigiendo a la cuenta regresiva.");
                    
                    // Detener el polling
                    if (pollingInterval) { 
                        clearInterval(pollingInterval);
                    }
                    
                    // Redirigir al flujo de juego. Si tienes una ruta específica para la cuenta regresiva úsala
                    const targetUrl = `/cuentaregresiva/${codigoPartida}`;
                    window.location.href = targetUrl;
                    return; 
                }

                // Solo actualizar si hay cambios y si hay participantes (para evitar error si data.participantes es null)
                if (data.participantes && data.timestamp !== lastTimestamp) {
                    console.log(`🔄 Actualización: ${data.total} participantes`);
                    lastTimestamp = data.timestamp;
                    renderizarParticipantes(data.participantes);
                }
            }

        } catch (error) {
            console.error("❌ Error en polling:", error);
        } finally {
            isPolling = false;
        }
    }

    // ===================================================================
    // FUNCIÓN: RENDERIZAR PARTICIPANTES EN GRUPOS
    // ===================================================================
    function renderizarParticipantes(participantes) {
        // Limpiar todas las listas de usuarios
        document.querySelectorAll('.lista-usuarios').forEach(lista => {
            lista.innerHTML = '';
        });

        participantes.forEach(p => {
            const grupoId = p.grupo_id || 0;
            const tarjeta = document.querySelector(`.tarjeta-grupo[data-grupo-id="${grupoId}"]`);
            
            if (!tarjeta) {
                console.warn(`⚠️ No se encontró tarjeta para grupo ${grupoId}`);
                return;
            }

            const listaUsuarios = tarjeta.querySelector('.lista-usuarios');
            const usuarioDiv = document.createElement('div');
            usuarioDiv.className = 'usuario';
            usuarioDiv.dataset.usuarioId = p.usuario_id;

            // Mostrar líder con corona
            const esLider = p.lider_id && p.lider_id === p.participante_id;
            
            if (esLider) {
                usuarioDiv.classList.add('lider');
                usuarioDiv.innerHTML = `
                    <img src="${p.url_avatar || '/static/img/avatar.jpeg'}" alt="Avatar">
                    <span>👑 ${p.nombre}</span>
                `;
            } else {
                usuarioDiv.innerHTML = `
                    <img src="${p.url_avatar || '/static/img/avatar.jpeg'}" alt="Avatar">
                    <span>${p.nombre}</span>
                `;
            }

            listaUsuarios.appendChild(usuarioDiv);
        });
    }

    // ===================================================================
    // MOSTRAR USUARIO ACTUAL EN SU TARJETA
    // ===================================================================
    const tarjetaUsuario = document.querySelector('.tarjeta-usuario');
    console.log("Avatar:"  + tarjetaUsuario.dataset.avatar);
    if (tarjetaUsuario) {
        const nombreUsuario = tarjetaUsuario.dataset.nombreUsuario || "Usuario";
        tarjetaUsuario.innerHTML = `
            <div class="usuario">
                <img src="${tarjetaUsuario.dataset.avatar || '/static/img/avatar.jpeg'}" alt="Avatar">
                <span>${nombreUsuario}</span>
            </div>
        `;
    }

    // ===================================================================
    // BOTÓN SALIR
    // ===================================================================
    const salirBtn = document.querySelector('#btnSalir');
    if (salirBtn) {
        salirBtn.addEventListener('click', async () => {
            if (!confirm("¿Estás seguro que quieres salir de la partida?")) {
                return;
            }

            try {
                // Primero actualizar BD
                await fetch('/api/partida/salir', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        codigo_partida: codigoPartida, 
                        usuario_id: usuarioId 
                    })
                });

                console.log("✅ Usuario salió de la partida");
                
                // Detener polling
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                }

                // Redirigir
                window.location.href = '/partidas';

            } catch (error) {
                console.error("❌ Error al salir:", error);
                alert("Error al salir de la partida");
            }
        });
    }

    // ===================================================================
    // MANEJAR REFRESH/CIERRE DE PESTAÑA
    // ===================================================================
    window.addEventListener("beforeunload", async (e) => {
        // Intentar notificar al servidor que el usuario salió
        try {
            navigator.sendBeacon(
                '/api/partida/salir', 
                JSON.stringify({
                    codigo_partida: codigoPartida,
                    usuario_id: usuarioId
                })
            );
        } catch (error) {
            console.error("Error en beforeunload:", error);
        }

        // Detener polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });

    // ===================================================================
    // INICIAR POLLING
    // ===================================================================
    if (!codigoPartida || !usuarioId) {
        console.error("❌ Faltan datos necesarios para polling");
    } else {
        console.log("🔄 Iniciando AJAX Polling cada 2 segundos...");
        
        // Primera carga inmediata
        pollParticipantes();
        
        // Polling cada 2 segundos
        pollingInterval = setInterval(pollParticipantes, 2000);
    }

    console.log("✅ salaespera.js configurado correctamente");
});