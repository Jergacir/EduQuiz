document.addEventListener("DOMContentLoaded", async () => {
    const usuarioId = document.body.dataset.usuarioId;
    const tipoUsuario = document.body.dataset.tipoUsuario; // 'P' o 'A'

    if (!usuarioId || !tipoUsuario) {
        console.error("No se encontró usuarioId o tipoUsuario");
        return;
    }

    // Contenedores
    const privadosContainer = document.querySelector("#privados-container");
    const publicosContainer = document.querySelector("#publicos-container");
    const comunidadContainer = document.querySelector("#comunidad-container");

    // --- Obtener cuestionarios ---
    async function fetchCuestionariosProfesor() {
        const res = await fetch(`/api/cuestionarios/${usuarioId}`);
        return res.ok ? res.json() : [];
    }

    async function fetchCuestionariosAlumnos() {
        const res = await fetch(`/api/cuestionarios_publicos`);
        return res.ok ? res.json() : [];
    }

    // --- Crear card ---
    function crearCardProfesor(cuestionario) {
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
                <i class="fa-solid fa-play action-icon" title="Jugar/Asignar"></i>
                <i class="fa-solid fa-trash action-icon icon-delete" title="Eliminar"></i>
            </div>
        `;
        return card;
    }

    function crearCardAlumno(cuestionario) {
        const card = document.createElement("div");
        card.classList.add("quiz-card", "student");

        card.innerHTML = `
        <div class="quiz-image">
            <img src="${cuestionario.url_img_cuestionario }" alt="Imagen del cuestionario">
        </div>
        <span class="quiz-questions">${cuestionario.num_preguntas || 0} preguntas</span>
        <h3 class="quiz-title">${cuestionario.nombre_cuestionario}</h3>
        <p class="quiz-description">${cuestionario.descripcion || ''}</p>
        <div class="quiz-actions">
            <a href="" class="btn-visualize">
                <i class="fa-solid fa-eye"></i> Visualizar
            </a>
        </div>
    `;
        return card;
    }

    // --- Renderizado según tipo ---
    if (tipoUsuario === 'P') {
        const cuestionarios = await fetchCuestionariosProfesor();

        privadosContainer.innerHTML = "";
        publicosContainer.innerHTML = "";

        cuestionarios.forEach(c => {
            const card = crearCardProfesor(c);
            if (c.publico) {
                publicosContainer.appendChild(card);
            } else {
                privadosContainer.appendChild(card);
            }

            // Evento de eliminar
            const deleteIcon = card.querySelector(".icon-delete");
            if (deleteIcon) {
                deleteIcon.addEventListener("click", () => {
                    abrirModalConfirmacion(c.cuestionario_id, card);
                });
            }
        });
    }
    else if (tipoUsuario === 'A') {
        const cuestionarios = await fetchCuestionariosAlumnos();

        comunidadContainer.innerHTML = "";
        cuestionarios.forEach(c => {
            const card = crearCardAlumno(c);
            comunidadContainer.appendChild(card);
        });
    }

    // --- Modal de confirmación ---
    const modal = document.getElementById("confirmDeleteModal");
    const btnCancel = document.getElementById("cancelDelete");
    const btnConfirm = document.getElementById("confirmDelete");
    let cuestionarioAEliminar = null;
    let cardAEliminar = null;

    function abrirModalConfirmacion(id, card) {
        cuestionarioAEliminar = id;
        cardAEliminar = card;
        modal.classList.remove("hidden");
    }

    btnCancel.addEventListener("click", () => {
        modal.classList.add("hidden");
        cuestionarioAEliminar = null;
    });

    btnConfirm.addEventListener("click", async () => {
        if (!cuestionarioAEliminar) return;
        try {
            const res = await fetch(`/api/cuestionarios/${cuestionarioAEliminar}`, {
                method: "PUT"
            });
            const data = await res.json();

            if (data.status === "ok") {
                cardAEliminar.remove();
            } else {
                alert("Error al eliminar: " + (data.mensaje || "desconocido"));
            }
        } catch (err) {
            console.error("Error al eliminar:", err);
            alert("Ocurrió un error en la conexión.");
        } finally {
            modal.classList.add("hidden");
            cuestionarioAEliminar = null;
        }
    });
});
