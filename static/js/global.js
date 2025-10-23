// Global UI behaviors: sidebar toggle and overlay handling
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const menuButton = document.getElementById('menu-button');
  const sidebarOverlay = document.getElementById('sidebar-overlay');

  if (!menuButton || !sidebar || !sidebarOverlay) return;

  menuButton.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('visible');
  });

  sidebarOverlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('visible');
  });

  // Perfil: abrir menú contextual
  const profileBox = document.getElementById('profile-box');
  const profileMenu = document.getElementById('profile-menu');
  if (profileBox && profileMenu) {
    profileBox.addEventListener('click', (e) => {
      // Si el click fue en un enlace dentro del menú, permitir la navegación
      const anchor = e.target.closest('a');
      if (anchor && profileMenu.contains(anchor)) {
        // Cerrar el menú (no impedir la navegación)
        profileMenu.classList.remove('visible');
        profileMenu.setAttribute('aria-hidden', 'true');
        return;
      }

      // Si el click es sobre el propio profileBox (no sobre un link del menú), togglear el menú
      e.stopPropagation();
      profileMenu.classList.toggle('visible');
      const isVisible = profileMenu.classList.contains('visible');
      profileMenu.setAttribute('aria-hidden', (!isVisible).toString());
    });

    // Click fuera para cerrar
    document.addEventListener('click', (ev) => {
      if (!profileBox.contains(ev.target)) {
        profileMenu.classList.remove('visible');
        profileMenu.setAttribute('aria-hidden', 'true');
      }
    });

    // ESC para cerrar
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') {
        profileMenu.classList.remove('visible');
        profileMenu.setAttribute('aria-hidden', 'true');
      }
    });
  }

  // --- Modal de confirmación global para logout ---
  // Crear modal si no existe
  let confirmLogoutModal = document.getElementById('confirm-logout-modal');
  if (!confirmLogoutModal) {
    confirmLogoutModal = document.createElement('div');
    confirmLogoutModal.id = 'confirm-logout-modal';
    confirmLogoutModal.className = 'confirm-logout-modal';
    confirmLogoutModal.innerHTML = `
      <div class="modal-backdrop"></div>
      <div class="confirm-card" role="dialog" aria-modal="true">
        <div class="confirm-header">
          <h3>¿Cerrar sesión?</h3>
          <button class="modal-close" aria-label="Cerrar">&times;</button>
        </div>
        <div class="confirm-body">¿Estás seguro que deseas cerrar sesión en tu cuenta?</div>
        <div class="confirm-actions">
          <button class="btn-cancel">Cancelar</button>
          <button class="btn-confirm">Cerrar sesión</button>
        </div>
      </div>
    `;
    document.body.appendChild(confirmLogoutModal);
  }

  const modalBackdrop = confirmLogoutModal.querySelector('.modal-backdrop');
  const btnCancel = confirmLogoutModal.querySelector('.btn-cancel');
  const btnConfirm = confirmLogoutModal.querySelector('.btn-confirm');
  const modalClose = confirmLogoutModal.querySelector('.modal-close');

  let pendingLogoutHref = null;

  function openConfirmLogout(href) {
    pendingLogoutHref = href;
    confirmLogoutModal.classList.add('visible');
  }

  function closeConfirmLogout() {
    pendingLogoutHref = null;
    confirmLogoutModal.classList.remove('visible');
  }

  // Interceptar todos los enlaces que cierran sesión
  function handleLogoutClick(e) {
    const link = e.currentTarget;
    const href = link.getAttribute('href');
    if (!href) return;
    e.preventDefault();
    openConfirmLogout(href);
  }

  // Seleccionar varios posibles selectores de logout en la app
  const logoutSelectors = Array.from(document.querySelectorAll('a[href*="logout"], a.logout-btn, #logout-button, a.profile-menu-item'));
  logoutSelectors.forEach(el => {
    // evitamos duplicar listeners
    el.removeEventListener('click', handleLogoutClick);
    el.addEventListener('click', function(e) {
      // Si el enlace es de perfil pero no tiene logout en href, ignorar
      const href = el.getAttribute('href') || '';
      if (href.includes('logout')) {
        handleLogoutClick.call(el, e);
      }
    });
  });

  // Acciones del modal
  modalBackdrop.addEventListener('click', closeConfirmLogout);
  btnCancel.addEventListener('click', closeConfirmLogout);
  modalClose.addEventListener('click', closeConfirmLogout);
  btnConfirm.addEventListener('click', () => {
    if (pendingLogoutHref) {
      // navegar a href
      window.location.href = pendingLogoutHref;
    } else {
      closeConfirmLogout();
    }
  });

  // ESC para cerrar modal de logout (agregar al listener ya existente)
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      closeConfirmLogout();
    }
  });
});
