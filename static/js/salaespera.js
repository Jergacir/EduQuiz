// static/js/salaespera.js
document.addEventListener("DOMContentLoaded", () => {
    const usuarioId = document.body.dataset.usuarioId;
    const tipoUsuario = document.body.dataset.tipoUsuario; // 'A' o 'P'
    const codigoPartida = document.body.dataset.codigoPartida;
    const numGrupos = parseInt(document.body.dataset.numGrupos || "3"); // <--- aquí
    // Solo los alumnos participan
    // Verificar tipo de usuario

    if (tipoUsuario !== 'A') {
        console.log("⛔ No es alumno, no se ejecuta sala de espera del alumno.");
        return;
    }

    const socket = io();
    socket.on('actualizar_participantes', (data) => {
        const participantes = data.participantes || [];
        console.log("📡 Actualización de participantes recibida:", participantes);

        // Limpia todas las listas de usuarios
        document.querySelectorAll('.lista-usuarios').forEach(lista => lista.innerHTML = '');

        // Mostrar los participantes dentro de sus grupos
        participantes.forEach(p => {
            const grupoId = p.grupo_id || 0; // Si no tiene grupo, va a "sin grupo"
            const tarjeta = document.querySelector(`.tarjeta-grupo[data-grupo-id="${grupoId}"]`);
            if (!tarjeta) return;

            const listaUsuarios = tarjeta.querySelector('.lista-usuarios');
            const usuarioDiv = document.createElement('div');
            usuarioDiv.className = 'usuario';
            usuarioDiv.dataset.usuarioId = p.usuario_id;

            // 🔹 Mostrar líder con corona
            if (p.lider_id && p.lider_id === p.participante_id) {
                usuarioDiv.classList.add('lider');
                usuarioDiv.innerHTML = `
                <img src="/static/img/default-avatar.png" alt="Avatar">
                <span>👑 ${p.nombre}</span>
            `;
            } else {
                usuarioDiv.innerHTML = `
                <img src="/static/img/default-avatar.png" alt="Avatar">
                <span>${p.nombre}</span>
            `;
            }

            listaUsuarios.appendChild(usuarioDiv);
        });


    });
    // 🔹 Contenedor de grupos
    const gruposContenedor = document.querySelector('.grupos-contenedor');
    if (gruposContenedor) {
        gruposContenedor.innerHTML = '';

        // Crear tarjetas de grupo dinámicamente
        for (let i = 0; i < numGrupos; i++) {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta-grupo';
            tarjeta.dataset.grupoId = i + 1;
            tarjeta.innerHTML = `
            <div class="encabezado-grupo">Grupo ${String(i + 1).padStart(2, '0')}</div>
            <div class="lista-usuarios"></div>
            <button class="boton-unirse"><span class="icono-mas">+</span> Unirse al equipo</button>
        `;
            gruposContenedor.appendChild(tarjeta);

            tarjeta.querySelector('.boton-unirse').addEventListener('click', () => {
                unirseAGrupo(i + 1);
            });
        }
    }

    // 🔹 Función para unirse a un grupo directamente
    function unirseAGrupo(grupoSeleccionado) {
        console.log("Me uno a:", grupoSeleccionado);

        // 🔹 Buscar si el usuario ya está en algún grupo
        document.querySelectorAll('.lista-usuarios').forEach(lista => {
            const usuarioExistente = lista.querySelector(`.usuario[data-usuario-id="${usuarioId}"]`);
            if (usuarioExistente) {
                lista.removeChild(usuarioExistente);
            }
        });

        const tarjeta = document.querySelector(`.tarjeta-grupo[data-grupo-id="${grupoSeleccionado}"]`);
        if (!tarjeta) return;

        const listaUsuarios = tarjeta.querySelector('.lista-usuarios');


        // 🔹 Mover la tarjeta-usuario dentro del grupo
        const tarjetaUsuario = document.querySelector('.tarjeta-usuario');
        if (tarjetaUsuario) {
            tarjetaUsuario.dataset.usuarioId = usuarioId; // aseguramos el id
            tarjetaUsuario.classList.add('usuario-en-grupo'); // por si quieres estilos distintos
            listaUsuarios.appendChild(tarjetaUsuario); // la movemos al grupo
        } else {
            console.warn("⚠️ No se encontró la tarjeta del usuario para mover al grupo.");
        }

        // 🔹 Emitir al backend para actualizar en tiempo real
        socket.emit("unirse_grupo", {
            codigo_partida: codigoPartida,
            usuario_id: usuarioId,
            grupo_id: grupoSeleccionado
        });
    }


    // 🔹 Escuchar actualizaciones de grupos desde el servidor
    socket.on('actualizar_grupos', (data) => {
        // data = [{usuario_id, nombre, grupo_id, avatar}, ...]
        document.querySelectorAll('.lista-usuarios').forEach(list => list.innerHTML = '');

        data.forEach(u => {
            const tarjeta = document.querySelector(`.tarjeta-grupo[data-grupo-id="${u.grupo_id}"]`);
            if (!tarjeta) return;

            const listaUsuarios = tarjeta.querySelector('.lista-usuarios');
            const divUsuario = document.createElement('div');
            divUsuario.className = 'usuario';
            divUsuario.innerHTML = `<img src="${u.avatar || '/static/img/default-avatar.png'}" alt="Avatar"><span>${u.nombre}</span>`;
            listaUsuarios.appendChild(divUsuario);
        });
    });
    // 🔹 Unirse a la sala (solo notificación al backend)
    socket.emit('unirse_sala', { codigo_partida: codigoPartida, usuario: { usuario_id: usuarioId } });

    // 🔹 Mostrar únicamente tu usuario en sala de espera
    const lista = document.querySelector('.tarjeta-usuario');
    if (lista) {

        const nombreUsuario = lista.dataset.nombreUsuario || "Usuario";
        lista.innerHTML = `
        <div class="usuario">
            <img src="/static/img/default-avatar.png" alt="Avatar">
            <span>${nombreUsuario}</span>
        </div>`;
    } else {
        console.warn("⚠️ No se encontró .tarjeta-usuario en el DOM.");
    }

    // 🔹 Botón salir
    const salirBtn = document.querySelector('#btnSalir');
    if (salirBtn) {
        salirBtn.addEventListener('click', () => {
            if (confirm("¿Estás seguro que quieres salir de la partida?")) {
                // Primero actualizamos la BD
                fetch('/api/partida/salir', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ codigo_partida: codigoPartida, usuario_id: usuarioId })
                }).finally(() => {
                    // Emitimos socket para notificar a otras vistas
                    socket.emit('salir_sala', { codigo_partida: codigoPartida, usuario_id: usuarioId });
                    // Redirigimos al menú
                    window.location.href = '/partidas';
                });
            }
        });
    }

    // 🔹 Manejar refresh o cerrar pestaña
    window.addEventListener("beforeunload", (e) => {
        // Actualizar BD usando sendBeacon (para garantizar envío aunque se cierre la pestaña)
        navigator.sendBeacon('/api/partida/salir', JSON.stringify({
            codigo_partida: codigoPartida,
            usuario_id: usuarioId
        }));

        // Emitir socket
        socket.emit('salir_sala', { codigo_partida: codigoPartida, usuario_id: usuarioId });

        e.preventDefault();
        e.returnValue = "";
    });

    // 🔹 Opcional: logs de socket
    socket.on('connect', () => console.log('✅ Socket conectado', socket.id));
    socket.on('disconnect', () => console.log('❌ Socket desconectado'));
});
