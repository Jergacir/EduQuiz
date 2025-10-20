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
});
