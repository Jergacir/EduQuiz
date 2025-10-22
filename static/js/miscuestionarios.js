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
            <div class="quiz-badge">${cuestionario.num_preguntas || 0
      } preguntas</div>
                    <div class="quiz-image-placeholder">
                    ${cuestionario.url_img_cuestionario ? `
                      <img src="${cuestionario.url_img_cuestionario}" alt="Imagen del cuestionario">
                    ` : `
                      <i class="fas fa-image"></i>
                    `}
                    </div>
                    <div class="quiz-content">
                        <h3 title="${cuestionario.nombre_cuestionario}">${cuestionario.nombre_cuestionario || "Cuestionario sin Título"
      }</h3>
                        <p>${cuestionario.descripcion || "Sin descripción"}</p>
                         ${cuestionario.codigo_visualizacion
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
                                <a href="/editar_cuestionario/${cuestionario.cuestionario_id
      }" class="edit-btn"><i class="fas fa-edit" style="margin-right:4px"></i> Editar</a>
                            </div>
                            <div class="action-icons">
                                <button title="Jugar" class="action-icon-btn play btn-jugar"><i class="fa-solid fa-gamepad"></i></button>
                                <button data-id="${cuestionario.cuestionario_id
      }" title="Clonar" class="action-icon-btn clone clone-quiz-btn"><i class="fas fa-copy"></i></button>
                                <button title="Eliminar" class="action-icon-btn delete"><i class="fa-solid fa-trash icon-delete"></i></button>
                                
                            </div>
                        </div>
                    </div>
        `;
    // 1. Obtener el ícono de Jugar
    const playIcon = card.querySelector(".btn-jugar");

    if (playIcon) {
      // 2. Adjuntar el evento para abrir el modal de configuración
      playIcon.addEventListener("click", () => {
        // Pasamos el objeto cuestionario completo para cargar la info en el modal
        abrirModalConfiguracion(cuestionario);
      });
    }
    return card;
  }

  function crearCardAlumno(cuestionario) {
    const card = document.createElement("div");
    card.classList.add("quiz-card", "student");

    card.innerHTML = `
        <div class="quiz-badge">${cuestionario.num_preguntas || 0
      } preguntas</div>
                    <div class="quiz-image-placeholder">
                    ${cuestionario.url_img_cuestionario ? `
                      <img src="${cuestionario.url_img_cuestionario}" alt="Imagen del cuestionario">
                    ` : `
                      <i class="fas fa-image"></i>
                    `}
                    </div>
                    <div class="quiz-content">
                        <h3 title="${cuestionario.nombre_cuestionario}">${cuestionario.nombre_cuestionario || "Cuestionario sin Título"
      }</h3>
                        <p>${cuestionario.descripcion || "Sin descripción"}</p>
                        <div class="quiz-actions">
                            <button class="btn-visualize" style="width: 100%; display: flex; background-color: var(--color-primary-teal); padding: 5px; border-radius: 12px; justify-content: center; align-items: center;border:none;" data-id="${cuestionario.cuestionario_id
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

  // --- Almacenamiento y render dinámico con filtrado en tiempo real ---
  let allCuestionarios = [];

  function renderAll(filter = "") {
    const q = (filter || "").toLowerCase().trim();

    if (tipoUsuario === "P") {
      const privados = allCuestionarios.filter(
        (c) => !(c.publico) && (c.nombre_cuestionario || "").toLowerCase().includes(q)
      );
      const publicos = allCuestionarios.filter(
        (c) => c.publico && (c.nombre_cuestionario || "").toLowerCase().includes(q)
      );

      privadosContainer.innerHTML = "";
      publicosContainer.innerHTML = "";

      privados.forEach((c) => {
        const card = crearCardProfesor(c);
        privadosContainer.appendChild(card);
        const deleteIcon = card.querySelector(".icon-delete");
        if (deleteIcon) deleteIcon.addEventListener("click", () => abrirModalConfirmacion(c.cuestionario_id, card));
        const cloneBtn = card.querySelector('.clone-quiz-btn');
        if (cloneBtn) {
          cloneBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = cloneBtn.dataset.id;
            try {
              const resp = await fetch(`/api/cuestionarios/clone/${id}`, { method: 'POST' });
              const data = await resp.json();
              if (resp.ok && data && data.status === 'ok') {
                // refrescar lista
                allCuestionarios = await fetchCuestionariosProfesor();
                renderAll(quizSearchInput.value || '');
              } else {
                alert('No se pudo clonar el cuestionario: ' + (data.error || data.message || JSON.stringify(data)));
              }
            } catch (err) {
              console.error('Error clonando cuestionario:', err);
              alert('Error de red al clonar.');
            }
          });
        }
      });

      publicos.forEach((c) => {
        const card = crearCardProfesor(c);
        publicosContainer.appendChild(card);
        const deleteIcon = card.querySelector(".icon-delete");
        if (deleteIcon) deleteIcon.addEventListener("click", () => abrirModalConfirmacion(c.cuestionario_id, card));
        const cloneBtn = card.querySelector('.clone-quiz-btn');
        if (cloneBtn) {
          cloneBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = cloneBtn.dataset.id;
            try {
              const resp = await fetch(`/api/cuestionarios/clone/${id}`, { method: 'POST' });
              const data = await resp.json();
              if (resp.ok && data && data.status === 'ok') {
                // refrescar lista
                allCuestionarios = await fetchCuestionariosProfesor();
                renderAll(quizSearchInput.value || '');
              } else {
                alert('No se pudo clonar el cuestionario: ' + (data.error || data.message || JSON.stringify(data)));
              }
            } catch (err) {
              console.error('Error clonando cuestionario:', err);
              alert('Error de red al clonar.');
            }
          });
        }
      });

      // Mostrar mensaje cuando no hay resultados
      const totalRenderedP = privados.length + publicos.length;
      const noQuizzesEl = document.getElementById('no-quizzes');
      if (noQuizzesEl) {
        if (totalRenderedP === 0) {
          noQuizzesEl.style.display = 'block';
        } else {
          noQuizzesEl.style.display = 'none';
        }
      }

    } else if (tipoUsuario === "A") {
      const filtered = allCuestionarios.filter((c) => (c.nombre_cuestionario || "").toLowerCase().includes(q));
      comunidadContainer.innerHTML = "";
      filtered.forEach((c) => {
        const card = crearCardAlumno(c);
        comunidadContainer.appendChild(card);
      });
      // Mostrar mensaje cuando no hay resultados
      const noQuizzesEl2 = document.getElementById('no-quizzes');
      if (noQuizzesEl2) {
        if (filtered.length === 0) {
          noQuizzesEl2.style.display = 'block';
        } else {
          noQuizzesEl2.style.display = 'none';
        }
      }
    }
  }

  // Inicializar datos y render inicial
  if (tipoUsuario === "P") {
    allCuestionarios = await fetchCuestionariosProfesor();
  } else {
    allCuestionarios = await fetchCuestionariosAlumnos();
  }

  renderAll("");

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
  // debounce simple
  function debounce(func, wait = 200) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => func(...args), wait);
    };
  }

  const handleSearch = debounce((e) => {
    renderAll(e.target.value || "");
  }, 150);

  quizSearchInput.addEventListener("input", handleSearch);





  // ******************************************************
  // --- LÓGICA DEL MODAL DE CONFIGURACIÓN DE PARTIDA ---
  // ******************************************************

  const configModal = document.getElementById("configuracionPartidaModal");
  const closeConfigBtn = document.getElementById("closeConfigModal");
  const iniciarPartidaBtn = document.getElementById("iniciarPartidaBtn");

  // Elementos dinámicos del modal
  const configQuizImage = document.getElementById("configQuizImage");
  const configNumPreguntas = document.getElementById("configNumPreguntas");
  const configQuizTitle = document.getElementById("configQuizTitle");
  const configQuizDescription = document.getElementById("configQuizDescription");
  let cuestionarioAConfigurar = null;

  // Función para abrir y cargar datos del modal
  // --- Nueva versión de abrirModalConfiguracion ---
  async function abrirModalConfiguracion(cuestionario) {
    try {
      // Obtener el cuestionario completo desde tu endpoint Flask
      const res = await fetch(`/api/cuestionario_completo/${cuestionario.cuestionario_id}`);
      const data = await res.json();

      if (!res.ok || data.error) {
        console.error("Error al obtener cuestionario completo:", data.error);
        alert("No se pudo cargar el cuestionario completo.");
        return;
      }

      // Guardar el cuestionario completo para usarlo al iniciar la partida
      cuestionarioAConfigurar = data;

      // Cargar la información básica en el modal
      configQuizImage.src = data.url_img_cuestionario || '/static/img/default_quiz.png';
      configNumPreguntas.textContent = `${data.preguntas?.length || 0} preguntas`;
      configQuizTitle.textContent = data.nombre_cuestionario;
      configQuizDescription.textContent = data.descripcion || 'Sin descripción.';

      // Mostrar PIN automático si aplica
      const pinDisplay = document.querySelector('.pin-display');
      const pinAutomatico = document.getElementById('checkPinAutomatico').checked;
      pinDisplay.style.display = pinAutomatico ? 'flex' : 'none';
      if (document.getElementById('checkPinAutomatico').checked) {
        const nuevoPin = generarPin();
        mostrarPin(nuevoPin);
        pinDisplay.style.display = 'flex';
      }
      // Mostrar modal
      configModal.classList.remove("hidden");

    } catch (err) {
      console.error("Error en abrirModalConfiguracion:", err);
      alert("Error al conectar con el servidor.");
    }
  }

  // Cerrar modal
  closeConfigBtn.addEventListener("click", () => {
    configModal.classList.add("hidden");
    cuestionarioAConfigurar = null;
  });

  // Lógica para iniciar la partida (Enviar configuración al backend)
  iniciarPartidaBtn.addEventListener("click", async () => {
    if (!cuestionarioAConfigurar) return;
    const modalidadSelect = document.getElementById("modalidadSelect").value;
    let tipo_partida = modalidadSelect === "grupal" ? "G" : "I";
    // 1. Recoger las opciones de configuración
    const configuracion = {
      cuestionario_id: cuestionarioAConfigurar.cuestionario_id,
      orden_preguntas_azar: document.getElementById("checkPreguntasAzar").checked,
      orden_respuestas_azar: document.getElementById("checkRespuestasAzar").checked,
      anadir_musica: document.getElementById("checkAnadirMusica").checked,
      modalidad: tipo_partida,
      num_grupos: document.getElementById("numGrupos").value,
      generar_qr: document.getElementById("checkGenerarQR").checked,
      pin_automatico: document.getElementById("checkPinAutomatico").checked,
      pin: Array.from(document.querySelectorAll('.pin-box'))
        .map(b => b.textContent)
        .join('')
    };

    console.log("Configuración a enviar:", configuracion);

    // === ALEATORIZACIÓN LOCAL ===
    console.log("🔹 Cuestionario ORIGINAL:", cuestionarioAConfigurar);

    let cuestionarioFinal = JSON.parse(JSON.stringify(cuestionarioAConfigurar));

    // Si está activado el orden de preguntas al azar
    if (configuracion.orden_preguntas_azar && Array.isArray(cuestionarioFinal.preguntas)) {
      cuestionarioFinal.preguntas = cuestionarioFinal.preguntas.sort(() => Math.random() - 0.5);
      console.log("🔀 Preguntas ALEATORIZADAS:", cuestionarioFinal.preguntas.map(p => p.titulo || p.texto || p.id));
    } else {
      console.log("⚠️ Orden de preguntas al azar DESACTIVADO");
    }

    // Si está activado el orden de respuestas al azar
    if (configuracion.orden_respuestas_azar && Array.isArray(cuestionarioFinal.preguntas)) {
      cuestionarioFinal.preguntas.forEach((p, i) => {
        if (Array.isArray(p.respuestas)) {
          const antes = p.respuestas.map(r => r.texto || r.id);
          p.respuestas = p.respuestas.sort(() => Math.random() - 0.5);
          const despues = p.respuestas.map(r => r.texto || r.id);
          console.log(`🎲 Respuestas pregunta ${i + 1}:`);
          console.log("Antes:", antes);
          console.log("Después:", despues);
        }
      });
    } else {
      console.log("⚠️ Orden de respuestas al azar DESACTIVADO");
    }

    // Guardar para la partida
    sessionStorage.setItem("cuestionario_actual", JSON.stringify(cuestionarioFinal));
    console.log("✅ Cuestionario aleatorizado guardado en sessionStorage:", cuestionarioFinal);

    try {
      // Ejemplo de endpoint, DEBES AJUSTARLO a tu lógica de creación de partida
      const res = await fetch(`/api/partidas/crear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configuracion)
      });

      const data = await res.json();

      if (data.status === "ok") {
        alert(`Partida creada con PIN: ${data.codigo_partida}`);

        // 🕒 Pequeña pausa para asegurar que localStorage se guarde bien
        setTimeout(() => {
          window.location.href = `/previapartida/${data.codigo_partida}`;
        }, 300);
      } else {
        alert("Error al crear la partida: " + (data.mensaje || "desconocido"));
      }

    } catch (error) {
      console.error("Error al iniciar la partida:", error);
      alert("Ocurrió un error en la conexión al crear la partida.");
    }

    // Cierra el modal después de intentar crear la partida
    configModal.classList.add("hidden");
  });

  // --- Lógica del PIN Automático ---
  const pinCheckbox = document.getElementById('checkPinAutomatico');
  const pinDisplay = document.querySelector('.pin-display');

  // Función para generar un PIN de 6 dígitos numéricos
  function generarPin() {
    let pin = "";
    for (let i = 0; i < 6; i++) {
      pin += Math.floor(Math.random() * 10); // genera un número entre 0-9
    }
    return pin;
  }

  // Función para mostrar un PIN en los .pin-box
  function mostrarPin(pin) {
    const pinBoxes = pinDisplay.querySelectorAll('.pin-box');
    pinBoxes.forEach((box, idx) => {
      box.textContent = pin[idx] || "";
    });
  }

  // --- Evento al cambiar el checkbox ---
  pinCheckbox.addEventListener('change', (e) => {
    if (e.target.checked) {
      // Si se activa, generar nuevo PIN
      const nuevoPin = generarPin();
      mostrarPin(nuevoPin);
      pinDisplay.style.display = 'flex';
    } else {
      // Si se desactiva, ocultar o limpiar
      pinDisplay.style.display = 'none';
      const pinBoxes = pinDisplay.querySelectorAll('.pin-box');
      pinBoxes.forEach(box => box.textContent = '');
    }
  });

  // --- Generar PIN inicial si está marcado por defecto ---
  if (pinCheckbox.checked) {
    mostrarPin(generarPin());
  }



  // --- Lógica del combo "Modalidad" ---
  const modalidadSelect = document.getElementById("modalidadSelect");
  const groupGrupal = document.querySelector(".group-grupal");

  // Mostrar/ocultar campo de número de grupos según modalidad
  modalidadSelect.addEventListener("change", (e) => {
    const valor = e.target.value;
    if (valor === "grupal") {
      groupGrupal.style.display = "block";
    } else {
      groupGrupal.style.display = "none";
    }
  });

  // -----------------------------------------------------
  // Lógica de música aleatoria 
  // -----------------------------------------------------
  const canciones = [
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1760924674/Los_Enanitos_Verdes_-_Tu_C%C3%A1rcel_Lyrics_ej9cyc.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1760925062/Bad_Bunny_-_Neverita_Video_Oficial_Un_Verano_Sin_Ti_oxyfy0.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1760925147/Soda_Stereo_-_De_M%C3%BAsica_Ligera_Official_Video_m1i83y.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761012145/The_Weeknd_-_Blinding_Lights_Lyrics_pnjckk.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761012198/The_Weeknd_-_Save_Your_Tears_Lyrics_sk53sy.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761012702/Imagine_Dragons_-_Believer_Lyrics_thbtuf.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013156/Tainy_Bad_Bunny_Julieta_Venegas_-_Lo_Siento_BB__tjdnjn.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013326/Harry_Styles_-_As_It_Was_Lyrics_ne5cp3.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013433/Charlie_Puth_-_Attention_Lyrics_tiluiq.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013506/Into_You_-_Ariana_Grande_Lyrics_d0jbb8.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013609/Bruno_Mars_Treasure_Letra_en_Espa%C3%B1ol_anocyz.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013695/Dua_Lipa_-_Don_t_Start_Now_Lyrics_z3ftld.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013759/Man%C3%A1_-_Oye_Mi_Amor_svzblo.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013897/Labios_Rotos_-_Zo%C3%A9_Letra._uy4h9m.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761013953/Morat_-_C%C3%B3mo_Te_Atreves_in9iej.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761014034/Avicii_-_Wake_Me_Up_Official_Lyric_Video_sumjir.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761014555/Danny_Ocean_-_Me_Reh%C3%BAso_yxhoob.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761014604/Besos_En_Guerra_-_Morat_Juanes_Lyrics_Video_wpnbbv.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761014813/Coldplay_-_Viva_la_Vida_Lyrics_gcinot.mp3",
    "https://res.cloudinary.com/ddsql5bqk/video/upload/v1761014903/Pokemon_Center_lofi_with_TanoshiSan_fp81ox.mp3"
  ];

  function reproducirMusicaAleatoria() {
    const randomIndex = Math.floor(Math.random() * canciones.length);
    const url = canciones[randomIndex];
    const musica = new Audio(url);
    musica.loop = true;
    musica.volume = 0.4;
    musica.play();

    console.log("🎧 Reproduciendo:", url);

    // ✅ Guardar en localStorage
    localStorage.setItem("musicaActiva", "true");
    localStorage.setItem("cancionActual", url);

    return musica;
  }

  let musicaActual = null;
  const checkAnadirMusica = document.getElementById("checkAnadirMusica");

  checkAnadirMusica.addEventListener("change", () => {
    if (checkAnadirMusica.checked) {
      musicaActual = reproducirMusicaAleatoria();
    } else {
      if (musicaActual) {
        musicaActual.pause();
        musicaActual = null;
      }
      localStorage.setItem("musicaActiva", "false");
    }
  });



});
