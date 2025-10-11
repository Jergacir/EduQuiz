document.addEventListener("DOMContentLoaded", () => {
    const usuarioId = document.body.dataset.usuarioId;
    // --- Referencias ---
    const titleInput = document.querySelector(".title-input");
    const btnGuardar = document.querySelector(".btn-primary");
    const questionListContainer = document.querySelector(".question-list-sidebar");
    const questionEditor = document.querySelector(".question-editor");
    const questionTextInput = document.querySelector(".question-text-input");
    const answerInputs = document.querySelectorAll(".answer-box input");
    const timeSelect = document.querySelectorAll(".option-select")[0];
    const pointsSelect = document.querySelectorAll(".option-select")[1];
    const btnAddQuestion = document.querySelector(".btn-add-question");

    const answersGrid = document.querySelector(".answers-grid");
    const btnAddAnswer = document.querySelector(".btn-add-answer")

    // --- Subir / Arrastrar imagen ---
    const mediaBox = document.querySelector(".media-upload-box");
    const mediaInput = document.getElementById("mediaInput");
    const btnUpload = mediaBox.querySelector(".btn-upload");
    const previewContainer = document.querySelector(".media-preview");
    const previewImage = document.getElementById("previewImage");
    const removeImage = document.getElementById("removeImage");

    // --- Modal de Temas ---
    const btnThemes = document.querySelector('.btn-action i.icon-themes').closest('a');
    const themesModal = document.getElementById('themesModal');
    const cancelThemes = document.getElementById('cancelThemes');
    const saveThemes = document.getElementById('saveThemes');
    const colorSchemeSelect = document.getElementById('colorScheme');
    const themePreview = document.getElementById('themePreview');


    // --- Estado ---
    let cuestionario = {
        titulo: "",
        preguntas: []
    };
    let preguntaActual = 0;

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

        questionListContainer.innerHTML = cardsHTML + `
            <button class="btn-add-question"><i class="icon-plus"></i> Añadir Pregunta</button>
        `;

        // Reasignar eventos
        asignarEventosCards();
    }

    function asignarEventosCards() {
        const cards = document.querySelectorAll(".question-card-preview");
        const btnsDuplicar = questionListContainer.querySelectorAll('[data-action="duplicar"]');
        const btnsEliminar = questionListContainer.querySelectorAll('[data-action="eliminar"]');
        const btnAdd = document.querySelector(".btn-add-question");

        cards.forEach(card => {
            card.addEventListener("click", (e) => {
                // Evitar que click en duplicar/eliminar cambie de pregunta
                if (e.target.dataset.action) return;
                guardarPreguntaActual();
                const index = parseInt(card.dataset.index);
                cargarPregunta(index);
            });
        });

        btnsDuplicar.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                duplicarPregunta(index);
            });
        });

        btnsEliminar.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                eliminarPregunta(index);
            });
        });

        if (btnAdd) {
            btnAdd.addEventListener("click", () => {
                guardarPreguntaActual();
                // Crear una nueva pregunta base
                cuestionario.preguntas.push(crearPreguntaBase());

                // Actualizar índice actual al final
                preguntaActual = cuestionario.preguntas.length - 1;

                // Volver a renderizar lista y cargar nueva pregunta
                renderPreguntas();
                cargarPregunta(preguntaActual);

                // Desplazar la barra lateral al final (opcional)
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
        renderRespuestas(); // 👈 nuevo método dinámico
        timeSelect.value = p.tiempo;
        pointsSelect.value = p.puntos;
        mostrarImagenGuardada(p.imagen);
    }

    function guardarPreguntaActual() {
        const p = cuestionario.preguntas[preguntaActual];
        p.texto = questionTextInput.value.trim();

        // 🔹 Recolectar las respuestas actuales del DOM dinámicamente
        const currentInputs = document.querySelectorAll(".answers-grid .answer-box input");
        p.respuestas = Array.from(currentInputs).map(inp => inp.value.trim());

        // 🔹 Guardar las opciones actuales
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
                renderRespuestas(); // se re-renderiza para reflejar el cambio
            });

            // Botón eliminar (solo si hay más de 4 respuestas)
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

                // Si eliminaste la correcta, reajusta índice correcta
                if (p.correcta === i) p.correcta = 0;
                else if (p.correcta > i) p.correcta--;

                renderRespuestas();
            });

            // Agregar elementos
            const controls = document.createElement("div");
            controls.classList.add("answer-controls");
            controls.appendChild(btnCorrecta);
            controls.appendChild(btnEliminar);

            answerBox.appendChild(input);
            answerBox.appendChild(controls);
            answersGrid.appendChild(answerBox);
        });

        // Control botón “Añadir respuesta”
        if (p.respuestas.length >= 6) {
            btnAddAnswer.disabled = true;
            btnAddAnswer.classList.add("disabled");
        } else {
            btnAddAnswer.disabled = false;
            btnAddAnswer.classList.remove("disabled");
        }
    }

    function agregarRespuesta() {
        const p = cuestionario.preguntas[preguntaActual];
        if (p.respuestas.length >= 6) {
            alert("Solo se pueden tener hasta 6 respuestas por pregunta.");
            return;
        }
        p.respuestas.push(""); // Añadir respuesta vacía
        renderRespuestas();
    }

    function duplicarPregunta(index) {
        const original = cuestionario.preguntas[index];
        const copia = JSON.parse(JSON.stringify(original));
        cuestionario.preguntas.splice(index + 1, 0, copia);
        cargarPregunta(index + 1);
        renderPreguntas();
        preguntaActual = index + 1;
        cargarPregunta(preguntaActual);
    }

    function eliminarPregunta(index) {
        if (cuestionario.preguntas.length === 1) {
            alert("Debe haber al menos una pregunta en el cuestionario.");
            return;
        }
        cuestionario.preguntas.splice(index, 1);
        preguntaActual = Math.min(preguntaActual, cuestionario.preguntas.length - 1);
        renderPreguntas();
        cargarPregunta(preguntaActual);
    }

    // --- Inicialización ---

    // Crear 3 preguntas vacías iniciales
    cuestionario.preguntas = [crearPreguntaBase(), crearPreguntaBase(), crearPreguntaBase()];

    // Validación título
    titleInput.value = "";
    btnGuardar.disabled = true;
    btnGuardar.classList.add("disabled");
    titleInput.addEventListener("input", () => {
        cuestionario.titulo = titleInput.value.trim();
        const valido = cuestionario.titulo.length > 0;
        btnGuardar.disabled = !valido;
        btnGuardar.classList.toggle("disabled", !valido);
    });

    // Escuchar cambios de inputs
    questionTextInput.addEventListener("input", guardarPreguntaActual);
    answerInputs.forEach(inp => inp.addEventListener("input", guardarPreguntaActual));
    timeSelect.addEventListener("change", guardarPreguntaActual);
    pointsSelect.addEventListener("change", guardarPreguntaActual);
    btnAddAnswer.addEventListener("click", agregarRespuesta);

    // Guardar cuestionario
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
            descripcion: "Cuestionario creado desde el editor", // puedes añadir un campo de descripción si lo agregas al front
            publico: detallesConfig.privacidad === "public" ? 1 : 0,
            modo_juego: detallesConfig.tema === "multiple" ? "M" : "C",
            tiempo_limite_pregunta: 30, // o podrías hacerlo configurable
            usuario_id: usuarioId,
            url_img_cuestionario: cuestionario.imagen || "https://url.com/imagen_por_defecto.jpg", // provisional, luego vendrá de Cloudinary
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

        console.log("📦 Datos a enviar:", cuestionarioData);

        try {
            const response = await fetch("/api/cuestionario_completo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cuestionarioData)
            });

            const data = await response.json();

            if (response.ok) {
                alert(`✅ Cuestionario "${cuestionarioData.nombre_cuestionario}" guardado correctamente.`);
                console.log("Respuesta del servidor:", data);
            } else {
                console.error("Error del servidor:", data);
                alert("❌ Error al guardar el cuestionario.");
            }
        } catch (err) {
            console.error("Error de conexión:", err);
            alert("⚠️ No se pudo conectar con el servidor.");
        }
        cambiosPendientes = false;
        window.location.href = "/cuestionario";
    });

    // Cargar primera pregunta
    renderPreguntas();
    cargarPregunta(0);


    // --- Confirmar salida ---
    const btnExit = document.querySelector(".btn-secondary"); // Tu botón "Salir"
    const exitModal = document.getElementById("exitModal");
    const cancelExit = document.getElementById("cancelExit");
    const confirmExit = document.getElementById("confirmExit");

    // Mostrar modal
    btnExit.addEventListener("click", (e) => {
        e.preventDefault();
        exitModal.classList.remove("hidden");
    });

    // Cancelar salida
    cancelExit.addEventListener("click", () => {
        exitModal.classList.add("hidden");
    });

    // Confirmar salida -> redirige a Flask
    confirmExit.addEventListener("click", () => {
        window.location.href = "/cuestionario";
    });

    // --- Advertencia al cerrar o recargar la página ---
    let cambiosPendientes = true; // Cambia a false si guardas el cuestionario

    window.addEventListener("beforeunload", function (e) {
        if (cambiosPendientes) {
            // Mensaje personalizado (solo algunos navegadores lo mostrarán)
            e.preventDefault();
            e.returnValue = "Tienes cambios sin guardar. ¿Seguro que deseas salir?";
        }
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

    // Cerrar sin guardar
    cancelDetails.addEventListener("click", () => {
        detailsModal.classList.add("hidden");
    });

    // Guardar cambios
    saveDetails.addEventListener("click", () => {
        const privacy = document.getElementById("privacy").value;
        const theme = document.getElementById("theme").value;

        detallesConfig.privacidad = privacy;
        detallesConfig.tema = theme;

        console.log("Configuración guardada:", detallesConfig);

        detailsModal.classList.add("hidden");
    });




    // Abrir selector de archivos al hacer clic en botón
    btnUpload.addEventListener("click", (e) => {
        e.stopPropagation();
        mediaInput.click();
    });

    // Manejar selección de archivo
    mediaInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) mostrarImagen(file);
    });

    // Permitir click directo en el cuadro para abrir file input
    mediaBox.addEventListener("click", () => {
        if (previewContainer.classList.contains("hidden")) {
            mediaInput.click();
        }
    });

    // --- Drag & Drop ---
    mediaBox.addEventListener("dragover", (e) => {
        e.preventDefault();
        mediaBox.classList.add("dragover");
    });

    mediaBox.addEventListener("dragleave", () => {
        mediaBox.classList.remove("dragover");
    });

    mediaBox.addEventListener("drop", (e) => {
        e.preventDefault();
        mediaBox.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file) mostrarImagen(file);
    });

    // --- Mostrar vista previa ---
    function mostrarImagen(file) {
        if (!file.type.startsWith("image/")) {
            alert("Solo se permiten imágenes.");
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewContainer.classList.remove("hidden");

            // Ocultar textos de arrastre
            mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.add("hidden"));

            // Guardar en el objeto de la pregunta actual
            cuestionario.preguntas[preguntaActual].imagen = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // --- Eliminar imagen ---
    removeImage.addEventListener("click", (e) => {
        e.stopPropagation();
        previewContainer.classList.add("hidden");
        previewImage.src = "";
        mediaInput.value = "";
        cuestionario.preguntas[preguntaActual].imagen = null;

        // Mostrar nuevamente el cuadro de arrastre
        mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.remove("hidden"));
    });

    function mostrarImagenGuardada(dataURL) {
        if (dataURL) {
            previewImage.src = dataURL;
            previewContainer.classList.remove("hidden");

            // Ocultar textos de arrastre
            mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.add("hidden"));
        } else {
            previewImage.src = "";
            previewContainer.classList.add("hidden");

            // Mostrar textos de arrastre
            mediaBox.querySelectorAll("i, p, .btn-upload").forEach(el => el.classList.remove("hidden"));
        }
    }



    // Abrir modal
    btnThemes.addEventListener('click', (e) => {
        e.preventDefault();
        themesModal.classList.remove('hidden');
    });

    // Cerrar modal
    cancelThemes.addEventListener('click', () => {
        themesModal.classList.add('hidden');
    });



    // --- Guardar tema ---
    saveThemes.addEventListener('click', () => {
        const selectedColor = colorSchemeSelect.value;

        const tema = { color: selectedColor };

        cuestionario.tema = tema;
        aplicarTema(tema);

        themesModal.classList.add('hidden');
    });

    // --- Aplicar tema visual ---
    function aplicarTema(tema) {
        const main = document.querySelector('.main-container');
        main.classList.remove('theme-light', 'theme-dark', 'theme-blue', 'theme-green', 'theme-pink');

        if (tema.color && tema.color !== 'default') {
            main.classList.add(`theme-${tema.color}`);
        }

        document.body.style.backgroundImage = ''; // aseguramos que no haya imagen previa
    }

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
