document.addEventListener('DOMContentLoaded', function () {
    // Frases (texto del panel)
    const frases = [
        { titulo: "Aprende de forma divertida", texto: "Gana puntos y compite con tus amigos mientras estudias tus cursos." },
        { titulo: "Refuerza tus conocimientos", texto: "Convierte cada reto en una oportunidad para mejorar." },
        { titulo: "Avanza paso a paso", texto: "Supera niveles y demuestra lo que sabes en cada materia." }
    ];

    const slides = Array.from(document.querySelectorAll('.carousel-image'));
    const dotsContainer = document.querySelector('.carousel-dots');
    const tituloElem = document.querySelector('.left-panel-content h2');
    const textoElem = document.querySelector('.left-panel-content p');
    const leftPanel = document.querySelector('.left-panel');

    if (!slides.length) return; // nada que hacer si no hay imágenes

    // --- Crear puntos dinámicamente (coinciden con la cantidad de imágenes) ---
    dotsContainer.innerHTML = '';
    const dots = slides.map((_, i) => {
        const d = document.createElement('div');
        d.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        dotsContainer.appendChild(d);
        d.addEventListener('click', () => goTo(i));
        return d;
    });

    // Estado
    let index = 0;
    let intervalId = null;

    function goTo(i) {
        // normalizar i
        i = ((i % slides.length) + slides.length) % slides.length;

        // imágenes
        slides.forEach((s, idx) => s.classList.toggle('active', idx === i));
        // puntos
        dots.forEach((d, idx) => d.classList.toggle('active', idx === i));
        // texto (si existe la frase correspondiente)
        if (frases[i]) {
            tituloElem.textContent = frases[i].titulo;
            textoElem.textContent = frases[i].texto;
        }
        index = i;
    }

    function next() {
        goTo(index + 1);
    }

    // Iniciar en 0
    goTo(0);
    // autoplay cada 4s
    intervalId = setInterval(next, 4000);

    // Pausar al hover y reanudar al salir (opcional, pero útil)
    leftPanel.addEventListener('mouseenter', () => {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    });
    leftPanel.addEventListener('mouseleave', () => {
        if (!intervalId) intervalId = setInterval(next, 4000);
    });
});
