

// static/js/previapartida.js
document.addEventListener("DOMContentLoaded", () => {

    console.log("🎮 previapartida.js cargado correctamente.");

    // -----------------------------
    // 🔹 Recuperar datos desde los data-attributes del body
    // -----------------------------
    const body = document.body;

    // loggedUser puede ser objeto o null
    const loggedUser = JSON.parse(body.dataset.loggedUser || "null");
    // isGroupGame debe ser booleano
    const isGroupGame = JSON.parse(body.dataset.isGroupGame || "false");
    const numGrupos = parseInt(body.dataset.numGrupos || "3");
    console.log("Número de grupos configurado:", numGrupos);
    console.log("Usuario logueado:", loggedUser);
    console.log("Es juego grupal?", isGroupGame);

    // -----------------------------------------------
    // 🎵 Recuperar canción elegida en la configuración
    // -----------------------------------------------
    const musicaActiva = localStorage.getItem("musicaActiva");
    const cancionGuardada = localStorage.getItem("cancionActual");

    let musicaActual = null;

    if (musicaActiva === "true" && cancionGuardada) {
        musicaActual = new Audio(cancionGuardada);
        musicaActual.loop = true;
        musicaActual.volume = 0.4;
        musicaActual.play();
        console.log("🎧 Reproduciendo la misma canción elegida:", cancionGuardada);
    } else {
        console.log("⚠️ No hay música activa o no se guardó canción.");
    }

    // -----------------------------------------------
    // 📋 Lógica del botón copiar código de partida
    // -----------------------------------------------
    const copyBtn = document.querySelector(".copy-icon");
    if (copyBtn) {
        copyBtn.addEventListener("click", () => {
            const code = document.querySelector(".game-code").textContent.trim();
            navigator.clipboard.writeText(code)
                .then(() => alert(`Código copiado: ${code}`))
                .catch(err => console.error("Error al copiar código:", err));
        });
    }

    // -----------------------------------------------
    // 🕹️ Botón “Iniciar Partida”
    // -----------------------------------------------
    const startBtn = document.querySelector(".start-game-button");
    if (startBtn) {
        startBtn.addEventListener("click", () => {
            console.log("🚀 Iniciando partida...");

            // Detener música
            if (musicaActual) {
                musicaActual.pause();
                musicaActual = null;
            }

            // Limpiar localStorage

            localStorage.removeItem("cancionActual");

            // Redirigir (ajusta la URL según tu lógica)
            // const codigoPartida = document.querySelector(".game-code").textContent.trim();
            // window.location.href = `/partida/${codigoPartida}`;
        });
    }



    // -----------------------------
    // 🟢 Contenedor y renderizado de participantes
    // -----------------------------
    const container = document.querySelector('#group-view') || document.querySelector('#individual-view');
    const codigoPartida = document.querySelector(".game-code").textContent.trim();

    // Crear dinámicamente las columnas de grupo
    if (isGroupGame) {
        const groupView = document.getElementById('group-view');
        groupView.innerHTML = ''; // limpiar por si acaso

        for (let i = 1; i <= numGrupos; i++) {
            const col = document.createElement('div');
            col.classList.add('group-column');
            col.innerHTML = `<h3 class="group-title">Grupo ${String(i).padStart(2, '0')}</h3>`;
            groupView.appendChild(col);
        }
    }
    function renderParticipantes(participantes) {
    const individualView = document.getElementById('individual-view');
    const groupView = document.getElementById('group-view');

    // 🔹 Si es juego individual
    if (!isGroupGame) {
        individualView.innerHTML = '';
        participantes.forEach(usuario => {
            const div = document.createElement('div');
            div.classList.add('participant-card');
            div.dataset.usuarioId = usuario.usuario_id;
            div.innerHTML = `
                <img src="${usuario.avatar || '/static/img/default-avatar.png'}" alt="Avatar" class="user-avatar">
                <span class="username">${usuario.nombre}</span>
            `;
            individualView.appendChild(div);
        });
        return;
    }

    // 🔹 Si es juego grupal
    groupView.innerHTML = '';

    // Crear columnas de grupo
    const columnas = [];
    for (let i = 1; i <= numGrupos; i++) {
        const col = document.createElement('div');
        col.classList.add('group-column');
        col.innerHTML = `<h3 class="group-title">Grupo ${String(i).padStart(2, '0')}</h3>`;
        groupView.appendChild(col);
        columnas.push(col);
    }

    // Columna de sin grupo
    const sinGrupoCol = document.createElement('div');
    sinGrupoCol.classList.add('group-column');
    sinGrupoCol.innerHTML = `<h3 class="group-title">Sin grupo</h3>`;
    groupView.appendChild(sinGrupoCol);

    // 🔹 Mostrar participantes
    participantes.forEach(usuario => {
        const tarjeta = document.createElement("div");
        tarjeta.classList.add("tarjeta-usuario", "usuario-en-grupo");
        tarjeta.title = usuario.nombre;

        // Mostrar bandera si es líder
        const esLider = usuario.lider_id === usuario.participante_id;
        const iconoLider = esLider ? `<span class="lider-icon" title="Líder del grupo">🏁</span>` : '';

        tarjeta.innerHTML = `
            <div class="usuario-info">
                <img src="${usuario.avatar || '/static/img/default-avatar.png'}" alt="Avatar">
                <span>${usuario.nombre}</span>
                ${iconoLider}
            </div>
        `;

        // Si el profesor hace clic, puede designar líder
        if (loggedUser && loggedUser.tipo_usuario === 'P' && usuario.grupo_id) {
            tarjeta.addEventListener('click', () => {
                if (confirm(`¿Designar a ${usuario.nombre} como líder del grupo ${usuario.grupo_id}?`)) {
                    socket.emit('designar_lider', {
                        codigo_partida: codigoPartida,
                        grupo_id: usuario.grupo_id,
                        lider_participante_id: usuario.participante_id
                    });
                }
            });
        }

        if (usuario.grupo_id && usuario.grupo_id >= 1 && usuario.grupo_id <= numGrupos) {
            columnas[usuario.grupo_id - 1].appendChild(tarjeta);
        } else {
            sinGrupoCol.appendChild(tarjeta);
        }
    });
}

    // 🔹 1️⃣ Cargar participantes actuales desde backend
    fetch(`/api/partida/${codigoPartida}/participantes`)
        .then(res => res.json())
        .then(data => {
            renderParticipantes(data.participantes || []);
        })
        .catch(err => console.error("Error cargando participantes:", err));

    // -----------------------------
    // 🌐 SOCKET.IO para actualizaciones en tiempo real
    // -----------------------------
    const socket = io();

    // Logs para depuración
    socket.on('connect', () => console.log('✅ Socket conectado', socket.id));
    socket.on('disconnect', () => console.log('❌ Socket desconectado'));
    socket.on('actualizar_participantes', data => {
        console.log('🔹 Recibido actualizar_participantes:', data);
        renderParticipantes(data.participantes || []);
    });

    // Emitir evento de unión a la sala después de conectar
    socket.emit('unirse_sala', {
        codigo_partida: codigoPartida,
        usuario: loggedUser
    });

    // -----------------------------
    // 🔄 Vista individual o grupal
    // -----------------------------
    if (isGroupGame) {
        document.getElementById('individual-view').style.display = 'none';
        document.getElementById('group-view').style.display = 'flex';
    } else {
        document.getElementById('individual-view').style.display = 'flex';
        document.getElementById('group-view').style.display = 'none';
    }
});
