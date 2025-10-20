

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

    function renderParticipantes(participantes) {
        const individualView = document.getElementById('individual-view');
        individualView.innerHTML = ''; // limpiar participantes previos
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
