document.addEventListener('DOMContentLoaded', function () {

    const form = document.querySelector('form');
    const dniInput = document.getElementById('dni');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('contrasena');
    const confirmPasswordInput = document.getElementById('confirmarContrasena');
    const emailDomainSpan = document.querySelector('.campo-con-dominio span');

    form.addEventListener('submit', function (event) {
        // Evita que el formulario se envíe automáticamente
        event.preventDefault(); 

        // Validaciones en un orden lógico
        if (dniInput.value.trim() === '') {
            alert('Por favor, ingresa tu DNI.');
            dniInput.focus();
            return; 
        }

        if (dniInput.value.length !== 8) {
            alert('El DNI debe tener 8 dígitos.');
            dniInput.focus();
            return;
        }

        if (emailInput.value.trim() === '') {
            alert('Por favor, ingresa tu correo electrónico.');
            emailInput.focus();
            return;
        }

        if (passwordInput.value.trim() === '') {
            alert('Por favor, ingresa una contraseña.');
            passwordInput.focus();
            return;
        }

        if (confirmPasswordInput.value.trim() === '') {
            alert('Por favor, confirma tu contraseña.');
            confirmPasswordInput.focus();
            return;
        }

        // Valida que las contraseñas coincidan
        if (passwordInput.value !== confirmPasswordInput.value) {
            alert('Las contraseñas no coinciden. Por favor, inténtalo de nuevo.');
            confirmPasswordInput.focus();
            return;
        }

        // Si todas las validaciones pasaron, completa el email y envía el formulario
        const fullEmail = emailInput.value.trim() + emailDomainSpan.textContent;
        emailInput.value = fullEmail;
        

        form.submit();
    });
});