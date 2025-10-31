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




        // Aquí puedes iterar y añadir al cuestionario
        data.preguntas.forEach(p => {
            window.cuestionario.preguntas.push(p); // tu array de preguntas ya existe
        });
        console.log("Preguntas importadas:", data.preguntas);

        // Agregar preguntas al cuestionario usando la función pública
        if (window.agregarPreguntasExcel) {
            window.agregarPreguntasExcel(data.preguntas);
        } else {
            console.error("No se encontró la función agregarPreguntasExcel");
        }
         alert("Excel procesado correctamente.");


    } catch (err) {
        console.error("Error al subir o procesar el Excel:", err);
        alert("Error al subir o procesar el Excel");
    }finally{
        excelInput.value = '';
        excelFileName.textContent = 'Ningún archivo seleccionado';
    }
});

// Función para leer Excel usando SheetJS
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

document.getElementById("btnDownloadTemplate").addEventListener("click", () => {
    // Cabeceras de la plantilla
    const wsData = [
        ["Pregunta", "RespuestaCorrecta", "Respuesta1", "Respuesta2", "Respuesta3"],
    ];

    // Crear libro y hoja
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    XLSX.utils.book_append_sheet(wb, ws, "Plantilla");

    // Descargar
    XLSX.writeFile(wb, "Plantilla_Cuestionario.xlsx");
});