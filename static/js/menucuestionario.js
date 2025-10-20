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
            ${cuestionario.codigo_visualizacion ? `
            <p class="quiz-code">
                Código de visualización: 
                <strong>${cuestionario.codigo_visualizacion}</strong>
            </p>
        ` : ''}
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
            <img src="${cuestionario.url_img_cuestionario}" alt="Imagen del cuestionario">
        </div>
        <span class="quiz-questions">${cuestionario.num_preguntas || 0} preguntas</span>
        <h3 class="quiz-title">${cuestionario.nombre_cuestionario}</h3>
        <p class="quiz-description">${cuestionario.descripcion || ''}</p>
        <div class="quiz-actions">
            <button class="btn-visualize" data-id="${cuestionario.cuestionario_id}">
                <i class="fa-solid fa-eye"></i> Visualizar
            </button>
        </div>
    `;

        // Evento para abrir el modal al hacer clic
        const btn = card.querySelector(".btn-visualize");
        btn.addEventListener("click", () => abrirModalVisualizar(cuestionario.cuestionario_id));
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
            if (e.inputType !== "insertFromPaste" && input.value.length === 1 && index < codeInputs.length - 1) {
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
            const pasted = (e.clipboardData || window.clipboardData).getData("text").trim();
            if (!pasted) return;

            // Tomar los primeros 6 caracteres (sin espacios)
            const chars = pasted.replace(/\s+/g, "").slice(0, 6).split("");
            codeInputs.forEach((box, i) => {
                box.value = chars[i] || "";
            });

            // Si se llenan los 6, mover foco al final
            const filled = Array.from(codeInputs).filter(i => i.value).length;
            if (filled === 6) codeInputs[5].focus();
        });
    });

    // Abrir modal
    function abrirModalVisualizar(cuestionarioId) {
        cuestionarioSeleccionado = cuestionarioId;
        modalVisualizar.classList.remove("hidden");
        codeInputs[0].focus();
        codeInputs.forEach(input => input.value = ""); // limpiar
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
        const code = Array.from(codeInputs).map(i => i.value).join("");

        if (code.length !== 6) {
            errorText.textContent = "Debes ingresar los 6 dígitos.";
            errorText.classList.remove("hidden");
            return;
        }

        // Aquí puedes hacer fetch al backend para verificar
        const response = await fetch(`/verificar_codigo/${cuestionarioSeleccionado}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ codigo: code })
        });

        const data = await response.json();

        if (data.valido) {
            // Redirigir al cuestionario
            window.location.href = `/ver_cuestionario/${cuestionarioSeleccionado}`;
        } else {
            errorText.textContent = "Código incorrecto. Inténtalo de nuevo.";
            errorText.classList.remove("hidden");
        }
    });
});


        const QUIZ_STORAGE_KEY = "eduquiz_local_quizzes";

        // Referencias a elementos del DOM
        const addQuizButton = document.getElementById('add-quiz-button');
        const addQuizModal = document.getElementById('add-quiz-modal');
        const closeModalButton = document.getElementById('close-modal-button');
        const addQuizForm = document.getElementById('add-quiz-form');
        const quizList = document.getElementById('quiz-list');
        const noQuizzes = document.getElementById('no-quizzes');
        const loadingQuizzes = document.getElementById('loading-quizzes');
        const sidebar = document.getElementById('sidebar');
        const menuButton = document.getElementById('menu-button');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        const logoutButton = document.getElementById('logout-button');
        const quizSearchInput = document.getElementById('quiz-search-input');

        let allQuizzes = []; // Almacenará la lista completa de cuestionarios

        /**
         * Simula la obtención de datos de Firebase cargando desde localStorage.
         * @returns {Array<Object>} Lista de cuestionarios.
         */
        // Fallback local si la API falla (datos de ejemplo)
        function getLocalFallbackQuizzes() {
            return [
                { id: 'q1', title: 'Matemáticas Básicas', topic: 'Álgebra', questionCount: 10, createdAt: new Date().toISOString() },
                { id: 'q2', title: 'Historia Mundial', topic: 'Guerra Fría', questionCount: 15, createdAt: new Date(Date.now() - 86400000).toISOString() },
                { id: 'q3', title: 'Física Clásica', topic: 'Mecánica', questionCount: 8, createdAt: new Date(Date.now() - 172800000).toISOString() },
                { id: 'q4', title: 'Literatura Clásica', topic: 'Shakespeare', questionCount: 12, createdAt: new Date(Date.now() - 345600000).toISOString() },
            ];
        }

        /**
         * Obtiene los cuestionarios desde la API del servidor.
         * Para profesores trae privados y públicos; para alumnos trae públicos.
         */
        async function fetchQuizzesFromServer() {
            const serverDiv = document.getElementById('server-user-data');
            const userTipo = serverDiv?.dataset.tipo || '';
            const userId = serverDiv?.dataset.userId || '';

            try {
                if (userTipo === 'P' && userId) {
                    // Profesor: traer privados del usuario y además los públicos
                    const [resPriv, resPub] = await Promise.all([
                        fetch(`/api/cuestionarios/${userId}`),
                        fetch('/api/cuestionarios_publicos')
                    ]);

                    const privados = resPriv.ok ? await resPriv.json() : [];
                    const publicos = resPub.ok ? await resPub.json() : [];

                    allQuizzes = [...privados, ...publicos];
                    // Render separado por contenedores
                    renderQuizzes(privados, 'privados-container');
                    renderQuizzes(publicos, 'publicos-container');
                } else {
                    // Alumno / Invitado: ver sólo públicos
                    const res = await fetch('/api/cuestionarios_publicos');
                    const publicos = res.ok ? await res.json() : [];
                    allQuizzes = publicos;
                    renderQuizzes(publicos, 'comunidad-container');
                }
            } catch (err) {
                console.error('Error al obtener cuestionarios desde el servidor:', err);
                // Fallback local
                allQuizzes = getLocalFallbackQuizzes();
                filterAndRenderQuizzes('');
            }
        }

        /**
         * Inicializa la aplicación y carga los datos.
         */
        function initApp() {
            // Cargar datos iniciales desde la API del servidor
            fetchQuizzesFromServer();
        }

        /**
         * Filtra la lista de cuestionarios según un término de búsqueda y luego los renderiza.
         * @param {string} searchTerm - Término de búsqueda.
         */
        function filterAndRenderQuizzes(searchTerm) {
            searchTerm = searchTerm.toLowerCase().trim();

            const filteredQuizzes = allQuizzes.filter(quiz => {
                const titleMatch = (quiz.title || '').toLowerCase().includes(searchTerm);
                const topicMatch = (quiz.topic || '').toLowerCase().includes(searchTerm);
                return titleMatch || topicMatch;
            });

            // Dependiendo del tipo de usuario, distribuir a contenedores
            // Leemos el tipo desde un elemento DOM inyectado por Jinja para evitar romper el parseo JS
            const userTipo = document.getElementById('server-user-data')?.dataset.tipo || '';
            const userIsProfesor = (userTipo === 'P');

            if (userIsProfesor) {
                // separar privados y publicos por una propiedad 'visibility' o similar
                const privados = filteredQuizzes.filter(q => q.visibility === 'private' || q.isPrivate);
                const publicos = filteredQuizzes.filter(q => q.visibility === 'public' || !q.isPrivate);
                renderQuizzes(privados, 'privados-container');
                renderQuizzes(publicos, 'publicos-container');
            } else {
                // alumno -> comunidad
                renderQuizzes(filteredQuizzes, 'comunidad-container');
            }
        }

        /**
         * Dibuja la lista de cuestionarios filtrada en el DOM.
         * @param {Array<Object>} quizzes - Lista de objetos cuestionario.
         */
        function renderQuizzes(quizzes, containerId = 'quiz-list') {
            const container = document.getElementById(containerId) || document.getElementById('quiz-list');
            if (!container) return;
            container.innerHTML = '';

            if (!quizzes || quizzes.length === 0) {
                // si todos los contenedores están vacíos, mostramos el mensaje global
                noQuizzes.style.display = 'block';
                noQuizzes.textContent = allQuizzes.length === 0
                    ? 'Aún no has creado ningún cuestionario. Haz clic en "Crear Cuestionario" para empezar.'
                    : 'No se encontraron cuestionarios que coincidan con la búsqueda.';
                return;
            }
            noQuizzes.style.display = 'none';

            quizzes.forEach(quiz => {
                const quizElement = document.createElement('div');
                quizElement.className = 'quiz-card';

                quizElement.innerHTML = `
                    <div class="quiz-badge">${quiz.questionCount || 0} preguntas</div>
                    <div class="quiz-image-placeholder"><i class="fas fa-image"></i></div>
                    <div class="quiz-content">
                        <h3 title="${quiz.title}">${quiz.title || 'Cuestionario sin Título'}</h3>
                        <p>Tema: ${quiz.topic || 'Desconocido'}</p>
                        <div class="quiz-actions" style="gap:10px">
                            <div class="div-edit-btn" style="width: 100%; display: flex; background-color: var(--color-primary-teal); padding: 5px; border-radius: 12px; justify-content: center; align-items: center;">
                                <button class="edit-btn"><i class="fas fa-edit" style="margin-right:4px"></i> Editar</button>
                            </div>
                            <div class="action-icons">
                                <button title="Jugar" class="action-icon-btn play"><i class="fa-solid fa-gamepad"></i></button>
                                <button data-id="${quiz.id}" title="Clonar" class="action-icon-btn clone clone-quiz-btn"><i class="fas fa-copy"></i></button>
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(quizElement);
            });

            // Reasignar listeners a los botones de eliminar y clonar dentro del container
            attachQuizActionListeners(container);
        }

        /**
         * Asigna listeners a los botones de acción de cada tarjeta de cuestionario.
         */
        function attachQuizActionListeners(container = document) {
            // Use event delegation so we don't accidentally attach many listeners when re-rendering.
            // For element containers we mark them as initialized with a data attribute.
            const isDocument = (container === document);

            if (!isDocument) {
                if (container.dataset.listenersAttached === 'true') return;
                container.dataset.listenersAttached = 'true';

                container.addEventListener('click', function (e) {
                    const deleteBtn = e.target.closest('.delete-quiz-btn');
                    if (deleteBtn && container.contains(deleteBtn)) {
                        e.stopPropagation();
                        const quizId = deleteBtn.getAttribute('data-id');
                        const quiz = allQuizzes.find(q => q.id === quizId);
                        showCustomModal('Confirmar Eliminación', `¿Estás seguro de que quieres eliminar el cuestionario "${quiz?.title || 'este cuestionario'}"?`, () => deleteQuiz(quizId), true);
                        return;
                    }

                    const cloneBtn = e.target.closest('.clone-quiz-btn');
                    if (cloneBtn && container.contains(cloneBtn)) {
                        e.stopPropagation();
                        const quizId = cloneBtn.getAttribute('data-id');
                        cloneQuiz(quizId);
                        return;
                    }
                });
            } else {
                // document-level delegation (used as fallback). Ensure we only attach once.
                if (document.documentElement.dataset.globalListenersAttached === 'true') return;
                document.documentElement.dataset.globalListenersAttached = 'true';

                document.addEventListener('click', function (e) {
                    const deleteBtn = e.target.closest('.delete-quiz-btn');
                    if (deleteBtn) {
                        e.stopPropagation();
                        const quizId = deleteBtn.getAttribute('data-id');
                        const quiz = allQuizzes.find(q => q.id === quizId);
                        showCustomModal('Confirmar Eliminación', `¿Estás seguro de que quieres eliminar el cuestionario "${quiz?.title || 'este cuestionario'}"?`, () => deleteQuiz(quizId), true);
                        return;
                    }

                    const cloneBtn = e.target.closest('.clone-quiz-btn');
                    if (cloneBtn) {
                        e.stopPropagation();
                        const quizId = cloneBtn.getAttribute('data-id');
                        cloneQuiz(quizId);
                        return;
                    }
                });
            }
        }

        /**
         * Añade un nuevo cuestionario a localStorage (simula addDoc).
         * @param {string} title 
         * @param {string} topic 
         */
        async function addQuiz(title, topic) {
            try {
                const newId = Date.now().toString(); // ID simple basado en el tiempo

                // Genera un número de preguntas aleatorio entre 5 y 20 para el ejemplo
                const randomQuestionCount = Math.floor(Math.random() * (20 - 5 + 1)) + 5;

                const newQuiz = {
                    id: newId,
                    title: title,
                    topic: topic,
                    createdAt: new Date().toISOString(),
                    questionCount: randomQuestionCount
                };

                // Actualizamos sólo en memoria (para pruebas). En producción llamar a la API para persistir.
                allQuizzes.push(newQuiz);
                filterAndRenderQuizzes(quizSearchInput.value); // Recargar la lista aplicando el filtro actual

                addQuizModal.classList.remove('visible');
                addQuizForm.reset();
                showCustomModal('Cuestionario Creado', `"${title}" ha sido añadido a tus cuestionarios.`, () => { }, false);

            } catch (error) {
                console.error("Error al añadir cuestionario local:", error);
                showCustomModal('Error', `No se pudo guardar el cuestionario: ${error.message}`, () => { }, false);
            }
        }

        /**
         * Elimina un cuestionario de localStorage (simula deleteDoc).
         * @param {string} quizId 
         */
        async function deleteQuiz(quizId) {
            try {
                const title = allQuizzes.find(q => q.id === quizId)?.title || 'Cuestionario';
                // Actualizamos sólo en memoria y re-renderizamos. Para persistir, llamar a la API correspondiente.
                allQuizzes = allQuizzes.filter(quiz => quiz.id !== quizId);
                filterAndRenderQuizzes(quizSearchInput.value); // Recargar la lista aplicando el filtro actual
                showCustomModal('Eliminado', `"${title}" ha sido eliminado con éxito.`, () => { }, false);

            } catch (error) {
                console.error("Error al eliminar cuestionario local:", error);
                showCustomModal('Error', `No se pudo eliminar el cuestionario: ${error.message}`, () => { }, false);
            }
        }

        /**
         * Clona un cuestionario existente, añade "(Copia)" al título y lo guarda.
         * @param {string} quizId 
         */
        async function cloneQuiz(quizId) {
            try {
                const originalQuiz = allQuizzes.find(quiz => quiz.id === quizId);

                if (!originalQuiz) {
                    showCustomModal('Error', 'Cuestionario original no encontrado para clonar.', () => { }, false);
                    return;
                }

                const newId = Date.now().toString();
                const newTitle = originalQuiz.title.includes('(Copia)')
                    ? originalQuiz.title + ' (Copia)'
                    : originalQuiz.title + ' (Copia)';

                const clonedQuiz = {
                    ...originalQuiz,
                    id: newId,
                    title: newTitle,
                    createdAt: new Date().toISOString(),
                    // Asume el mismo número de preguntas por simplicidad
                };

                // Actualizamos en memoria; para persistir habría que llamar al endpoint de creación
                allQuizzes.push(clonedQuiz);
                filterAndRenderQuizzes(quizSearchInput.value);

                showCustomModal('Cuestionario Clonado', `Se ha creado una copia de "${originalQuiz.title}".`, () => { }, false);

            } catch (error) {
                console.error("Error al clonar cuestionario local:", error);
                showCustomModal('Error', `No se pudo clonar el cuestionario: ${error.message}`, () => { }, false);
            }
        }


        // --- Event Listeners ---

        // Búsqueda en tiempo real
        quizSearchInput.addEventListener('input', (e) => {
            filterAndRenderQuizzes(e.target.value);
        });

        // Toggle de la Navegación Lateral (Sidebar)
        menuButton.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            sidebarOverlay.classList.toggle('visible');
        });

        sidebarOverlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('visible');
        });

        // Cierra la sesión (simulación)
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            // Limpia el localStorage para simular un cierre de sesión
            localStorage.removeItem(QUIZ_STORAGE_KEY);
            showCustomModal('Cierre de Sesión', 'Se ha cerrado la sesión (simuladamente). Recarga la página para volver a iniciar sesión.', () => {
                window.location.reload();
            }, false);
        });


        // Manejo del Modal de Añadir Cuestionario
        addQuizButton.addEventListener('click', () => {
            addQuizModal.classList.add('visible');
        });

        closeModalButton.addEventListener('click', () => {
            addQuizModal.classList.remove('visible');
            addQuizForm.reset();
        });

        addQuizForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('quiz-title').value.trim();
            const topic = document.getElementById('quiz-topic').value.trim();

            if (title && topic) {
                await addQuiz(title, topic);
            }
        });

        // --- Modal Personalizado (Reemplazo de alert/confirm) ---
        function showCustomModal(title, message, onConfirm = null, isConfirm = true) {
            const modal = document.getElementById('custom-alert-modal');
            const confirmBtn = document.getElementById('modal-confirm');
            const cancelBtn = document.getElementById('modal-cancel');

            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;

            // Clonar para limpiar listeners
            const newConfirmBtn = confirmBtn.cloneNode(true);
            const newCancelBtn = cancelBtn.cloneNode(true);
            confirmBtn.replaceWith(newConfirmBtn);
            cancelBtn.replaceWith(newCancelBtn);

            if (isConfirm && onConfirm) {
                // Modo Confirmación (Eliminar usa color rojo)
                newConfirmBtn.textContent = 'Eliminar';
                newConfirmBtn.classList.remove('primary');
                newConfirmBtn.classList.add('delete');
                newCancelBtn.style.display = 'block';

                newConfirmBtn.onclick = () => { modal.classList.remove('visible'); onConfirm(); };
                newCancelBtn.onclick = () => { modal.classList.remove('visible'); };

            } else {
                // Modo Alerta/Error/Simulación (Usa color primario Teal)
                newConfirmBtn.textContent = 'Cerrar';
                newConfirmBtn.classList.remove('delete');
                newConfirmBtn.classList.add('primary');
                newCancelBtn.style.display = 'none';

                // Si hay una función de confirmación, la ejecutamos después de cerrar, si no, solo cerramos.
                newConfirmBtn.onclick = () => {
                    modal.classList.remove('visible');
                    if (onConfirm) onConfirm();
                };
            }

            modal.classList.add('visible');
        }

        // Iniciar la aplicación al cargar la ventana
        window.onload = initApp;



