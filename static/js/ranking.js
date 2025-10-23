document.addEventListener('DOMContentLoaded', () => {
    const rankingList = document.getElementById('ranking-list');
    const continueBtn = document.getElementById('continue-btn');

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

    // Cargar el ranking inicial
    updateRanking(sampleRankingData);

    // --- Lógica del botón Continuar ---
    continueBtn.addEventListener('click', () => {
        alert('Botón Continuar presionado. Aquí iría la lógica para cargar la siguiente pregunta o el resultado final.');
        // Aquí podrías enviar una solicitud a tu backend para avanzar la partida
        // Ejemplo: fetch('/api/partida/avanzar', { method: 'POST' });
    });

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