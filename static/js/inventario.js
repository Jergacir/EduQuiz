// JS para tabs de inventario (accesorios/skins)
document.addEventListener('DOMContentLoaded', function() {
    const tabAccesorios = document.getElementById('tab-accesorios');
    const tabSkins = document.getElementById('tab-skins');
    const accesoriosSection = document.getElementById('accesorios-section');
    const skinsSection = document.getElementById('skins-section');
    if (tabAccesorios && tabSkins && accesoriosSection && skinsSection) {
        tabAccesorios.addEventListener('click', function() {
            tabAccesorios.classList.add('active');
            tabSkins.classList.remove('active');
            accesoriosSection.style.display = '';
            skinsSection.style.display = 'none';
            tabAccesorios.style.background = '#0d9488';
            tabSkins.style.background = '#fff';
        });
        tabSkins.addEventListener('click', function() {
            tabSkins.classList.add('active');
            tabAccesorios.classList.remove('active');
            accesoriosSection.style.display = 'none';
            skinsSection.style.display = '';
            tabSkins.style.background = '#0d9488';
            tabAccesorios.style.background = '#fff';
        });
    }
});
