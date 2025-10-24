// static/js/ranking.js
document.addEventListener('DOMContentLoaded', () => {
    const rankingList = document.getElementById('ranking-list');
    const continueBtn = document.getElementById('continue-btn');
    const codigoPartida = document.body.dataset.codigoPartida;
    const esProfesor = document.body.dataset.esProfesor === 'true';
    const esGrupal = document.body.dataset.esGrupal === 'true';

    function createPlayerCard(player, position) {
        const card = document.createElement('div');
        card.classList.add('player-card');

        const avatarContent = player.avatarUrl
            ? `<img src="${player.avatarUrl}" alt="Avatar de ${player.name}">`
            : '<i class="fas fa-user-circle"></i>';

        card.innerHTML = `
            <div class="player-info">
                <div class="player-rank">${position}</div>
                <div class="player-avatar">
                    ${avatarContent}
                </div>
                <span class="player-name">${player.name}</span>
            </div>
            <div class="player-score-container">
                <div class="player-score">${player.score}</div>
            </div>
        `;
        return card;
    }

    function updateRanking(playersData) {
        rankingList.innerHTML = '';
        playersData.forEach((player, index) => {
            rankingList.appendChild(createPlayerCard(player, index + 1));
        });
    }

    if (!esProfesor && continueBtn) {
        continueBtn.style.display = 'none';
    }

    async function loadRanking() {
        try {
            const resp = await fetch(`/api/partida/${codigoPartida}/ranking`);
            if (!resp.ok) {
                console.warn('No se pudo obtener ranking');
                return;
            }
            const data = await resp.json();
            if (data && data.success && Array.isArray(data.ranking)) {
                let jugadores = data.ranking;
                
                // Si es grupal, solo mostrar líderes
                if (esGrupal) {
                   jugadores = jugadores.filter(j => j.es_lider === true);
                }

                updateRanking(jugadores);
            }
        } catch (err) {
            console.error('Error cargando ranking:', err);
        }
    }

    loadRanking();
    const rankingInterval = setInterval(loadRanking, 3000);

    let lastPreguntaIndex = null;
    async function pollEstadoPartida() {
        try {
            const resp = await fetch(`/api/partida/${codigoPartida}/poll`);
            if (!resp.ok) return;
            const data = await resp.json();
            if (!data || !data.success) return;

            const estado = data.estado_partida || data.estado || '';
            const preguntaServer = typeof data.pregunta_actual !== 'undefined' ? data.pregunta_actual : null;

            if (lastPreguntaIndex === null && preguntaServer !== null) {
                lastPreguntaIndex = preguntaServer;
            }

            if (estado === 'en_curso' || estado === 'en_juego') {
                clearInterval(rankingInterval);
                clearInterval(estadoInterval);
                if (esProfesor) {
                    window.location.href = `/preguntasprofesor/${codigoPartida}`;
                } else {
                    window.location.href = `/preguntasalumno/${codigoPartida}`;
                }
                return;
            }

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

    if (continueBtn) {
        continueBtn.addEventListener('click', async () => {
            continueBtn.disabled = true;
            continueBtn.textContent = 'Avanzando...';

            try {
                const resp = await fetch(`/api/partida/${codigoPartida}/avanzar`, { method: 'POST' });
                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    console.error('Error al avanzar pregunta', data);
                    continueBtn.disabled = false;
                    continueBtn.textContent = 'Continuar';
                    return;
                }

                await fetch(`/api/partida/${codigoPartida}/estado`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nuevo_estado: 'en_curso' })
                });

                clearInterval(rankingInterval);
                window.location.href = `/preguntasprofesor/${codigoPartida}`;

            } catch (error) {
                console.error('Error al avanzar desde ranking:', error);
                continueBtn.disabled = false;
                continueBtn.textContent = 'Continuar';
            }
        });
    }
});