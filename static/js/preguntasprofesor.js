// static/js/preguntasprofesor.js
document.addEventListener("DOMContentLoaded", async () => {
    console.log("👨‍🏫 Vista profesor cargada");

    const codigoPartida = document.body.dataset.codigoPartida;

    // Elementos del DOM
    const cuestionarioNombre = document.getElementById("cuestionarioNombre");
    const totalParticipantes = document.getElementById("totalParticipantes");
    const preguntaActualSpan = document.getElementById("preguntaActual");
    const totalPreguntasSpan = document.getElementById("totalPreguntas");
    const preguntaTexto = document.getElementById("preguntaTexto");
    const preguntaMedia = document.getElementById("preguntaMedia");
    const answersGrid = document.getElementById("answersGrid");
    const timerFill = document.getElementById("timerFill");
    const respondidos = document.getElementById("respondidos");
    const totalAlumnos = document.getElementById("totalAlumnos");
    const progressCircle = document.getElementById("progressCircle");
    const progressPercent = document.getElementById("progressPercent");
    const responseIndicator = document.getElementById("responseIndicator");
    const btnContinuar = document.getElementById("btnContinuar");

    // Estado
    let cuestionarioData = null;
    let preguntaActual = 0;
    let tiempoRestante = 30;
    let timerInterval = null;
    let pollingInterval = null;
    let todosRespondieron = false;

    // ===================================================================
    // Cargar datos del cuestionario desde sessionStorage
    // ===================================================================
    function cargarCuestionario() {
        const stored = sessionStorage.getItem("cuestionario_actual");
        if (!stored) {
            console.error("❌ No se encontró cuestionario en sessionStorage");
            preguntaTexto.textContent = "Error: Cuestionario no encontrado";
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
    // Inicializar partida
    // ===================================================================
    async function inicializarPartida() {
        cuestionarioData = cargarCuestionario();
        if (!cuestionarioData) return;

        // Actualizar UI con datos del cuestionario
        cuestionarioNombre.textContent = cuestionarioData.nombre_cuestionario || "Cuestionario";
        totalPreguntasSpan.textContent = cuestionarioData.preguntas?.length || 0;

        // Obtener total de participantes
        await actualizarParticipantes();

        // Mostrar primera pregunta
        mostrarPregunta(0);

        // Iniciar polling de respuestas
        iniciarPolling();
    }

    // ===================================================================
    // Mostrar respuestas
    // ===================================================================
    function mostrarRespuestas(respuestas) {
        answersGrid.innerHTML = "";

        const labels = ['A', 'B', 'C', 'D', 'E', 'F'];

        respuestas.forEach((respuesta, index) => {
            const div = document.createElement("div");
            div.className = "answer-option";
            div.innerHTML = `
                <div class="answer-label">${labels[index]}</div>
                <span>${respuesta.texto_respuesta || respuesta.texto || 'Sin texto'}</span>
            `;
            answersGrid.appendChild(div);
        });
    }

    // ===================================================================
    // Timer visual
    // ===================================================================
    function iniciarTimer() {
        if (timerInterval) clearInterval(timerInterval);

        const tiempoInicial = tiempoRestante;
        let transcurrido = 0;

        timerFill.style.width = "100%";

        timerInterval = setInterval(() => {
            transcurrido++;
            const porcentaje = ((tiempoInicial - transcurrido) / tiempoInicial) * 100;
            timerFill.style.width = `${Math.max(0, porcentaje)}%`;

            if (transcurrido >= tiempoInicial) {
                clearInterval(timerInterval);
                tiempoAgotado();
            }
        }, 1000);
    }

    // ===================================================================
    // Tiempo agotado
    // ===================================================================
    function tiempoAgotado() {
        console.log("⏰ Tiempo agotado");
        
        // Marcar respuestas no contestadas como incorrectas
        marcarRespuestasNoContestadas();
        
        // Mostrar respuestas correctas
        mostrarRespuestasCorrectas();
        
        // Habilitar botón continuar
        btnContinuar.disabled = false;
        responseIndicator.textContent = "¡Tiempo agotado! Puedes continuar.";
        responseIndicator.classList.add("complete");
    }

    // ===================================================================
    // Marcar respuestas no contestadas como incorrectas
    // ===================================================================
    async function marcarRespuestasNoContestadas() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/marcar_no_respondidas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pregunta_index: preguntaActual
                })
            });

            if (!response.ok) {
                console.error("Error al marcar respuestas no contestadas");
            }
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // ===================================================================
    // Mostrar respuestas correctas (bordear en verde/rojo)
    // ===================================================================
    function mostrarRespuestasCorrectas() {
        if (!cuestionarioData || !cuestionarioData.preguntas) return;

        const pregunta = cuestionarioData.preguntas[preguntaActual];
        if (!pregunta || !pregunta.respuestas) return;

        const answerOptions = answersGrid.querySelectorAll(".answer-option");

        pregunta.respuestas.forEach((respuesta, index) => {
            if (answerOptions[index]) {
                if (respuesta.estado_respuesta === 1) {
                    answerOptions[index].classList.add("correct");
                } else {
                    answerOptions[index].classList.add("incorrect");
                }
            }
        });
    }

    // ===================================================================
    // Polling de respuestas recibidas
    // ===================================================================
    async function actualizarParticipantes() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/poll`);
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            // Actualizar total de participantes
            const total = data.total || 0;
            totalParticipantes.textContent = total;
            totalAlumnos.textContent = total;

            // Obtener respuestas recibidas de la pregunta actual
            const respuestasRecibidas = await obtenerRespuestasRecibidas();

            // Actualizar UI
            respondidos.textContent = respuestasRecibidas;
            
            // Calcular porcentaje
            const porcentaje = total > 0 ? Math.round((respuestasRecibidas / total) * 100) : 0;
            progressPercent.textContent = `${porcentaje}%`;

            // Actualizar círculo de progreso
            const circumference = 2 * Math.PI * 52; // radio = 52
            const offset = circumference - (porcentaje / 100) * circumference;
            progressCircle.style.strokeDashoffset = offset;

            // Verificar si todos respondieron
            if (respuestasRecibidas >= total && total > 0 && !todosRespondieron) {
                todosRespondieron = true;
                todosHanRespondido();
            }

        } catch (error) {
            console.error("Error en polling:", error);
        }
    }

    // ===================================================================
    // Obtener cantidad de respuestas recibidas
    // ===================================================================
    async function obtenerRespuestasRecibidas() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/respuestas_recibidas?pregunta_index=${preguntaActual}`);
            if (!response.ok) return 0;

            const data = await response.json();
            return data.respuestas_recibidas || 0;
        } catch (error) {
            console.error("Error obteniendo respuestas:", error);
            return 0;
        }
    }

    // ===================================================================
    // Todos han respondido
    // ===================================================================
    function todosHanRespondido() {
        console.log("✅ Todos han respondido");

        // Detener timer
        if (timerInterval) {
            clearInterval(timerInterval);
        }

        // Mostrar respuestas correctas
        mostrarRespuestasCorrectas();

        // Actualizar indicador
        responseIndicator.textContent = "✅ ¡Todos han respondido!";
        responseIndicator.classList.add("complete");

        // Habilitar botón
        btnContinuar.disabled = false;
    }

    // ===================================================================
    // Iniciar polling
    // ===================================================================
    function iniciarPolling() {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(actualizarParticipantes, 1500);
    }

    // ===================================================================
    // Detener polling
    // ===================================================================
    function detenerPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    // ===================================================================
    // Botón Continuar
    // ===================================================================
    btnContinuar.addEventListener("click", async () => {
        btnContinuar.disabled = true;
        btnContinuar.textContent = "Avanzando...";

        // Verificar si hay más preguntas
        if (preguntaActual + 1 < cuestionarioData.preguntas.length) {
            // Avanzar a siguiente pregunta
            await avanzarPregunta();
            mostrarPregunta(preguntaActual + 1);
            btnContinuar.textContent = "Continuar a Siguiente Pregunta";
        } else {
            // No hay más preguntas, finalizar partida
            await finalizarPartida();
        }
    });

    // ===================================================================
    // Avanzar pregunta en el servidor
    // ===================================================================
    async function avanzarPregunta() {
        try {
            const response = await fetch(`/api/partida/${codigoPartida}/avanzar_pregunta`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                console.error("Error al avanzar pregunta");
            }
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // ===================================================================
    // Finalizar partida
    // ===================================================================
    async function finalizarPartida() {
        try {
            const response = await fetch(`/api/partida/finalizar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo_partida: codigoPartida })
            });

            if (response.ok) {
                console.log("✅ Partida finalizada");
                detenerPolling();
                
                // Redirigir a resultados
                const data = await response.json();
                if (data.partida_id) {
                    window.location.href = `/resultados_partida/${data.partida_id}`;
                }
            }
        } catch (error) {
            console.error("Error al finalizar:", error);
        }
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

    console.log("✅ Vista profesor inicializada");
}); pregunta
    // ===================================================================
    function mostrarPregunta(index) {
        if (!cuestionarioData || !cuestionarioData.preguntas) return;

        const pregunta = cuestionarioData.preguntas[index];
        if (!pregunta) {
            console.error("❌ Pregunta no encontrada en índice:", index);
            return;
        }

        preguntaActual = index;

        // Actualizar contador
        preguntaActualSpan.textContent = index + 1;

        // Mostrar texto
        preguntaTexto.textContent = pregunta.texto_pregunta || pregunta.texto || "Pregunta sin texto";

        // Mostrar imagen si existe
        if (pregunta.media_url) {
            preguntaMedia.src = pregunta.media_url;
            preguntaMedia.style.display = "block";
        } else {
            preguntaMedia.style.display = "none";
        }

        // Mostrar respuestas
        mostrarRespuestas(pregunta.respuestas || []);

        // Obtener tiempo límite
        tiempoRestante = pregunta.tiempo_limite || 30;

        // Resetear estado
        todosRespondieron = false;
        btnContinuar.disabled = true;
        responseIndicator.classList.remove("complete");
        responseIndicator.textContent = "Esperando respuestas...";

        // Iniciar timer
        iniciarTimer();
    }

    // ===================================================================
    // Mostrar