// static/js/esperando_lider.js

document.addEventListener("DOMContentLoaded", () => {
    const codigoPartida = document.body.dataset.codigoPartida || '';
    const tipoUsuario = document.body.dataset.tipoUsuario || ''; // 'P' para Profesor, 'A' para Alumno
    const display = document.getElementById('countdownDisplay'); // mismo div que tu cuenta regresiva
    const redirectLoader = document.getElementById('redirectLoader');

    let ultimaPreguntaIndex = null;

    async function checkEstado() {
        try {
            const res = await fetch(`/api/partida/${codigoPartida}/estado_usuario`);
            const data = await res.json();

            // if (!data.success) {
            //     display.textContent = "❌ Error al consultar partida";
            //     console.error(data.message);
            //     return;
            // }

            // Si eres líder, puedes avanzar automáticamente (o mostrar GO)
            // if (data.es_lider) {
            //     display.textContent = `🔥 Tú eres el líder. Pregunta actual: ${data.pregunta_actual_index + 1}`;
            // } else {
            //     display.textContent = "⏳ Esperando al líder...";
            // }

            // Detectamos si avanzó la pregunta
            if (ultimaPreguntaIndex !== null && data.pregunta_actual_index !== ultimaPreguntaIndex) {
                // Redirigir a la vista de juego (alumno)
                redirectLoader.classList.add('active');
                window.location.href = `/preguntasalumno/${codigoPartida}`;
            }

            ultimaPreguntaIndex = data.pregunta_actual_index;

        } catch (err) {
            console.error("Error al consultar estado de partida:", err);
        }
    }

    // Polling cada 1.5 segundos
    setInterval(checkEstado, 1500);
});