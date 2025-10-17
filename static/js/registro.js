document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const tipoSelect = document.getElementById('tipo');
    const dniInput = document.getElementById('dni');
    const grupoDni = document.getElementById('grupo-dni');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('contrasena');
    const confirmPasswordInput = document.getElementById('confirmarContrasena');
    const emailDomainSpan = document.getElementById('email-domain');
    const labelEmail = document.getElementById('label-email');

    // 🔹 Cambia dinámicamente según el tipo de usuario
    tipoSelect.addEventListener('change', function () {
        if (tipoSelect.value === 'Alumno') {
            grupoDni.style.display = 'none'; // ocultar DNI
            dniInput.removeAttribute('required');

            labelEmail.textContent = 'DNI';
            emailInput.placeholder = 'DNI*';
            emailDomainSpan.textContent = '@usat.pe';
        } else {
            grupoDni.style.display = 'block'; // mostrar DNI
            dniInput.setAttribute('required', true);

            labelEmail.textContent = 'Correo electrónico';
            emailInput.placeholder = 'Correo electrónico*';
            emailDomainSpan.textContent = '@usat.edu.pe';
        }
    });

    // 🔹 Validación y envío
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        if (tipoSelect.value === 'Docente') {
            if (dniInput.value.trim() === '' || dniInput.value.length !== 8) {
                alert('Por favor, ingresa un DNI válido de 8 dígitos.');
                dniInput.focus();
                return;
            }
        }

        if (emailInput.value.trim() === '') {
            alert('Por favor, ingresa el ' + (tipoSelect.value === 'Alumno' ? 'DNI' : 'correo'));
            emailInput.focus();
            return;
        }

        if (passwordInput.value.trim() === '') {
            alert('Por favor, ingresa una contraseña.');
            passwordInput.focus();
            return;
        }

        // Validación de contraseña fuerte
        const pwd = passwordInput.value;
        const pwdErrors = [];
        if (pwd.length < 8) pwdErrors.push('al menos 8 caracteres');
        if (!/[A-Z]/.test(pwd)) pwdErrors.push('una letra mayúscula');
        if (!/[a-z]/.test(pwd)) pwdErrors.push('una letra minúscula');
        if (!/[0-9]/.test(pwd)) pwdErrors.push('un número');
        if (!/[!@#\$%\^&\*\(\)\-_\+=\[\]{};:\"'\\|,.<>\/?]/.test(pwd)) pwdErrors.push('un carácter especial');
        if (pwdErrors.length > 0) {
            // Mostrar modal en vez de alert
            const msg = 'La contraseña debe contener ' + pwdErrors.join(', ');
            showModal('Contraseña débil', msg);
            passwordInput.focus();
            return;
        }

        if (confirmPasswordInput.value.trim() === '') {
            alert('Por favor, confirma tu contraseña.');
            confirmPasswordInput.focus();
            return;
        }

        if (passwordInput.value !== confirmPasswordInput.value) {
            alert('Las contraseñas no coinciden. Por favor, inténtalo de nuevo.');
            confirmPasswordInput.focus();
            return;
        }

        // 🔹 Completar correo y dni automáticamente para alumnos
        if (tipoSelect.value === 'Alumno') {
            const dni = emailInput.value.trim();
            if (dni.length !== 8 || isNaN(dni)) {
                alert('El DNI debe tener exactamente 8 dígitos numéricos.');
                emailInput.focus();
                return;
            }
            // El correo será dni@usat.pe
            emailInput.value = dni + emailDomainSpan.textContent;
            // Mandamos el dni en el input oculto
            dniInput.value = dni;
        } else {
            // Docente → correo normal
            emailInput.value = emailInput.value.trim() + emailDomainSpan.textContent;
        }

        form.submit();
    });

    // --- Carrusel Registro ---
    const frases = [
        { titulo: "Tu camino al éxito académico", texto: "Domina cada materia y alcanza el máximo potencial en tu carrera." },
        { titulo: "Aprendizaje dinámico", texto: "Convierte cada clase en una experiencia interactiva y entretenida." },
        { titulo: "Alcanza tus metas", texto: "EduQuiz te acompaña en cada paso hacia el logro de tus objetivos." }
    ];

    const titulo = document.querySelector('.panel-derecho-contenido h2');
    const texto = document.querySelector('.panel-derecho-contenido p');
    const dots = document.querySelectorAll('.punto-carrusel');
    const imagenes = document.querySelectorAll('.carousel-image'); // 🔹 capturar imágenes

    let indice = 0;

    function cambiarFrase(i) {
        // Cambiar título y texto
        titulo.textContent = frases[i].titulo;
        texto.textContent = frases[i].texto;

        // Cambiar imagen activa
        imagenes.forEach((img, idx) => {
            img.classList.toggle('active', idx === i);
        });

        // Cambiar punto activo
        dots.forEach((dot, idx) => {
            dot.classList.toggle('activo', idx === i);
        });
    }

    // Cambio automático cada 4s
    setInterval(() => {
        indice = (indice + 1) % frases.length;
        cambiarFrase(indice);
    }, 4000);

    // Clic manual en los puntos
    dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => {
            indice = idx;
            cambiarFrase(indice);
        });
    });

});

// --- Modal reutilizable creado desde JS (sin tocar templates) ---
function showModal(title, message) {
    // Si ya existe, actualizar y mostrar
    let existing = document.getElementById('rg-modal');
    if (!existing) {
        const modal = document.createElement('div');
        modal.id = 'rg-modal';
        modal.classList.add('rg-modal-overlay');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');

        const box = document.createElement('div');
        box.classList.add('rg-modal-box');

        const h = document.createElement('h3');
        h.textContent = title;

        const p = document.createElement('p');
        p.innerHTML = message.replace(/\n/g, '<br>');

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = 'Aceptar';
        btn.classList.add('rg-modal-accept');

        // Cerrar modal al hacer click en aceptar
        btn.addEventListener('click', () => {
            closeModal();
        });

        // Cerrar al clicar fuera del cuadro (overlay)
        modal.addEventListener('click', (ev) => {
            if (ev.target === modal) closeModal();
        });

        box.appendChild(h);
        box.appendChild(p);
        box.appendChild(btn);
        modal.appendChild(box);
        document.body.appendChild(modal);
        existing = modal;
    } else {
        // actualizar contenido
        const h = existing.querySelector('h3');
        const p = existing.querySelector('p');
        if (h) h.textContent = title;
        if (p) p.innerHTML = message.replace(/\n/g, '<br>');
        existing.classList.remove('rg-modal-hidden');
    }
}

function closeModal() {
    const m = document.getElementById('rg-modal');
    if (m && m.parentNode) m.parentNode.removeChild(m);
}

// Cerrar con la tecla Escape cuando el modal esté abierto
document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
        const m = document.getElementById('rg-modal');
        if (m) closeModal();
    }
});
