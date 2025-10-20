// static/js/salaespera.js
document.addEventListener("DOMContentLoaded", () => {
    const usuarioId = document.body.dataset.usuarioId;
    const tipoUsuario = document.body.dataset.tipoUsuario; // 'A' o 'P'
    const codigoPartida = document.body.dataset.codigoPartida;

    // Solo los alumnos participan
    if (tipoUsuario !== 'A') return;

    const socket = io();

    // 🔹 Modal de selección de grupo
    const modalGrupos = document.getElementById("modalGrupos");
    const gruposLista = modalGrupos.querySelector(".grupos-lista");

    // Obtenemos los grupos de la sala (puede ser dinámico, aquí hardcode ejemplo)
    const grupos = ["Grupo 01", "Grupo 02", "Grupo 03"];

    grupos.forEach((nombreGrupo) => {
        const btn = document.createElement("button");
        btn.className = "grupo-btn";
        btn.textContent = nombreGrupo;
        btn.addEventListener("click", () => {
            unirseAGrupo(nombreGrupo);
        });
        gruposLista.appendChild(btn);
    });

    // Abrir modal automáticamente
    modalGrupos.classList.remove("hidden");

    document.getElementById("cerrarModalGrupos").addEventListener("click", () => {
        modalGrupos.classList.add("hidden");
    });

    // Función para unirse a un grupo
    function unirseAGrupo(grupoSeleccionado) {
        console.log("Me uno a:", grupoSeleccionado);

        // Notificar al backend / socket
        //socket.emit("unirse_grupo", {
            //codigo_partida: codigoPartida,
            //usuario_id: usuarioId,
            //grupo: grupoSeleccionado
        //});

        // Actualizar UI
        const listaGrupos = document.querySelectorAll(".tarjeta-grupo");
        listaGrupos.forEach(tarjeta => {
            const encabezado = tarjeta.querySelector(".encabezado-grupo").textContent;
            if (encabezado === grupoSeleccionado) {
                const listaUsuarios = tarjeta.querySelector(".lista-usuarios");
                const divUsuario = document.createElement("div");
                divUsuario.className = "usuario";
                divUsuario.innerHTML = `<img src="/static/img/default-avatar.png" alt="Avatar"><span>Tu nombre</span>`;
                listaUsuarios.appendChild(divUsuario);
            }
        });

        // Cerrar modal
        modalGrupos.classList.add("hidden");
    }
    // 🔹 Unirse a la sala (solo notificación al backend)
    socket.emit('unirse_sala', { codigo_partida: codigoPartida, usuario: { usuario_id: usuarioId } });

    // 🔹 Mostrar únicamente tu usuario en sala de espera
    const lista = document.querySelector('.tarjeta-usuario');
    if (lista) {
        lista.innerHTML = `
        <div class="usuario">
            <img src="/static/img/default-avatar.png" alt="Avatar">
            <span>Tu nombre</span>
        </div>`;
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
