// ======================================================
// SCRIPT PARA RESULTADOS DE PARTIDA (EDUQUIZ)
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    animarEstadisticas();
    configurarExportacionCSV();
});

// ======================================================
// 🟢 ANIMACIÓN DE ENTRADA DE LAS TARJETAS DE ESTADÍSTICAS
// ======================================================

function animarEstadisticas() {
    const cards = document.querySelectorAll(".analysis-card");

    cards.forEach((card, index) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";

        setTimeout(() => {
            card.style.transition = "all 0.6s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, 200 * index); // animación escalonada
    });
}

// ======================================================
// 💾 EXPORTAR RESULTADOS DE LA TABLA A CSV
// ======================================================

function configurarExportacionCSV() {
    const btnExportar = document.querySelector(".btn-primary");
    if (btnExportar) {
        btnExportar.addEventListener("click", exportarResultadosCSV);
    }
}

function exportarResultadosCSV() {
    const tabla = document.querySelector(".ranking-table");
    if (!tabla) {
        alert("No se encontró la tabla de resultados.");
        return;
    }

    let csvContent = "";
    const filas = tabla.querySelectorAll("tr");

    filas.forEach((fila) => {
        const columnas = fila.querySelectorAll("th, td");
        const filaCSV = Array.from(columnas)
            .map((col) => `"${col.innerText.replace(/"/g, '""')}"`)
            .join(",");
        csvContent += filaCSV + "\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    const partidaId = document.body.getAttribute("data-partida-id") || "partida";
    link.setAttribute("href", url);
    link.setAttribute("download", `resultados_${partidaId}.csv`);
    link.style.display = "none";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    mostrarNotificacion("✅ Resultados exportados correctamente");
}

// ======================================================
// ✨ FUNCIÓN DE NOTIFICACIÓN VISUAL (LIGERA Y BONITA)
// ======================================================

function mostrarNotificacion(mensaje) {
    const notif = document.createElement("div");
    notif.classList.add("eduquiz-toast");
    notif.innerText = mensaje;

    document.body.appendChild(notif);

    setTimeout(() => {
        notif.classList.add("visible");
    }, 100);

    setTimeout(() => {
        notif.classList.remove("visible");
        setTimeout(() => notif.remove(), 400);
    }, 3000);
}

// ======================================================
// 🎨 ESTILOS INLINE PARA EL TOAST (NO REQUIERE CSS EXTRA)
// ======================================================

const estiloToast = document.createElement("style");
estiloToast.innerHTML = `
.eduquiz-toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: #2D3047;
    color: #fff;
    padding: 12px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.4s ease;
    font-weight: 600;
    z-index: 9999;
}

.eduquiz-toast.visible {
    opacity: 1;
    transform: translateY(0);
}
`;
document.head.appendChild(estiloToast);
