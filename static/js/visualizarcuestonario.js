// static/js/visualizar_cuestionario.js
document.addEventListener("DOMContentLoaded", async () => {
  // --- Obtener el ID del cuestionario desde la URL ---
  const partes = window.location.pathname.split("/");
  const cuestionarioId = partes[partes.length - 1]; // Ejemplo: /ver_cuestionario/7 → 7

  // Referencias al DOM
  const titleInput = document.querySelector(".quiz-title-input");
  const descInput = document.querySelector(".quiz-description-input");
  const imgContainer = document.querySelector(".quiz-image-placeholder");
  const questionsGrid = document.querySelector(".questions-grid");
  const questionCount = document.getElementById("question-count");

  try {
    const res = await fetch(`/api/cuestionario_completo/${cuestionarioId}`);
    const data = await res.json();

    if (!res.ok) {
      titleInput.value = "Error al cargar el cuestionario";
      descInput.value = data.error || "No disponible";
      return;
    }

    // --- Mostrar datos del cuestionario ---
    titleInput.value = data.nombre_cuestionario || "Sin título";
    descInput.value = data.descripcion || "Sin descripción";

    if (data.url_img_cuestionario) {
      imgContainer.innerHTML = `<img src="${data.url_img_cuestionario}" alt="Imagen del cuestionario">`;
    } else {
      imgContainer.innerHTML = `<i class="fas fa-image"></i>`;
    }

    // --- Mostrar preguntas ---
    questionsGrid.innerHTML = ""; // limpiar
    questionCount.textContent = data.preguntas.length;

    data.preguntas.forEach((pregunta, index) => {
      const card = document.createElement("div");
      card.classList.add("question-card");

      // Imagen o ícono
      const mediaHTML = pregunta.media_url
        ? `<img src="${pregunta.media_url}" alt="Imagen de la pregunta">`
        : `<i class="fas fa-image"></i>`;

      // Opciones de respuesta
      const respuestasHTML = pregunta.respuestas
        .map((r, i) => {
          const clase = r.estado_respuesta === 1 ? "correct" : "incorrect";
          return `<button class="answer-btn ${clase}">${r.texto_respuesta}</button>`;
        })
        .join("");

      card.innerHTML = `
        <h3 class="question-number">Pregunta ${String(index + 1).padStart(2, "0")}</h3>
        <div class="question-content-placeholder">
          ${mediaHTML}
        </div>
        <div class="answer-options">
          ${respuestasHTML}
        </div>
      `;

      questionsGrid.appendChild(card);
    });
  } catch (err) {
    console.error("Error al cargar cuestionario:", err);
    titleInput.value = "Error de conexión";
    descInput.value = "No se pudo obtener la información del cuestionario.";
  }
});
