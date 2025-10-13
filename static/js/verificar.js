document.addEventListener('DOMContentLoaded', function () {
    // --- Carrusel ---
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

    // --- Manejo de inputs de verificación (6 cajas) ---
    const codigoInputs = Array.from(document.querySelectorAll('.codigo-box'));
    const formVerificar = document.getElementById('form-verificar');
    const codigoHidden = document.getElementById('codigo-hidden');

    if(codigoInputs.length){
        // Foco en primer input
        codigoInputs[0].addEventListener('focus', () => codigoInputs[0].select());

        codigoInputs.forEach((input, idx) => {
            input.addEventListener('input', (e) => {
                const v = e.target.value.replace(/[^0-9]/g,'');
                e.target.value = v;
                if(v && idx < codigoInputs.length - 1){
                    codigoInputs[idx+1].focus();
                }
            });

            input.addEventListener('keydown', (e) => {
                if(e.key === 'Backspace' && !e.target.value && idx > 0){
                    codigoInputs[idx-1].focus();
                }
                // Permitir flechas para navegar
                if(e.key === 'ArrowLeft' && idx>0) codigoInputs[idx-1].focus();
                if(e.key === 'ArrowRight' && idx < codigoInputs.length-1) codigoInputs[idx+1].focus();
            });

            // Pegar soporte: si el usuario pega 6 dígitos en una caja, distribuir
            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const paste = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
                if(!paste) return;
                for(let i=0;i<codigoInputs.length;i++){
                    codigoInputs[i].value = paste[i] || '';
                }
                // mover foco al final
                const filled = Math.min(paste.length, codigoInputs.length) - 1;
                if(filled >= 0) codigoInputs[Math.min(filled+1, codigoInputs.length-1)].focus();
            });
        });

        // Antes de enviar el form, rellenar el hidden
        if(formVerificar){
            formVerificar.addEventListener('submit', function(ev){
                // Ensamblar codigo
                const codigo = codigoInputs.map(i=>i.value||'').join('');
                codigoHidden.value = codigo;
                // Si no completo, prevenir submit y avisar
                if(codigo.length !== codigoInputs.length){
                    ev.preventDefault();
                    alert('Ingresa el código completo de 6 dígitos.');
                    codigoInputs.find(i=>!i.value)?.focus();
                    return;
                }

                // Enviar por fetch (JSON) y mostrar modal si success
                ev.preventDefault();
                const email = (formVerificar.querySelector('input[name=email]')||{}).value || '';
                const payload = { email, codigo };

                fetch(formVerificar.action, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify(payload),
                }).then(async res => {
                    let data = null;
                    try { data = await res.json(); } catch(e){ data = null; }

                    if(data && data.success){
                        const modal = document.getElementById('modal-exito');
                        if(modal){ modal.setAttribute('aria-hidden','false'); }
                    } else if(data && !data.success){
                        // Mostrar modal de error con mensaje del servidor
                        const modalErr = document.getElementById('modal-error');
                        const title = document.getElementById('modal-error-title');
                        const msg = document.getElementById('modal-error-msg');
                        if(title) title.textContent = 'Error al verificar';
                        if(msg) msg.textContent = data.message || 'No se pudo verificar tu cuenta.';
                        if(modalErr) modalErr.setAttribute('aria-hidden','false');
                    } else {
                        // No recibimos JSON: tratar como error general
                        const modalErr = document.getElementById('modal-error');
                        const title = document.getElementById('modal-error-title');
                        const msg = document.getElementById('modal-error-msg');
                        if(title) title.textContent = 'Error de servidor';
                        if(msg) msg.textContent = 'Respuesta inesperada del servidor.';
                        if(modalErr) modalErr.setAttribute('aria-hidden','false');
                    }
                }).catch(err => {
                    console.error(err);
                    const modalErr = document.getElementById('modal-error');
                    const title = document.getElementById('modal-error-title');
                    const msg = document.getElementById('modal-error-msg');
                    if(title) title.textContent = 'Error de red';
                    if(msg) msg.textContent = 'No se pudo conectar al servidor. Revisa tu conexión e intenta nuevamente.';
                    if(modalErr) modalErr.setAttribute('aria-hidden','false');
                });
            });
        }
    }

    // Manejo del modal (botón iniciar sesión, cerrar fuera o Escape)
    const modal = document.getElementById('modal-exito');
    const modalBtn = document.getElementById('modal-iniciar');
    if(modal && modalBtn){
        modalBtn.addEventListener('click', () => { window.location.href = '/login'; });
        // cerrar al clickear fuera
        modal.addEventListener('click', (e) => {
            if(e.target === modal) modal.setAttribute('aria-hidden','true');
        });
        document.addEventListener('keydown', (e) => {
            if(e.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') modal.setAttribute('aria-hidden','true');
        });
    }

    // Manejo modal de error
    const modalErr = document.getElementById('modal-error');
    const modalErrCerrar = document.getElementById('modal-error-cerrar');
    if(modalErr && modalErrCerrar){
        modalErrCerrar.addEventListener('click', () => modalErr.setAttribute('aria-hidden','true'));
        modalErr.addEventListener('click', (e) => { if(e.target === modalErr) modalErr.setAttribute('aria-hidden','true'); });
    }

    // Reenviar código usando JSON (antes se hacía form-urlencoded)
    const btnReenviar = document.getElementById('btn-reenviar');
    if(btnReenviar){
        let reenviando = false;
        btnReenviar.addEventListener('click', async () => {
            if(reenviando) return; // evitar doble click
            reenviando = true;
            btnReenviar.setAttribute('disabled','true');
            btnReenviar.setAttribute('aria-busy','true');
            const email = (document.querySelector('input[name=email]')||{}).value || '';
            try{
                const resp = await fetch("/reenviar_codigo", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await resp.json();
                if(data && data.success){
                    // Mostrar un toast temporal en lugar de usar el modal principal
                    const toast = document.createElement('div');
                    toast.textContent = data.message || 'Código reenviado. Revisa tu correo.';
                    Object.assign(toast.style, {
                        position: 'fixed',
                        left: '20px',
                        top: '20px',
                        background: '#111',
                        color: '#fff',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        boxShadow: '0 6px 18px rgba(2,6,23,0.2)',
                        zIndex: 200
                    });
                    document.body.appendChild(toast);
                    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 300ms'; }, 2200);
                    setTimeout(() => { toast.remove(); }, 2600);
                    // re-habilitar después de mostrar
                    setTimeout(() => { reenviando = false; btnReenviar.removeAttribute('disabled'); btnReenviar.removeAttribute('aria-busy'); }, 2600);
                } else {
                    const modalErr = document.getElementById('modal-error');
                    const title = document.getElementById('modal-error-title');
                    const msg = document.getElementById('modal-error-msg');
                    if(title) title.textContent = 'No se pudo reenviar';
                    if(msg) msg.textContent = data && data.message ? data.message : 'No se pudo reenviar el código.';
                    if(modalErr) modalErr.setAttribute('aria-hidden','false');
                    reenviando = false; btnReenviar.removeAttribute('disabled'); btnReenviar.removeAttribute('aria-busy');
                }
            }catch(err){
                console.error(err);
                const modalErr = document.getElementById('modal-error');
                const title = document.getElementById('modal-error-title');
                const msg = document.getElementById('modal-error-msg');
                if(title) title.textContent = 'Error de red';
                if(msg) msg.textContent = 'No se pudo conectar al servidor.';
                if(modalErr) modalErr.setAttribute('aria-hidden','false');
                reenviando = false; btnReenviar.removeAttribute('disabled'); btnReenviar.removeAttribute('aria-busy');
            }
        });
    }

});
