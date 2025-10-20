document.addEventListener("DOMContentLoaded", () => {
    animarTarjetas();
    configurarExportacion();
});

// ====================== ANIMACIONES ======================
function animarTarjetas() {
    const analisis = document.querySelectorAll(".analysis-card");
    const ranking = document.querySelectorAll(".ranking-item");

    analisis.forEach((card, i) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";
        setTimeout(() => {
            card.style.transition = "all 0.6s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, i * 150);
    });

    ranking.forEach((item, i) => {
        item.style.opacity = "0";
        item.style.transform = "translateX(-20px)";
        setTimeout(() => {
            item.style.transition = "all 0.5s ease";
            item.style.opacity = "1";
            item.style.transform = "translateX(0)";
        }, i * 100 + 500);
    });
}

// ====================== EXPORTACIÓN ======================
function configurarExportacion() {
    const btn = document.querySelector(".exportar-btn");
    if (!btn) return;

    btn.addEventListener("click", () => {
        setTimeout(() => {
            mostrarToast("✅ Exportando resultados...");
        }, 300);
    });
}

// ====================== TOAST ======================
function mostrarToast(msg) {
    const toast = document.createElement("div");
    toast.classList.add("eduquiz-toast");
    toast.innerText = msg;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add("visible"), 100);
    setTimeout(() => {
        toast.classList.remove("visible");
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}
