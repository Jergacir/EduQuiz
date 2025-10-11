document.addEventListener("DOMContentLoaded", async () => {
    const usuarioId = document.body.dataset.usuarioId; // Lee el atributo data-usuario-id
    if (!usuarioId) {
        console.error("No se encontró el usuarioId en el body");
        return;
    }

    const privadosContainer = document.querySelector("section.quiz-section:nth-of-type(1) .quiz-grid");
    const publicosContainer = document.querySelector("section.quiz-section:nth-of-type(2) .quiz-grid");

    async function fetchCuestionarios() {
        try {
            const response = await fetch(`/api/cuestionarios/${usuarioId}`);
            if (!response.ok) throw new Error("Error al obtener cuestionarios");
            const data = await response.json();
            return data;
        } catch (err) {
            console.error(err);
            return [];
        }
    }

    function crearCard(cuestionario) {
        const card = document.createElement("div");
        card.classList.add("quiz-card", "professor");

        card.innerHTML = `
            <div class="quiz-image">
                <img src="${cuestionario.url_img_cuestionario || '/static/img/default_quiz.png'}" alt="Imagen del cuestionario">
            </div>
            <span class="quiz-questions">${cuestionario.num_preguntas || 0} preguntas</span>
            <h3 class="quiz-title">${cuestionario.nombre_cuestionario}</h3>
            <p class="quiz-description">${cuestionario.descripcion || ''}</p>
            <div class="quiz-actions">
                <a href="/editar_cuestionario/${cuestionario.cuestionario_id}" class="btn-edit">Editar</a>
                <i class="action-icon icon-play" title="Jugar/Asignar"></i>
                <i class="action-icon icon-copy" title="Duplicar"></i>
            </div>
        `;
        return card;
    }

    const cuestionarios = await fetchCuestionarios();

    // Limpiar contenedores
    privadosContainer.innerHTML = "";
    publicosContainer.innerHTML = "";

    cuestionarios.forEach(c => {
        const card = crearCard(c);
        if (c.publico) {
            publicosContainer.appendChild(card);
        } else {
            privadosContainer.appendChild(card);
        }
    });
});
