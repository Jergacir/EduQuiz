document.addEventListener("DOMContentLoaded", () => {
    const gameCodeInput = document.getElementById("gameCodeInput");
    const joinButton = document.getElementById("joinButton");
    const messageArea = document.getElementById("messageArea");
    const usuarioId = document.body.dataset.usuarioId;

    // Lógica para limitar la entrada a 6 caracteres (y mayúsculas)
    gameCodeInput.addEventListener('input', function() {
        // Convierte a mayúsculas y limita a 6 caracteres
        this.value = this.value.toUpperCase().slice(0, 6);
    });

    joinButton.addEventListener('click', async () => {
        const codigoPartida = gameCodeInput.value.trim();
        
        messageArea.textContent = "";
        messageArea.classList.remove("error", "success");

        if (codigoPartida.length !== 6) {
            messageArea.textContent = "El código debe tener 6 caracteres.";
            messageArea.classList.add("error");
            return;
        }

        // Deshabilitar botón para evitar envíos múltiples
        joinButton.disabled = true;
        joinButton.textContent = "Uniéndose...";

        try {
            const response = await fetch('/api/partida/unirse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ codigo: codigoPartida, usuario_id: usuarioId }),
            });

            const result = await response.json();

            if (response.ok) {
                messageArea.textContent = result.message;
                messageArea.classList.add("success");
                
                // Redirigir al usuario a la pantalla de juego/espera
                setTimeout(() => {
                    window.location.href = result.redirect_url; 
                }, 1500);

            } else {
                // Error 400 o cualquier otro error de la API
                messageArea.textContent = result.message || "Error al unirse. Inténtalo de nuevo.";
                messageArea.classList.add("error");
            }

        } catch (error) {
            console.error('Error de red:', error);
            messageArea.textContent = "Error de conexión con el servidor.";
            messageArea.classList.add("error");
        } finally {
            joinButton.disabled = false;
            joinButton.innerHTML = '<i class="icon-play"></i> Unirme';
        }
    });
});