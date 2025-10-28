document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ partidas_profesor.js cargado');

    // DIAGNÓSTICO: Verificar que todos los elementos existan
    console.log('🔍 DIAGNÓSTICO DE ELEMENTOS:');
    console.log('Modal seleccionar:', document.getElementById('seleccionarCuestionarioModal'));
    console.log('Grid cuestionarios:', document.getElementById('cuestionarios-grid-modal'));
    console.log('Modal config:', document.getElementById('configuracionPartidaModal'));
    console.log('Botón crear:', document.getElementById('create-partida-button'));

    const usuarioId = document.body.dataset.usuarioId;
    const btnCrearPartida = document.getElementById('create-partida-button');

    if (!btnCrearPartida) {
        console.error('❌ ERROR: No se encontró el botón #create-partida-button');
        return;
    }

    let cuestionariosData = [];
    let cuestionarioSeleccionado = null;

    // ====================================================================
    // ABRIR MODAL DE SELECCIÓN
    // ====================================================================
    btnCrearPartida.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log('🎯 Botón Crear Partida clickeado');
        
        // Buscar modal JUSTO cuando se hace clic
        const modalSeleccionar = document.getElementById('seleccionarCuestionarioModal');
        const cuestionariosGrid = document.getElementById('cuestionarios-grid-modal');
        
        console.log('🔍 Buscando modal...', modalSeleccionar);
        console.log('🔍 Buscando grid...', cuestionariosGrid);

        if (!modalSeleccionar) {
            console.error('❌ El elemento #seleccionarCuestionarioModal NO EXISTE en el DOM');
            console.log('📋 Elementos con clase modal:', document.querySelectorAll('.modal'));
            console.log('📋 Todos los IDs en el body:', Array.from(document.querySelectorAll('[id]')).map(el => el.id));
            alert('Error: No se encuentra el modal. Verifica que partidas_profesor.html tenga el modal con id="seleccionarCuestionarioModal"');
            return;
        }

        if (!cuestionariosGrid) {
            console.error('❌ El elemento #cuestionarios-grid-modal NO EXISTE en el DOM');
            return;
        }

        console.log('✅ Modal encontrado, abriendo...');
        await abrirModalSeleccion(modalSeleccionar, cuestionariosGrid);
    });

    // ====================================================================
    // FUNCIÓN PARA ABRIR MODAL
    // ====================================================================
    async function abrirModalSeleccion(modalSeleccionar, cuestionariosGrid) {
        console.log('📂 Abriendo modal de selección...');
        
        const searchInput = document.getElementById('search-cuestionario-modal');
        const closeSeleccionarBtn = document.getElementById('closeSeleccionarModal');

        // Mostrar modal
        modalSeleccionar.classList.remove('hidden');
        console.log('✅ Clase hidden removida');
        
        // Asignar evento de cierre
        if (closeSeleccionarBtn) {
            closeSeleccionarBtn.onclick = () => {
                modalSeleccionar.classList.add('hidden');
            };
        }

        // Asignar evento de búsqueda
        if (searchInput) {
            searchInput.oninput = (e) => {
                const query = e.target.value.toLowerCase().trim();
                const filtrados = cuestionariosData.filter(q => 
                    q.nombre_cuestionario.toLowerCase().includes(query) ||
                    (q.descripcion && q.descripcion.toLowerCase().includes(query))
                );
                renderizarCuestionarios(filtrados, cuestionariosGrid);
            };
        }

        await cargarCuestionarios(cuestionariosGrid);
    }

    // ====================================================================
    // CARGAR CUESTIONARIOS DEL PROFESOR
    // ====================================================================
    async function cargarCuestionarios(cuestionariosGrid) {
        cuestionariosGrid.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-circle-notch fa-spin"></i>
                <p>Cargando cuestionarios...</p>
            </div>
        `;

        try {
            console.log(`📡 Cargando cuestionarios del usuario ${usuarioId}...`);
            const response = await fetch(`/api/cuestionarios/${usuarioId}`);
            if (!response.ok) throw new Error('Error al cargar cuestionarios');
            
            cuestionariosData = await response.json();
            console.log(`✅ Cuestionarios cargados: ${cuestionariosData.length}`, cuestionariosData);
            renderizarCuestionarios(cuestionariosData, cuestionariosGrid);
        } catch (error) {
            console.error('❌ Error:', error);
            cuestionariosGrid.innerHTML = `
                <div class="no-results-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error al cargar los cuestionarios</p>
                </div>
            `;
        }
    }

    // ====================================================================
    // RENDERIZAR CUESTIONARIOS
    // ====================================================================
    function renderizarCuestionarios(cuestionarios, cuestionariosGrid) {
        if (cuestionarios.length === 0) {
            cuestionariosGrid.innerHTML = `
                <div class="no-results-message">
                    <i class="fas fa-inbox"></i>
                    <p>No tienes cuestionarios creados</p>
                </div>
            `;
            return;
        }

        cuestionariosGrid.innerHTML = cuestionarios.map(quiz => `
            <div class="quiz-card-modal" data-quiz-id="${quiz.cuestionario_id}">
                <span class="quiz-badge-modal">${quiz.num_preguntas || 0} preguntas</span>
                <div class="quiz-image-modal">
                    ${quiz.url_img_cuestionario 
                        ? `<img src="${quiz.url_img_cuestionario}" alt="${quiz.nombre_cuestionario}">`
                        : '<i class="fas fa-image"></i>'
                    }
                </div>
                <h3 class="quiz-title-modal">${quiz.nombre_cuestionario}</h3>
                <p class="quiz-description-modal">${quiz.descripcion || 'Sin descripción'}</p>
                <button class="btn-crear-partida-card">
                    <i class="fas fa-play"></i> Crear Partida
                </button>
            </div>
        `).join('');

        asignarEventosCards(cuestionariosGrid);
    }

    // ====================================================================
    // ASIGNAR EVENTOS A LAS TARJETAS
    // ====================================================================
    function asignarEventosCards(cuestionariosGrid) {
        const cards = cuestionariosGrid.querySelectorAll('.quiz-card-modal');
        
        cards.forEach(card => {
            const btn = card.querySelector('.btn-crear-partida-card');
            const quizId = parseInt(card.dataset.quizId);
            
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                console.log(`🎮 Creando partida con cuestionario ID: ${quizId}`);
                await crearPartidaConCuestionario(quizId);
            });
        });
    }

    // ====================================================================
    // CREAR PARTIDA CON CUESTIONARIO SELECCIONADO
    // ====================================================================
    async function crearPartidaConCuestionario(quizId) {
        try {
            console.log(`📡 Cargando cuestionario completo con ID: ${quizId}`);
            const response = await fetch(`/api/cuestionario_completo/${quizId}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Error del servidor:', errorText);
                throw new Error('Error al cargar cuestionario completo');
            }
            
            cuestionarioSeleccionado = await response.json();
            console.log('✅ Cuestionario completo cargado:', cuestionarioSeleccionado);
            
            // Cerrar modal de selección
            const modalSeleccionar = document.getElementById('seleccionarCuestionarioModal');
            if (modalSeleccionar) {
                modalSeleccionar.classList.add('hidden');
            }
            
            // Abrir modal de configuración
            await abrirModalConfiguracion(cuestionarioSeleccionado);
            
        } catch (error) {
            console.error('❌ Error:', error);
            alert('Error al cargar el cuestionario. Intenta nuevamente.');
        }
    }

    // ====================================================================
    // ABRIR MODAL DE CONFIGURACIÓN
    // ====================================================================
    async function abrirModalConfiguracion(cuestionario) {
        console.log('⚙️ Abriendo modal de configuración...');
        
        const modalConfig = document.getElementById('configuracionPartidaModal');
        const closeConfigBtn = document.getElementById('closeConfigModal');
        const iniciarPartidaBtn = document.getElementById('iniciarPartidaBtn');

        if (!modalConfig) {
            console.error('❌ ERROR: El modal de configuración no está definido en el HTML');
            alert('Error: No se pudo abrir el modal de configuración');
            return;
        }

        cuestionarioSeleccionado = cuestionario;
        
        // Actualizar información del cuestionario en el modal
        const configQuizImage = document.getElementById('configQuizImage');
        const configNumPreguntas = document.getElementById('configNumPreguntas');
        const configQuizTitle = document.getElementById('configQuizTitle');
        const configQuizDescription = document.getElementById('configQuizDescription');

        if (configQuizImage) {
            configQuizImage.src = cuestionario.url_img_cuestionario || '/static/img/default.png';
        }
        if (configNumPreguntas) {
            configNumPreguntas.textContent = `${cuestionario.preguntas?.length || 0} preguntas`;
        }
        if (configQuizTitle) {
            configQuizTitle.textContent = cuestionario.nombre_cuestionario;
        }
        if (configQuizDescription) {
            configQuizDescription.textContent = cuestionario.descripcion || 'Sin descripción';
        }

        // Generar PIN si está activado
        const checkPinAutomatico = document.getElementById('checkPinAutomatico');
        if (checkPinAutomatico && checkPinAutomatico.checked) {
            const pin = generarPin();
            mostrarPin(pin);
        }

        // Asignar evento de cierre
        if (closeConfigBtn) {
            closeConfigBtn.onclick = () => {
                modalConfig.classList.add('hidden');
            };
        }

        // Asignar evento de iniciar partida
        if (iniciarPartidaBtn) {
            iniciarPartidaBtn.onclick = async () => {
                await iniciarPartida();
            };
        }

        // Configurar eventos de los controles
        configurarControlesModal();

        // Mostrar modal
        modalConfig.classList.remove('hidden');
        console.log('✅ Modal de configuración abierto');
    }

    // ====================================================================
    // CONFIGURAR CONTROLES DEL MODAL
    // ====================================================================
    function configurarControlesModal() {
        const pinCheckbox = document.getElementById('checkPinAutomatico');
        const pinDisplay = document.querySelector('.pin-display');

        if (pinCheckbox && pinDisplay) {
            pinCheckbox.onchange = (e) => {
                if (e.target.checked) {
                    mostrarPin(generarPin());
                    pinDisplay.style.display = 'flex';
                } else {
                    pinDisplay.style.display = 'none';
                }
            };
        }

        const modalidadSelect = document.getElementById('modalidadSelect');
        const groupGrupal = document.querySelector('.group-grupal');

        if (modalidadSelect && groupGrupal) {
            modalidadSelect.onchange = (e) => {
                groupGrupal.style.display = e.target.value === 'grupal' ? 'block' : 'none';
            };
        }
    }

    // ====================================================================
    // FUNCIONES DE PIN
    // ====================================================================
    function generarPin() {
        return String(Math.floor(100000 + Math.random() * 900000));
    }

    function mostrarPin(pin) {
        const boxes = document.querySelectorAll('.pin-display .pin-box');
        boxes.forEach((box, idx) => {
            box.textContent = pin[idx] || '0';
        });
    }

    // ====================================================================
    // INICIAR PARTIDA
    // ====================================================================
    async function iniciarPartida() {
        if (!cuestionarioSeleccionado) {
            alert('Error: No se ha seleccionado un cuestionario');
            return;
        }

        console.log('🚀 Iniciando partida...');

        localStorage.setItem("userInteractedWithAudio", "true");
        
        const modalidadSelect = document.getElementById('modalidadSelect');
        const tipo_partida = modalidadSelect.value === 'grupal' ? 'G' : 'I';
        
        const configuracion = {
            cuestionario_id: cuestionarioSeleccionado.cuestionario_id,
            anadir_musica: document.getElementById('checkAnadirMusica').checked,
            modalidad: tipo_partida,
            num_grupos: document.getElementById('numGrupos').value,
            pin_automatico: document.getElementById('checkPinAutomatico').checked,
            pin: Array.from(document.querySelectorAll('.pin-box'))
                .map(b => b.textContent)
                .join('')
        };

        console.log('📦 Configuración de partida:', configuracion);

        sessionStorage.setItem('cuestionario_actual', JSON.stringify(cuestionarioSeleccionado));

        try {
            const res = await fetch(`/api/partidas/crear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configuracion)
            });

            const data = await res.json();

            if (data.status === 'ok') {
                console.log('✅ Partida creada:', data);
                alert(`Partida creada con PIN: ${data.codigo_partida}`);
                setTimeout(() => {
                    window.location.href = `/previapartida/${data.codigo_partida}`;
                }, 300);
            } else {
                console.error('❌ Error del servidor:', data);
                alert('Error al crear la partida: ' + (data.mensaje || 'desconocido'));
            }
        } catch (error) {
            console.error('❌ Error al iniciar la partida:', error);
            alert('Ocurrió un error en la conexión al crear la partida.');
        }

        const modalConfig = document.getElementById('configuracionPartidaModal');
        if (modalConfig) {
            modalConfig.classList.add('hidden');
        }
    }

    console.log('✅ Script partidas_profesor.js completamente inicializado');
});