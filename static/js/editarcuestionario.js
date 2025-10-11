document.addEventListener("DOMContentLoaded", async () => {
    // --- Obtener IDs desde el HTML ---
    const usuarioId = document.body.dataset.usuarioId;
    const cuestionarioId = document.body.dataset.cuestionarioId;

    // --- Referencias del DOM ---
    const titleInput = document.querySelector(".title-input");
    const btnGuardar = document.querySelector(".btn-primary");
    const questionListContainer = document.querySelector(".question-list-sidebar");
    const questionTextInput = document.querySelector(".question-text-input");
    const answersGrid = document.querySelector(".answers-grid");
    const btnAddAnswer = document.querySelector(".btn-add-answer");
    const timeSelect = document.querySelectorAll(".option-select")[0];
    const pointsSelect = document.querySelectorAll(".option-select")[1];

    const mediaBox = document.querySelector(".media-upload-box");
    const mediaInput = document.getElementById("mediaInput");
    const previewContainer = document.querySelector(".media-preview");
    const previewImage = document.getElementById("previewImage");
    const removeImage = document.getElementById("removeImage");

    // --- Estado ---
    let cuestionario = { titulo: "", preguntas: [] };
    let preguntaActual = 0;
    let cambiosPendientes = true;

    // --- Funciones auxiliares ---
    function crearPreguntaBase() {
        return {
            texto: "",
            respuestas: ["", "", "", ""],
            correcta: 0,
            tiempo: "30s",
            puntos: "standard",
            imagen: null
        };
    }

    function renderPreguntas() {
        const cardsHTML = cuestionario.preguntas.map((p, i) => `
            <div class="question-card-preview ${i === preguntaActual ? "active" : ""}" data-index="${i}">
                <span class="q-number">${i + 1}. Pregunta ${String(i + 1).padStart(2, "0")}</span>
                <div class="q-actions">
                    <i class="icon-copy" title="Duplicar" data-action="duplicar" data-index="${i}">Duplicar</i>
                    <i class="icon-delete" title="Eliminar" data-action="eliminar" data-index="${i}">Eliminar</i>
                </div>
                <div class="q-image-placeholder"></div>
            </div>
        `).join("");
        questionListContainer.innerHTML = cardsHTML + `<button class="btn-add-question"><i class="icon-plus"></i> Añadir Pregunta</button>`;
        asignarEventosCards();
    }

    function asignarEventosCards() {
        const cards = document.querySelectorAll(".question-card-preview");
        const btnsDuplicar = questionListContainer.querySelectorAll('[data-action="duplicar"]');
        const btnsEliminar = questionListContainer.querySelectorAll('[data-action="eliminar"]');
        const btnAdd = document.querySelector(".btn-add-question");

        cards.forEach(card => {
            card.addEventListener("click", (e) => {
                if (e.target.dataset.action) return;
                guardarPreguntaActual();
                cargarPregunta(parseInt(card.dataset.index));
            });
        });

        btnsDuplicar.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                duplicarPregunta(parseInt(btn.dataset.index));
            });
        });

        btnsEliminar.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                eliminarPregunta(parseInt(btn.dataset.index));
            });
        });

        if (btnAdd) {
            btnAdd.addEventListener("click", () => {
                guardarPreguntaActual();
                cuestionario.preguntas.push(crearPreguntaBase());
                preguntaActual = cuestionario.preguntas.length - 1;
                renderPreguntas();
                cargarPregunta(preguntaActual);
                questionListContainer.scrollTop = questionListContainer.scrollHeight;
            });
        }
    }

    function cargarPregunta(index) {
        const p = cuestionario.preguntas[index];
        preguntaActual = index;

        document.querySelectorAll(".question-card-preview").forEach(c => c.classList.remove("active"));
        const activeCard = document.querySelector(`.question-card-preview[data-index="${index}"]`);
        if (activeCard) activeCard.classList.add("active");

        questionTextInput.value = p.texto;
        timeSelect.value = p.tiempo;
        pointsSelect.value = p.puntos;
        renderRespuestas();
        mostrarImagenGuardada(p.imagen);
    }

    function guardarPreguntaActual() {
        const p = cuestionario.preguntas[preguntaActual];
        p.texto = questionTextInput.value.trim();
        const currentInputs = document.querySelectorAll(".answers-grid .answer-box input");
        p.respuestas = Array.from(currentInputs).map(inp => inp.value.trim());
        p.tiempo = timeSelect.value;
        p.puntos = pointsSelect.value;
    }

    function renderRespuestas() {
        const p = cuestionario.preguntas[preguntaActual];
        answersGrid.innerHTML = "";

        p.respuestas.forEach((rpta, i) => {
            const answerBox = document.createElement("div");
            answerBox.classList.add("answer-box");
            if (i === p.correcta) answerBox.classList.add("correct");

            // Input de texto
            const input = document.createElement("input");
            input.type = "text";
            input.placeholder = "Escribe aquí la respuesta";
            input.value = rpta;

            input.addEventListener("input", () => {
                p.respuestas[i] = input.value.trim();
            });

            // Botón para marcar como correcta
            const btnCorrecta = document.createElement("button");
            btnCorrecta.classList.add("btn-correcta");
            btnCorrecta.textContent = "✓";
            btnCorrecta.title = "Marcar como correcta";

            btnCorrecta.addEventListener("click", () => {
                p.correcta = i;
                renderRespuestas(); // re-renderiza para reflejar cambio
            });

            // Botón eliminar respuesta
            const btnEliminar = document.createElement("button");
            btnEliminar.classList.add("btn-eliminar-rpta");
            btnEliminar.textContent = "🗑";
            btnEliminar.title = "Eliminar respuesta";

            btnEliminar.addEventListener("click", () => {
                if (p.respuestas.length <= 4) {
                    alert("Debe haber al menos 4 respuestas por pregunta.");
                    return;
                }
                p.respuestas.splice(i, 1);

                // Ajustar índice de la respuesta correcta
                if (p.correcta === i) p.correcta = 0;
                else if (p.correcta > i) p.correcta--;

                renderRespuestas();
            });

            // Contenedor de botones
            const controls = document.createElement("div");
            controls.classList.add("answer-controls");
            controls.appendChild(btnCorrecta);
            controls.appendChild(btnEliminar);

            answerBox.appendChild(input);
            answerBox.appendChild(controls);

            answersGrid.appendChild(answerBox);
        });

        // Control de botón “Añadir respuesta”
        if (p.respuestas.length >= 6) {
            btnAddAnswer.disabled = true;
            btnAddAnswer.classList.add("disabled");
        } else {
            btnAddAnswer.disabled = false;
            btnAddAnswer.classList.remove("disabled");
        }
    }

    function mostrarImagenGuardada(dataURL) {
        if (dataURL) {
            previewImage.src = dataURL;
            previewContainer.classList.remove("hidden");
            mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.add("hidden"));
        } else {
            previewImage.src = "";
            previewContainer.classList.add("hidden");
            mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.remove("hidden"));
        }
    }

    function duplicarPregunta(index) {
        const copia = JSON.parse(JSON.stringify(cuestionario.preguntas[index]));
        cuestionario.preguntas.splice(index + 1, 0, copia);
        preguntaActual = index + 1;
        renderPreguntas();
        cargarPregunta(preguntaActual);
    }

    function eliminarPregunta(index) {
        if (cuestionario.preguntas.length === 1) return;
        cuestionario.preguntas.splice(index, 1);
        preguntaActual = Math.min(preguntaActual, cuestionario.preguntas.length - 1);
        renderPreguntas();
        cargarPregunta(preguntaActual);
    }

    function agregarRespuesta() {
        const p = cuestionario.preguntas[preguntaActual];
        if (p.respuestas.length >= 6) return;
        p.respuestas.push("");
        renderRespuestas();
    }

    // --- Eventos ---
    btnAddAnswer.addEventListener("click", agregarRespuesta);
    questionTextInput.addEventListener("input", guardarPreguntaActual);
    timeSelect.addEventListener("change", guardarPreguntaActual);
    pointsSelect.addEventListener("change", guardarPreguntaActual);

    removeImage.addEventListener("click", () => {
        cuestionario.preguntas[preguntaActual].imagen = null;
        mostrarImagenGuardada(null);
        mediaInput.value = "";
    });

    mediaInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file || !file.type.startsWith("image/")) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            cuestionario.preguntas[preguntaActual].imagen = ev.target.result;
            mostrarImagenGuardada(ev.target.result);
        };
        reader.readAsDataURL(file);
    });

    mediaBox.addEventListener("click", () => mediaInput.click());

    // --- Cargar cuestionario desde backend ---
    try {
        const resp = await fetch(`/api/cuestionario_completo/${cuestionarioId}`);
        if (!resp.ok) throw new Error("Error al obtener cuestionario");
        const data = await resp.json();

        cuestionario.titulo = data.nombre_cuestionario || "";
        titleInput.value = cuestionario.titulo;

        cuestionario.preguntas = data.preguntas.map(p => ({
            texto: p.texto_pregunta,
            respuestas: p.respuestas.map(r => r.texto_respuesta),
            correcta: p.correcta,
            tiempo: (p.tiempo_limite || 30) + "s",
            puntos: p.puntos || "standard",
            imagen: p.media_url || null
        }));
        cuestionario.url_img_cuestionario = data.url_img_cuestionario || null;


        renderPreguntas();
        cargarPregunta(0);

    } catch (err) {
        console.error(err);
        alert("No se pudo cargar el cuestionario");
    }

    // --- Advertencia salida ---
    window.addEventListener("beforeunload", (e) => {
        if (cambiosPendientes) {
            e.preventDefault();
            e.returnValue = "";
        }
    });

    // --- Botón Guardar ---
    btnGuardar.addEventListener("click", async (e) => {
        e.preventDefault();
        guardarPreguntaActual();

        if (!cuestionario.titulo.trim()) {
            alert("Agrega un título al cuestionario primero.");
            return;
        }

        // --- Armar estructura final ---
        const cuestionarioData = {
            nombre_cuestionario: cuestionario.titulo,
            descripcion: "Cuestionario editado desde el editor",
            publico: detallesConfig.privacidad === "public" ? 1 : 0,
            modo_juego: detallesConfig.tema === "multiple" ? "M" : "C",
            tiempo_limite_pregunta: 30,
            usuario_id: usuarioId,
            url_img_cuestionario: cuestionario.imagen || null,
            preguntas: cuestionario.preguntas.map((p) => ({
                texto_pregunta: p.texto,
                media_url: p.imagen || null,
                tiempo_limite: parseInt(p.tiempo) || 30,
                respuestas: p.respuestas.map((r, i) => ({
                    texto_respuesta: r,
                    estado_respuesta: i === p.correcta ? 1 : 0
                }))
            }))
        };

        console.log("📦 Datos a enviar para actualizar:", cuestionarioData);

        try {
            const response = await fetch(`/api/cuestionario_completo/${cuestionarioId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cuestionarioData)
            });

            const data = await response.json();

            if (response.ok) {
                alert(`✅ Cuestionario "${cuestionarioData.nombre_cuestionario}" actualizado correctamente.`);
                console.log("Respuesta del servidor:", data);
            } else {
                console.error("Error del servidor:", data);
                alert("❌ Error al actualizar el cuestionario.");
            }
        } catch (err) {
            console.error("Error de conexión:", err);
            alert("⚠️ No se pudo conectar con el servidor.");
        }

        cambiosPendientes = false;
        window.location.href = "/cuestionario";
    });


    // --- Modal de Detalles ---
    const btnDetalles = document.querySelector('.btn-action .icon-details, .btn-action i.icon-details, .btn-action:nth-child(2)');
    const detailsModal = document.getElementById('detailsModal');
    const cancelDetails = document.getElementById('cancelDetails');
    const saveDetails = document.getElementById('saveDetails');

    let detallesConfig = {
        privacidad: "public",
        tema: "default"
    };

    // Abrir modal de detalles
    document.querySelectorAll(".btn-action").forEach(btn => {
        if (btn.querySelector(".icon-details")) {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                detailsModal.classList.remove("hidden");
            });
        }
    });

    // Cerrar modal sin guardar
    cancelDetails.addEventListener("click", () => {
        detailsModal.classList.add("hidden");
    });

    // Guardar cambios de detalles
    saveDetails.addEventListener("click", () => {
        const privacy = document.getElementById("privacy").value;
        const theme = document.getElementById("theme").value;

        detallesConfig.privacidad = privacy;
        detallesConfig.tema = theme;

        console.log("Configuración guardada:", detallesConfig);

        detailsModal.classList.add("hidden");
    });


    // --- Modal de Temas ---
    const btnThemes = document.querySelector('.btn-action i.icon-themes').closest('a');
    const themesModal = document.getElementById('themesModal');
    const cancelThemes = document.getElementById('cancelThemes');
    const saveThemes = document.getElementById('saveThemes');
    const colorSchemeSelect = document.getElementById('colorScheme');

    btnThemes.addEventListener('click', (e) => {
        e.preventDefault();
        themesModal.classList.remove('hidden');
    });

    // Cerrar modal de temas
    cancelThemes.addEventListener('click', () => {
        themesModal.classList.add('hidden');
    });

    // Guardar tema seleccionado y aplicar visualmente
    saveThemes.addEventListener('click', () => {
        const selectedColor = colorSchemeSelect.value;

        const tema = { color: selectedColor };
        cuestionario.tema = tema;
        aplicarTema(tema);

        themesModal.classList.add('hidden');
    });

    // Función para aplicar tema visual
    function aplicarTema(tema) {
        const main = document.querySelector('.main-container');
        main.classList.remove('theme-light', 'theme-dark', 'theme-blue', 'theme-green', 'theme-pink');

        if (tema.color && tema.color !== 'default') {
            main.classList.add(`theme-${tema.color}`);
        }

        document.body.style.backgroundImage = ''; // limpiar cualquier fondo previo
    }

    // --- Botón Salir y modal de confirmación ---
    const btnExit = document.querySelector(".btn-secondary"); // tu botón "Salir"
    const exitModal = document.getElementById("exitModal");
    const cancelExit = document.getElementById("cancelExit");
    const confirmExit = document.getElementById("confirmExit");

    // Mostrar modal al hacer clic en salir
    btnExit.addEventListener("click", (e) => {
        e.preventDefault();
        exitModal.classList.remove("hidden");
    });

    // Cerrar modal sin salir
    cancelExit.addEventListener("click", () => {
        exitModal.classList.add("hidden");
    });

    // Confirmar salida -> redirige a lista de cuestionarios
    confirmExit.addEventListener("click", () => {
        window.location.href = "/cuestionario";
    });

    // Advertencia al cerrar o recargar la página si hay cambios sin guardar
    // cambia a false cuando guardes el cuestionario
    window.addEventListener("beforeunload", (e) => {
        if (cambiosPendientes) {
            e.preventDefault();
            e.returnValue = "Tienes cambios sin guardar. ¿Seguro que deseas salir?";
        }
    });

    // --- Modal Editar Imagen del Cuestionario ---
    const btnEditarCuestionario = document.querySelector('.btn-action.active'); // tu botón "Editar"
    const editImageModal = document.getElementById('editImageModal');
    const cancelEditImage = document.getElementById('cancelEditImage');
    const saveEditImage = document.getElementById('saveEditImage');

    const mediaBoxModal = editImageModal.querySelector('.media-upload-box-modal');
    const imageInputModal = document.getElementById('imageInputModal');
    const btnUploadModal = document.getElementById('btnUploadModal');
    const previewContainerModal = document.getElementById('previewContainerModal');
    const previewImageModal = document.getElementById('previewImageModal');
    const removeImageModal = document.getElementById('removeImageModal');

    let imagenCuestionario = null; // guardará DataURL temporal

    // Abrir modal
    btnEditarCuestionario.addEventListener('click', (e) => {
        e.preventDefault();
        editImageModal.classList.remove('hidden');

        // Solo establecer la imagen inicial si aún no hay cambios temporales
        if (imagenCuestionario === null && cuestionario.url_img_cuestionario) {
            previewImageModal.src = cuestionario.url_img_cuestionario;
            previewContainerModal.classList.remove('hidden');
            mediaBoxModal.querySelectorAll('i, p, .btn-upload').forEach(el => el.classList.add('hidden'));
            imagenCuestionario = cuestionario.url_img_cuestionario;
        }
    });

    // Cerrar modal sin guardar
    cancelEditImage.addEventListener('click', () => {
        editImageModal.classList.add('hidden');
    });

    // Botón subir
    btnUploadModal.addEventListener('click', () => {
        imageInputModal.click();
    });

    // Selección de archivo
    imageInputModal.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) mostrarImagenCuestionario(file);
    });

    // Drag & drop
    mediaBoxModal.addEventListener('dragover', (e) => { e.preventDefault(); mediaBoxModal.classList.add('dragover'); });
    mediaBoxModal.addEventListener('dragleave', () => mediaBoxModal.classList.remove('dragover'));
    mediaBoxModal.addEventListener('drop', (e) => {
        e.preventDefault();
        mediaBoxModal.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) mostrarImagenCuestionario(file);
    });

    // Función vista previa
    function mostrarImagenCuestionario(file) {
        if (!file.type.startsWith('image/')) { alert("Solo se permiten imágenes."); return; }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImageModal.src = e.target.result;
            previewContainerModal.classList.remove('hidden');

            // Ocultar textos de arrastre
            mediaBoxModal.querySelectorAll('i, p, .btn-upload').forEach(el => el.classList.add('hidden'));

            imagenCuestionario = e.target.result; // guardamos la imagen temporal
        };
        reader.readAsDataURL(file);
    }

    // Eliminar imagen
    removeImageModal.addEventListener('click', () => {
        previewContainerModal.classList.add('hidden');
        previewImageModal.src = '';
        imageInputModal.value = '';
        imagenCuestionario = null;

        mediaBoxModal.querySelectorAll('i, p, .btn-upload').forEach(el => el.classList.remove('hidden'));
    });

    // Guardar imagen del cuestionario
    saveEditImage.addEventListener('click', () => {
        if (imagenCuestionario) {
            // Guardar temporal en el objeto principal
            cuestionario.imagen = imagenCuestionario;
            console.log("Imagen del cuestionario guardada:", imagenCuestionario);
        }
        editImageModal.classList.add('hidden');
    });
});
