// Referencias a elementos
const excelInput = document.getElementById('excelInput');
const btnUploadExcel = document.getElementById('btnUploadExcel');
const excelFileName = document.getElementById('excelFileName');
const questionListSidebar = document.querySelector('.question-list-sidebar');

btnUploadExcel.addEventListener('click', () => {
    excelInput.click();
});

excelInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowedExtensions = ['xlsx', 'xls'];
    const fileExt = file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExt)) {
        alert('Solo se permiten archivos Excel (.xlsx, .xls)');
        excelInput.value = '';
        excelFileName.textContent = 'Ningún archivo seleccionado';
        return;
    }

    excelFileName.textContent = file.name;

    // Enviar al backend
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/subir_excel', {
            method: 'POST',
            body: formData
        });

        let data;
        try {
            data = await resp.json();
        } catch (jsonErr) {
            console.error("No se pudo parsear JSON:", jsonErr);
            alert("Error al procesar la respuesta del servidor.");
            return;
        }

        if (!resp.ok) {
            console.error("Error del servidor:", data);
            alert(data.error || "Error al subir o procesar el Excel");
            return;
        }

        console.log("Preguntas importadas desde Excel:", data.preguntas);

        // Verificar que las preguntas tengan el campo tiempo
        data.preguntas.forEach((p, idx) => {
            console.log(`Pregunta ${idx + 1}: tiempo=${p.tiempo}, tiempo_limite=${p.tiempo_limite}`);
        });

        // Agregar preguntas al cuestionario usando la función pública
        if (window.agregarPreguntasExcel) {
            window.agregarPreguntasExcel(data.preguntas);
            alert(`✅ Se importaron ${data.preguntas.length} preguntas correctamente con sus tiempos personalizados.`);
        } else {
            console.error("No se encontró la función agregarPreguntasExcel");
            alert("Error al cargar las preguntas en el editor");
        }

    } catch (err) {
        console.error("Error al subir o procesar el Excel:", err);
        alert("Error al subir o procesar el Excel");
    } finally {
        excelInput.value = '';
        excelFileName.textContent = 'Ningún archivo seleccionado';
    }
});

// Función para leer Excel usando SheetJS (no se usa actualmente, procesamiento en backend)
function readExcel(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(sheet, { defval: '' });
            resolve(jsonData);
        };
        reader.onerror = (err) => reject(err);
        reader.readAsArrayBuffer(file);
    });
}

// Descargar plantilla de Excel con columna TiempoPregunta (EN BLANCO)
document.getElementById("btnDownloadTemplate").addEventListener("click", () => {
    // ✅ Plantilla en blanco sin datos de ejemplo
    const wsData = [
        ["Pregunta", "RespuestaCorrecta", "Respuesta1", "Respuesta2", "Respuesta3", "TiempoPregunta"],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""]
    ];

    // Crear libro y hoja
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    
    // Ajustar ancho de columnas para mejor legibilidad
    ws['!cols'] = [
        { wch: 40 }, // Pregunta
        { wch: 20 }, // RespuestaCorrecta
        { wch: 20 }, // Respuesta1
        { wch: 20 }, // Respuesta2
        { wch: 20 }, // Respuesta3
        { wch: 15 }  // TiempoPregunta
    ];
    
    XLSX.utils.book_append_sheet(wb, ws, "Plantilla");

    // Descargar
    XLSX.writeFile(wb, "Plantilla_Cuestionario.xlsx");
});