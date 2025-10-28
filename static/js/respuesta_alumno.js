document.addEventListener('DOMContentLoaded', () => {
    // Función para actualizar la UI
    function updateFeedback(isCorrect, questionNum, streak, points, username, totalScore, avatarUrl) {
        // Asegurar tipos numéricos
        const pts = Number(points) || 0;
        const qNum = Number(questionNum) || 1;
        const st = Number(streak) || 0;

        document.getElementById('question-number').textContent = `Pregunta ${qNum}`;
        document.getElementById('username-display').textContent = username;
        document.getElementById('user-total-score').textContent = totalScore;
        document.getElementById('user-avatar').src = avatarUrl || 'https://via.placeholder.com/40';

        const feedbackIconWrapper = document.getElementById('feedback-icon-wrapper');
        const feedbackMessage = document.getElementById('feedback-message');
        const feedbackStreak = document.getElementById('feedback-streak');
        const pointsAwarded = document.getElementById('points-awarded');
        const pointsSpan = pointsAwarded.querySelector('span');

        // Limpiar contenido previo
        feedbackIconWrapper.innerHTML = '';
        pointsAwarded.style.display = 'none'; // Ocultar por defecto

        if (isCorrect) {
            feedbackIconWrapper.innerHTML = '<i class="fas fa-check-circle correct-icon"></i>';
            feedbackMessage.textContent = '¡Respuesta Correcta!';
            feedbackStreak.textContent = `Racha de respuesta: ${st} 🔥`;
            // Mostrar puntos con formato seguro
            pointsSpan.textContent = `+${pts}`;
            pointsAwarded.style.display = 'block'; // Mostrar puntos
        } else {
            feedbackIconWrapper.innerHTML = '<i class="fas fa-times-circle incorrect-icon"></i>';
            feedbackMessage.textContent = 'Respuesta Incorrecta';
            feedbackStreak.textContent = `Racha de respuestas perdidas ¡No te rindas!`;
            // Los puntos no se muestran en incorrecta, ya está oculto por defecto
        }
    }

    // --- EJEMPLOS DE USO ---

    // Simular una respuesta correcta
    // Descomenta para probar:
    // updateFeedback(true, 5, 2, 900, 'EstudianteFeliz', 1500, 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214821/Ingeniero-Civil128x128.png_pnf3ts.png');

    // Simular una respuesta incorrecta
    // Descomenta para probar:
    // updateFeedback(false, 6, 0, 0, 'EstudianteTriste', 1500, 'https://res.cloudinary.com/dpxslk02r/image/upload/v1760214817/Hacker-1.png_zlyogm.png');


    // --- Cómo lo usarías en un entorno real (ejemplo con datos de un backend) ---
    // Leer datos inyectados por Jinja en el contenedor
    const container = document.querySelector('.feedback-container');
    if (container) {
        const username = container.dataset.username || 'Usuario';
        const avatar = container.dataset.avatar || '../static/img/default.png';
        const totalScore = Number(container.dataset.score) || 0;
        const streak = Number(container.dataset.streak) || 0;
        const questionNumber = Number(container.dataset.questionNumber) || 1;
        // puntos que envía el backend (si existe) — puede ser null/undefined
        const pointsEarnedRaw = container.dataset.pointsEarned;
        const pointsEarned = Number(pointsEarnedRaw);

        // Depuración: loguear los valores recibidos para rastrear por qué siempre sale 900
        console.log('Respuesta alumno - dataset:', {
            username: container.dataset.username,
            avatar: container.dataset.avatar,
            score: container.dataset.score,
            streak: container.dataset.streak,
            questionNumber: container.dataset.questionNumber,
            pointsEarnedRaw
        });

        // Si el backend no proporciona pointsEarned o quieres calcularlo aquí,
        // puedes usar una fórmula alternativa (ejemplo: base 100 * streak)
        // Pero por ahora preferimos usar el valor enviado si es un número válido.
        const finalPoints = Number.isFinite(pointsEarned) ? pointsEarned : (streak > 0 ? 100 * streak : 0);

        updateFeedback(
            finalPoints > 0, // correcto si points > 0
            questionNumber,
            streak,
            finalPoints,
            username,
            totalScore,
            avatar
        );
    }

    // Polling: esperar a que el profesor avance (estado vuelva a 'en_curso')
    let pollInterval = null;
    function startPollingEstado() {
        const codigo = container ? container.dataset.codigoPartida : null;
        if (!codigo) return;

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/partida/${codigo}/poll`);
                if (!res.ok) return;
                const data = await res.json();
                        const estado = data.estado_partida || data.estado || '';
                        if (estado === 'en_curso' || estado === 'en_juego') {
                            // Redirigir a la vista de preguntas del alumno
                            clearInterval(pollInterval);
                            window.location.href = `/preguntasalumno/${codigo}`;
                        }

                        // Si la partida fue finalizada por el profesor, llevar al alumno al podio
                        if (estado === 'finalizada') {
                            clearInterval(pollInterval);
                            window.location.href = `/podio/${codigo}`;
                        }
            } catch (e) {
                console.warn('Error en polling respuesta_alumno:', e);
            }
        }, 1500);
    }

    startPollingEstado();

});