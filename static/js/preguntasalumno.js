// static/js/preguntasalumno.js
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
    let cuestionarioData = null;
    let preguntaActual = 0;
    let tiempoRestante = 30;
    let timerInterval = null;
    let pollingInterval = null;
    let respuestaSeleccionada = null;
    let esLider = false;
    let yaRespondi = false;

    // ===================================================================
    // Cargar datos del cuestionario desde sessionStorage
    // ===================================================================
    function cargarCuestionario() {
        const stored = sessionStorage.getItem("cuestionario_actual");
        if (!stored) {
            console.error("❌ No se encontró cuestionario en sessionStorage");
            return null;
        }

        try {
            const data = JSON.parse(stored);
            console.log("✅ Cuestionario cargado:", data);
            return data;
        } catch (error) {
            console.error("❌ Error al parsear cuestionario:", error);
            return null;
        }
    }

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
    // Mostrar pregunta
    // ===================================================================
    function mostrarPregunta(index) {
        if (!cuestionarioData || !cuestionarioData.preguntas) return;

        const pregunta = cuestionarioData.preguntas[index];
        if (!pregunta) {
            console.error("❌ Pregunta no encontrada en índice:", index);
            return;
        }

        preguntaActual = index;
        yaRespondi = false;
        respuestaSeleccionada = null;

        // Actualizar contador
        currentQuestion.textContent = index + 1;
        totalQuestions.textContent = cuestionarioData.preguntas.length;

        // Mostrar texto
        questionText.textContent = pregunta.texto_pregunta || pregunta.texto || "Pregunta sin texto";

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
        respuestaSeleccionada = respuesta;

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
            const tiempoRespuesta = cuestionarioData.preguntas[preguntaActual].tiempo_limite - tiempoUsado;

            const response = await fetch(`/api/juego/responder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    participante_id: participanteId,
                    pregunta_id: cuestionarioData.preguntas[preguntaActual].pregunta_id,
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

            // Enviar respuesta en blanco
            await enviarRespuesta(null, 0);

            // Mostrar pantalla de espera
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
                if (data.pregunta_actual !== undefined && data.pregunta_actual !== preguntaActual) {
                    console.log(`🔄 Avanzando a pregunta ${data.pregunta_actual + 1}`);
                    mostrarPregunta(data.pregunta_actual);
                }

                // Verificar si la partida finalizó
                if (data.estado_partida === 'finalizada') {
                    detenerPolling();
                    window.location.href = `/resultados_alumno/${codigoPartida}`;
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
        cuestionarioData = cargarCuestionario();
        if (!cuestionarioData) return;

        // Verificar si es líder (modo grupal)
        await verificarSiEsLider();

        // Mostrar primera pregunta
        mostrarPregunta(0);

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