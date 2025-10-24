document.addEventListener('DOMContentLoaded', () => {
    const rankingList = document.getElementById('ranking-list');
    const continueBtn = document.getElementById('continue-btn');
    const codigoPartida = document.body.dataset.codigoPartida;
    const esProfesor = document.body.dataset.esProfesor === 'true';
    const esGrupal = document.body.dataset.esGrupal === 'true';

    console.log("¿Es grupal?:", esGrupal);
    // Función para crear una tarjeta de jugador en el ranking
    function createPlayerCard(player) {
        const card = document.createElement('div');
        card.classList.add('player-card');

        // Determinar la clase para la flecha de cambio de posición
        let changeIcon = '';
        let changeClass = 'stay'; // Por defecto, se mantiene
        if (player.positionChange === 'up') {
            changeIcon = '<i class="fas fa-arrow-up"></i>';
            changeClass = 'up';
        } else if (player.positionChange === 'down') {
            changeIcon = '<i class="fas fa-arrow-down"></i>';
            changeClass = 'down';
        } else { // 'stay' o null/undefined
            changeIcon = '<i class="fas fa-minus"></i>';
        }

        const avatarContent = player.avatarUrl
            ? `<img src="${player.avatarUrl}" alt="Avatar de ${player.name}">`
            : '<i class="fas fa-user-circle"></i>'; // Icono de usuario si no hay avatar

        card.innerHTML = `
            <div class="player-info">
                <div class="player-avatar">
                    ${avatarContent}
                </div>
                <span class="player-name">${player.name}</span>
            </div>
            <div class="player-score-container">
                <div class="player-position-change ${changeClass}">
                    ${changeIcon}
                </div>
                <div class="player-score">${player.score}</div>
            </div>
        `;
        return card;
    }

    // Función para actualizar el ranking completo
    function updateRanking(playersData) {
        rankingList.innerHTML = ''; // Limpiar el ranking actual
        playersData.forEach(player => {
            rankingList.appendChild(createPlayerCard(player));
        });
    }

    // --- DATOS DE EJEMPLO ---
    // Esto es lo que recibirías de tu backend después de cada pregunta
    const sampleRankingData = [
        { id: 'p1', name: 'Jugador 1', score: 1500, avatarUrl: 'https://via.placeholder.com/50/4CAF50/FFFFFF?text=J1', positionChange: 'up' },
        { id: 'p2', name: 'Jugador 2', score: 1400, avatarUrl: 'https://via.placeholder.com/50/F44336/FFFFFF?text=J2', positionChange: 'down' },
        { id: 'p3', name: 'Jugador 3', score: 1300, avatarUrl: 'https://via.placeholder.com/50/2196F3/FFFFFF?text=J3', positionChange: 'up' },
        { id: 'p4', name: 'Jugador 4', score: 1200, avatarUrl: 'https://via.placeholder.com/50/FFC107/FFFFFF?text=J4', positionChange: 'stay' },
        { id: 'p5', name: 'Jugador 5', score: 1150, avatarUrl: null, positionChange: 'down' }, // Ejemplo sin avatar
        { id: 'p6', name: 'Jugador Muy Muy Largo Para Prueba', score: 1100, avatarUrl: 'https://via.placeholder.com/50/9E9E9E/FFFFFF?text=J6', positionChange: 'up' },
    ];

    // Mostrar/ocultar botón según rol
    if (!esProfesor && continueBtn) {
        continueBtn.style.display = 'none';
    }

    // Función para cargar ranking real desde backend
    async function loadRanking() {
        try {
            const resp = await fetch(`/api/partida/${codigoPartida}/ranking`);
            if (!resp.ok) {
                console.warn('No se pudo obtener ranking, usando demo');
                return;
            }
            const data = await resp.json();
            if (data && data.success && Array.isArray(data.ranking)) {
                let jugadores = data.ranking;
                // 🔍 Mostrar ranking recibido
                
                // Si la partida es grupal, solo mostrar líderes
                if (esGrupal) {
                   const lideres = jugadores.filter(j => j.es_lider === true);
                    
                    jugadores = lideres;
                }

                updateRanking(jugadores);
            }
        } catch (err) {
            console.error('Error cargando ranking:', err);
        }
    }

    // Cargar ranking al inicio y cada 3 segundos
    loadRanking();
    const rankingInterval = setInterval(loadRanking, 3000);

    // Poll pequeño para detectar cambio de estado/pregunta y redirigir a la vista de pregunta
    let lastPreguntaIndex = null;
    async function pollEstadoPartida() {
        try {
            const resp = await fetch(`/api/partida/${codigoPartida}/poll`);
            if (!resp.ok) return;
            const data = await resp.json();
            if (!data || !data.success) return;

            const estado = data.estado_partida || data.estado || '';
            const preguntaServer = typeof data.pregunta_actual !== 'undefined' ? data.pregunta_actual : null;

            // Guardar la primera vez
            if (lastPreguntaIndex === null && preguntaServer !== null) {
                lastPreguntaIndex = preguntaServer;
            }

            // Si el servidor indica que vuelve a en_curso, redirigir según rol
            if (estado === 'en_curso' || estado === 'en_juego') {
                // limpiar intervals
                clearInterval(rankingInterval);
                clearInterval(estadoInterval);
                if (esProfesor) {
                    window.location.href = `/preguntasprofesor/${codigoPartida}`;
                } else {
                    window.location.href = `/preguntasalumno/${codigoPartida}`;
                }
                return;
            }

            // Si cambió el índice de la pregunta (por ejemplo profesor avanzó), también redirigir
            if (preguntaServer !== null && lastPreguntaIndex !== null && preguntaServer !== lastPreguntaIndex) {
                clearInterval(rankingInterval);
                clearInterval(estadoInterval);
                if (esProfesor) {
                    window.location.href = `/preguntasprofesor/${codigoPartida}`;
                } else {
                    window.location.href = `/preguntasalumno/${codigoPartida}`;
                }
                return;
            }

        } catch (err) {
            console.error('Error polling estado desde ranking:', err);
        }
    }

    const estadoInterval = setInterval(pollEstadoPartida, 1500);

    // --- Lógica del botón Continuar (solo profesor) ---
    if (continueBtn) {
        continueBtn.addEventListener('click', async () => {
            continueBtn.disabled = true;
            continueBtn.textContent = 'Avanzando...';

            try {
                // 1) Avanzar pregunta en servidor
                const resp = await fetch(`/api/partida/${codigoPartida}/avanzar`, { method: 'POST' });
                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    console.error('Error al avanzar pregunta', data);
                    continueBtn.disabled = false;
                    continueBtn.textContent = 'Continuar';
                    return;
                }

                // 2) Cambiar estado a 'en_curso' para que los clientes vuelvan a la pregunta
                await fetch(`/api/partida/${codigoPartida}/estado`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nuevo_estado: 'en_curso' })
                });

                // detener el polling del ranking antes de redirigir
                clearInterval(rankingInterval);

                // 3) Redirigir al profesor a su vista de pregunta
                window.location.href = `/preguntasprofesor/${codigoPartida}`;

            } catch (error) {
                console.error('Error al avanzar desde ranking:', error);
                continueBtn.disabled = false;
                continueBtn.textContent = 'Continuar';
            }
        });
    }

    // --- Ejemplo de cómo actualizar el ranking después de un cambio ---
    // Simular una actualización después de 5 segundos (como si fuera una nueva pregunta)
    setTimeout(() => {
        const updatedRankingData = [
            { id: 'p1', name: 'Jugador 1', score: 1800, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'up' },
            { id: 'p3', name: 'Jugador 3', score: 1600, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'up' },
            { id: 'p2', name: 'Jugador 2', score: 1400, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'stay' },
            { id: 'p4', name: 'Jugador 4', score: 1250, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'up' },
            { id: 'p6', name: 'Jugador Muy Muy Largo Para Prueba', score: 1100, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'stay' },
            { id: 'p5', name: 'Jugador 5', score: 1050, avatarUrl: '../static/img/avatar.jpeg', positionChange: 'down' },
        ];
        console.log('Actualizando ranking...');
        updateRanking(updatedRankingData);
    }, 5000);
});