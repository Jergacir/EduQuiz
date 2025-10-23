// static/js/cuentaregresiva.js

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    
    // ⭐️ CORRECCIÓN: Usamos el operador OR (||) para asegurar que las variables no sean null/undefined.
    const codigoPartida = body.dataset.codigoPartida || '';
    const tipoUsuario = body.dataset.tipoUsuario || ''; // 'P' para Profesor, 'A' para Alumno

    const display = document.getElementById('countdown-display');
    let count = 3;

    console.log(`Código leído: ${codigoPartida}, Tipo Usuario leído: ${tipoUsuario}`);
    console.log(`⏰ Iniciando cuenta regresiva...`);
    
    // Función para manejar la cuenta regresiva
    function startCountdown() {
        if (display) {
            // Aseguramos que solo muestre el número cuando es > 0
            display.textContent = count > 0 ? count : '¡GO!'; 
        }

        if (count > 0) {
            count--;
            // Llama a la función de nuevo después de 1 segundo
            setTimeout(startCountdown, 1000); 
        } else {
            // Cuando la cuenta llega a 0, se realiza la redirección
            redirectToGame();
        }
    }

    // Función de redirección
    function redirectToGame() {
        let redirectUrl = '';
        
        // ⭐️ CORRECCIÓN: Usamos la variable segura codigoPartida (que es '' si no se cargó)
        if (codigoPartida === '' || tipoUsuario === '') {
             console.error("❌ Error grave: Faltan datos de partida o usuario. Redirigiendo a /partidas.");
             window.location.href = '/partidas'; 
             return;
        }

        if (tipoUsuario === 'P') {
            // Redirige al profesor a la vista de preguntas
            redirectUrl = `/preguntasprofesor/${codigoPartida}`;
            console.log("🚀 Redirigiendo al Profesor a la vista de preguntas...");
            
        } else if (tipoUsuario === 'A') {
            // Redirige al alumno a la vista de preguntas
            redirectUrl = `/preguntasalumno/${codigoPartida}`;
            console.log("🚀 Redirigiendo al Alumno a la vista de juego...");
            
        } else {
            console.error(`❌ Error: Tipo de usuario desconocido (${tipoUsuario}). Redirigiendo a home.`);
            redirectUrl = '/'; 
        }
        
        // Ejecutar la redirección
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }

    // Iniciar el proceso de cuenta regresiva
    startCountdown();
});