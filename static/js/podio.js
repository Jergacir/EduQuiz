document.addEventListener('DOMContentLoaded', () => {
	const body = document.body;
	const codigoPartida = body.dataset.codigoPartida || null;
	const esProfesor = body.dataset.esProfesor === 'true';

	const continueBtn = document.getElementById('continueBtn');
	if (!continueBtn) return;

	continueBtn.addEventListener('click', async () => {
		continueBtn.disabled = true;
		continueBtn.textContent = 'Procesando...';

		try {
			if (esProfesor) {
				// Obtener partida_id desde el servidor para redirigir a resultados_partida/<id>
				if (!codigoPartida) throw new Error('Falta codigo de partida');

				const resp = await fetch(`/api/partida/${codigoPartida}/info`);
				if (!resp.ok) throw new Error('No se pudo obtener info de la partida');
				const data = await resp.json();
				if (!data.success || !data.partida) throw new Error('Respuesta inválida del servidor');

				const partidaId = data.partida.partida_id;
				if (!partidaId) throw new Error('No se obtuvo partida_id');

				// Redirigir a resultados del profesor
				window.location.href = `/resultados_partida/${partidaId}`;

			} else {
				// Alumnos vuelven al listado de partidas
				window.location.href = `/partidas`;
			}
		} catch (err) {
			console.error('Error en acción continuar podio:', err);
			// Restaurar botón
			continueBtn.disabled = false;
			continueBtn.textContent = 'Continuar';
			alert('Error al procesar la acción. Intenta de nuevo.');
		}
	});
});
