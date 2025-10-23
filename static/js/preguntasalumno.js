// static/js/preguntasalumno.js - VERSIÓN CORREGIDA
document.addEventListener("DOMContentLoaded", async () => {
    console.log("👨‍🎓 Vista alumno cargada");

    const codigoPartida = document.body.dataset.codigoPartida;
    const usuarioId = document.body.dataset.usuarioId;
    const participanteId = document.body.dataset.participanteId;

    // Elementos del DOM
    const questionContainer = document.getElementById("questionContainer");
    const waitingScreen = document.getElementById("waitingScreen");
    const questionText = document.getElementById("questionText");
    const questionImage = document.getElementById("questionImage");
    const answersContainer = document.getElementById("answersContainer");
    const timerValue = document.getElementById("timerValue");
    const timerCircle = document.getElementById("timerCircle");
    const currentQuestion = document.getElementById("currentQuestion");
    const totalQuestions = document.getElementById("totalQuestions");
    const leaderIndicator = document.getElementById("leaderIndicator");

    // Estado
    let preguntaActual = 0;
    let tiempoRestante = 30;
    let timerInterval = null;
    let pollingInterval = null;
    let yaRespondi = false;
    let esLider = false;

    // ===================================================================
    // Verificar si el usuario es líder (modo grupal)
    // ===================================================================
    async function verificarSiEsLider() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/poll`);
            if (!response.ok) return false;

            const data = await response.json();
            if (!data.success) return false;

            const miParticipante = data.participantes.find(
                p => p.usuario_id === parseInt(usuarioId)
            );

            if (!miParticipante) return false;

            esLider = miParticipante.lider_id === miParticipante.participante_id;
            
            if (esLider) {
                leaderIndicator.classList.add("show");
            }

            return esLider;

        } catch (error) {
            console.error("❌ Error verificando líder:", error);
            return false;
        }
    }

    // ===================================================================
    // Cargar pregunta desde el servidor
    // ===================================================================
    async function cargarPreguntaActual() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/pregunta_actual`);
            if (!response.ok) {
                throw new Error('Error al cargar pregunta');
            }

            const data = await response.json();
            
            if (!data.success) {
                console.error("❌ Error en respuesta:", data.error);
                return null;
            }

            if (data.finalizada) {
                console.log("🏁 Partida finalizada");
                window.location.href = `/resultados_alumno/${codigoPartida}`;
                return null;
            }

            return data.pregunta;

        } catch (error) {
            console.error("❌ Error cargando pregunta:", error);
            return null;
        }
    }

    // ===================================================================
    // Mostrar pregunta
    // ===================================================================
    async function mostrarPregunta() {
        const pregunta = await cargarPreguntaActual();
        
        if (!pregunta) {
            questionText.textContent = "Error al cargar pregunta";
            return;
        }

        yaRespondi = false;

        // Actualizar contador
        currentQuestion.textContent = preguntaActual + 1;
        totalQuestions.textContent = pregunta.total_preguntas || "?";

        // Mostrar texto
        questionText.textContent = pregunta.texto_pregunta || "Pregunta sin texto";

        // Mostrar imagen si existe
        if (pregunta.media_url) {
            questionImage.src = pregunta.media_url;
            questionImage.style.display = "block";
        } else {
            questionImage.style.display = "none";
        }

        // Mostrar respuestas
        mostrarRespuestas(pregunta.respuestas || []);

        // Obtener tiempo límite
        tiempoRestante = pregunta.tiempo_limite || 30;

        // Mostrar contenedor de pregunta
        questionContainer.style.display = "block";
        waitingScreen.classList.remove("active");

        // Iniciar timer
        iniciarTimer();
    }

    // ===================================================================
    // Mostrar respuestas
    // ===================================================================
    function mostrarRespuestas(respuestas) {
        answersContainer.innerHTML = "";

        const labels = ['A', 'B', 'C', 'D', 'E', 'F'];

        respuestas.forEach((respuesta, index) => {
            const btn = document.createElement("button");
            btn.className = "answer-btn";
            btn.innerHTML = `
                <div class="answer-label">${labels[index]}</div>
                <span>${respuesta.texto_respuesta || respuesta.texto || 'Sin texto'}</span>
            `;

            // Solo permitir responder si es líder (modo grupal) o modo individual
            if (esLider || !leaderIndicator.classList.contains("show")) {
                btn.addEventListener("click", () => seleccionarRespuesta(btn, respuesta, index));
            } else {
                btn.disabled = true;
                btn.style.opacity = "0.5";
                btn.style.cursor = "not-allowed";
            }

            answersContainer.appendChild(btn);
        });
    }

    // ===================================================================
    // Seleccionar respuesta
    // ===================================================================
    async function seleccionarRespuesta(btn, respuesta, index) {
        if (yaRespondi) return;

        yaRespondi = true;

        // Marcar visualmente
        document.querySelectorAll(".answer-btn").forEach(b => {
            b.classList.remove("selected");
            b.disabled = true;
        });
        btn.classList.add("selected");

        // Detener timer
        if (timerInterval) {
            clearInterval(timerInterval);
        }

        // Enviar respuesta al servidor
        await enviarRespuesta(respuesta.respuesta_id, tiempoRestante);

        // Mostrar pantalla de espera
        mostrarPantallaEspera();
    }

    // ===================================================================
    // Enviar respuesta al servidor
    // ===================================================================
    async function enviarRespuesta(respuestaId, tiempoUsado) {
        try {
            const pregunta = await cargarPreguntaActual();
            if (!pregunta) return;

            const tiempoRespuesta = pregunta.tiempo_limite - tiempoUsado;

            const response = await fetch(`/api/juego/responder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    participante_id: participanteId,
                    pregunta_id: pregunta.pregunta_id,
                    respuesta_seleccionada_id: respuestaId,
                    tiempo_respuesta: tiempoRespuesta
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log("✅ Respuesta enviada:", data);
            } else {
                console.error("❌ Error al enviar respuesta:", data.message);
            }

        } catch (error) {
            console.error("❌ Error enviando respuesta:", error);
        }
    }

    // ===================================================================
    // Timer visual
    // ===================================================================
    function iniciarTimer() {
        if (timerInterval) clearInterval(timerInterval);

        const tiempoInicial = tiempoRestante;
        let transcurrido = 0;

        const circumference = 2 * Math.PI * 42;
        timerCircle.style.strokeDasharray = circumference;
        timerCircle.style.strokeDashoffset = 0;

        timerInterval = setInterval(() => {
            transcurrido++;
            tiempoRestante = tiempoInicial - transcurrido;

            timerValue.textContent = Math.max(0, tiempoRestante);

            const offset = (transcurrido / tiempoInicial) * circumference;
            timerCircle.style.strokeDashoffset = offset;

            if (transcurrido >= tiempoInicial) {
                clearInterval(timerInterval);
                tiempoAgotado();
            }
        }, 1000);
    }

    // ===================================================================
    // Tiempo agotado
    // ===================================================================
    async function tiempoAgotado() {
        console.log("⏰ Tiempo agotado");

        if (!yaRespondi) {
            yaRespondi = true;
            await enviarRespuesta(null, 0);
            mostrarPantallaEspera();
        }
    }

    // ===================================================================
    // Mostrar pantalla de espera
    // ===================================================================
    function mostrarPantallaEspera() {
        questionContainer.style.display = "none";
        waitingScreen.classList.add("active");
    }

    // ===================================================================
    // Polling: Detectar avance de pregunta
    // ===================================================================
    async function pollEstadoPartida() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/poll`);
            if (!response.ok) return;

            const data = await response.json();

            if (data.success) {
                // Verificar si cambió la pregunta actual
                const preguntaServer = data.pregunta_actual || 0;
                
                if (preguntaServer !== preguntaActual) {
                    console.log(`🔄 Avanzando a pregunta ${preguntaServer + 1}`);
                    preguntaActual = preguntaServer;
                    await mostrarPregunta();
                }

                // Verificar si la partida finalizó
                if (data.estado_partida === 'finalizada') {
                    detenerPolling();
                    window.location.href = `/resultados_alumno/${codigoPartida}`;
                }

                // Si el profesor está mostrando resultados (entre preguntas), redirigir al alumno a la vista de feedback
                // aceptamos tanto 'entre_preguntas' (código) como 'entre_preguntas' de BD o 'mostrar_resultados'
                const estado = data.estado_partida || data.estado || '';
                if (estado === 'entre_preguntas' || estado === 'mostrar_resultados' || estado === 'EN_RESULTS') {
                    detenerPolling();
                    // redirigir a la plantilla de feedback del alumno
                    window.location.href = `/respuesta_alumno/${codigoPartida}`;
                }
            }

        } catch (error) {
            console.error("❌ Error en polling:", error);
        }
    }

    // ===================================================================
    // Iniciar/Detener polling
    // ===================================================================
    function iniciarPolling() {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(pollEstadoPartida, 2000);
    }

    function detenerPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    // ===================================================================
    // Inicializar partida
    // ===================================================================
    async function inicializarPartida() {
        // Verificar si es líder (modo grupal)
        await verificarSiEsLider();

        // Mostrar primera pregunta
        await mostrarPregunta();

        // Iniciar polling
        iniciarPolling();
    }

    // ===================================================================
    // Limpiar al salir
    // ===================================================================
    window.addEventListener("beforeunload", () => {
        detenerPolling();
        if (timerInterval) clearInterval(timerInterval);
    });

    // ===================================================================
    // Inicializar
    // ===================================================================
    inicializarPartida();

    console.log("✅ Vista alumno inicializada");
});