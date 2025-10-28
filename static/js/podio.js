document.addEventListener('DOMContentLoaded', () => {
	const body = document.body;
	const codigoPartida = body.dataset.codigoPartida || null;
	const esProfesor = body.dataset.esProfesor === 'true';

	const continueBtn = document.getElementById('continueBtn');
	// Confetti helper using canvas-confetti (loaded via CDN in template)
	function shouldShowConfetti() {
		return !!document.querySelector('.podium-item.first');
	}

	function launchConfettiFor(duration = 8000) {
		if (typeof confetti !== 'function') {
			console.warn('canvas-confetti no está disponible');
			return;
		}

		const end = Date.now() + duration;
		const colors = ['#ff595e', '#ffca3a', '#8ac926', '#1982c4', '#6a4c93', '#ff7ab6'];

		const timer = setInterval(() => {
			const timeLeft = end - Date.now();
			if (timeLeft <= 0) {
				clearInterval(timer);
				return;
			}

			// ráfaga aleatoria
			confetti({
				particleCount: 20 + Math.floor(Math.random() * 30),
				spread: 60 + Math.random() * 20,
				startVelocity: 30,
				origin: { x: Math.random(), y: Math.random() * 0.4 },
				colors: colors
			});
		}, 250);
	}

	if (shouldShowConfetti()) {
		// lanzar confeti en ráfagas durante 8s
		setTimeout(() => launchConfettiFor(8000), 200);
	}

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
