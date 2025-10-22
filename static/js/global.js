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
});
