document.addEventListener("DOMContentLoaded", async () => {
  const quizSearchInput = document.getElementById("quiz-search-input");

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
            <div class="quiz-badge">${
              cuestionario.num_preguntas || 0
            } preguntas</div>
                    <div class="quiz-image-placeholder"><i class="fas fa-image"></i></div>
                    <div class="quiz-content">
                        <h3 title="${cuestionario.nombre_cuestionario}">${
      cuestionario.nombre_cuestionario || "Cuestionario sin Título"
    }</h3>
                        <p>${cuestionario.descripcion || "Sin descripción"}</p>
                         ${
                           cuestionario.codigo_visualizacion
                             ? `
            <p class="quiz-code">
                Código de visualización: 
                <strong>${cuestionario.codigo_visualizacion}</strong>
            </p>
        `
                             : ""
                         }
                        <div class="quiz-actions" style="gap:10px">
                            <div class="div-edit-btn" style="width: 100%; display: flex; background-color: var(--color-primary-teal); padding: 5px; border-radius: 12px; justify-content: center; align-items: center;">
                                <a href="/editar_cuestionario/${
                                  cuestionario.cuestionario_id
                                }" class="edit-btn"><i class="fas fa-edit" style="margin-right:4px"></i> Editar</a>
                            </div>
                            <div class="action-icons">
                                <button title="Jugar" class="action-icon-btn play"><i class="fa-solid fa-gamepad"></i></button>
                                <button data-id="${
                                  cuestionario.cuestionario_id
                                }" title="Clonar" class="action-icon-btn clone clone-quiz-btn"><i class="fas fa-copy"></i></button>
                                <button title="Eliminar" class="action-icon-btn play"><i class="fa-solid fa-trash icon-delete"></i></button>
                                
                            </div>
                        </div>
                    </div>
        `;
    return card;
  }

  function crearCardAlumno(cuestionario) {
    const card = document.createElement("div");
    card.classList.add("quiz-card", "student");

    card.innerHTML = `
        <div class="quiz-badge">${
          cuestionario.num_preguntas || 0
        } preguntas</div>
                    <div class="quiz-image-placeholder"><i class="fas fa-image"></i></div>
                    <div class="quiz-content">
                        <h3 title="${cuestionario.nombre_cuestionario}">${
      cuestionario.nombre_cuestionario || "Cuestionario sin Título"
    }</h3>
                        <p>${cuestionario.descripcion || "Sin descripción"}</p>
                        <div class="quiz-actions">
                            <button class="btn-visualize" style="width: 100%; display: flex; background-color: var(--color-primary-teal); padding: 5px; border-radius: 12px; justify-content: center; align-items: center;border:none;" data-id="${
                              cuestionario.cuestionario_id
                            }">
                <i class="fa-solid fa-eye" style="margin-right:4px"></i> Visualizar
            </button>
                        </div>
                    </div>
    `;

    // Evento para abrir el modal al hacer clic
    const btn = card.querySelector(".btn-visualize");
    btn.addEventListener("click", () =>
      abrirModalVisualizar(cuestionario.cuestionario_id)
    );
    return card;
  }

  // --- Renderizado según tipo ---
  if (tipoUsuario === "P") {
    const cuestionarios = await fetchCuestionariosProfesor();

    privadosContainer.innerHTML = "";
    publicosContainer.innerHTML = "";

    cuestionarios.forEach((c) => {
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
  } else if (tipoUsuario === "A") {
    const cuestionarios = await fetchCuestionariosAlumnos();

    comunidadContainer.innerHTML = "";
    cuestionarios.forEach((c) => {
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
        method: "PUT",
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

  const modalVisualizar = document.getElementById("visualizarModal");
  const cancelCodeBtn = document.getElementById("cancelCode");
  const verifyCodeBtn = document.getElementById("verifyCode");
  const codeInputs = document.querySelectorAll(".code-box");
  const errorText = document.getElementById("code-error");

  let cuestionarioSeleccionado = null;

  // --- Manejo de inputs del código (escribir, borrar y pegar completo) ---
  codeInputs.forEach((input, index) => {
    // Avanzar automáticamente
    input.addEventListener("input", (e) => {
      if (
        e.inputType !== "insertFromPaste" &&
        input.value.length === 1 &&
        index < codeInputs.length - 1
      ) {
        codeInputs[index + 1].focus();
      }
    });

    // Retroceder con Backspace
    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && index > 0) {
        codeInputs[index - 1].focus();
      }
    });

    // Detectar pegado completo (Ctrl+V)
    input.addEventListener("paste", (e) => {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData)
        .getData("text")
        .trim();
      if (!pasted) return;

      // Tomar los primeros 6 caracteres (sin espacios)
      const chars = pasted.replace(/\s+/g, "").slice(0, 6).split("");
      codeInputs.forEach((box, i) => {
        box.value = chars[i] || "";
      });

      // Si se llenan los 6, mover foco al final
      const filled = Array.from(codeInputs).filter((i) => i.value).length;
      if (filled === 6) codeInputs[5].focus();
    });
  });

  // Abrir modal
  function abrirModalVisualizar(cuestionarioId) {
    cuestionarioSeleccionado = cuestionarioId;
    modalVisualizar.classList.remove("hidden");
    codeInputs[0].focus();
    codeInputs.forEach((input) => (input.value = "")); // limpiar
    errorText.classList.add("hidden");
  }

  // Cerrar modal
  cancelCodeBtn.addEventListener("click", () => {
    modalVisualizar.classList.add("hidden");
  });

  // Pasar al siguiente input automáticamente
  codeInputs.forEach((input, idx) => {
    input.addEventListener("input", () => {
      if (input.value.length === 1 && idx < codeInputs.length - 1) {
        codeInputs[idx + 1].focus();
      }
    });
  });

  // Verificar código
  verifyCodeBtn.addEventListener("click", async () => {
    const code = Array.from(codeInputs)
      .map((i) => i.value)
      .join("");

    if (code.length !== 6) {
      errorText.textContent = "Debes ingresar los 6 dígitos.";
      errorText.classList.remove("hidden");
      return;
    }

    // Aquí puedes hacer fetch al backend para verificar
    const response = await fetch(
      `/verificar_codigo/${cuestionarioSeleccionado}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo: code }),
      }
    );

    const data = await response.json();

    if (data.valido) {
      // Redirigir al cuestionario
      window.location.href = `/ver_cuestionario/${cuestionarioSeleccionado}`;
    } else {
      errorText.textContent = "Código incorrecto. Inténtalo de nuevo.";
      errorText.classList.remove("hidden");
    }
  });

  // Búsqueda en tiempo real
  quizSearchInput.addEventListener("input", (e) => {
    //Implementar la lógica de búsqueda 
  });
});
