(function(){
    if (window.showModal) return; // no sobrescribir si ya existe

    function createModalElements(title, message) {
        const modal = document.createElement('div');
        modal.id = 'rg-modal';
        modal.classList.add('rg-modal-overlay');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');

        const box = document.createElement('div');
        box.classList.add('rg-modal-box');

        const h = document.createElement('h3');
        h.textContent = title;

        const p = document.createElement('p');
        p.innerHTML = message.replace(/\n/g, '<br>');

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = 'Aceptar';
        btn.classList.add('rg-modal-accept');

        btn.addEventListener('click', function(){
            closeModal();
        });

        box.appendChild(h);
        box.appendChild(p);
        box.appendChild(btn);
        modal.appendChild(box);

        // cerrar al click en overlay
        modal.addEventListener('click', function(ev){ if (ev.target === modal) closeModal(); });

        return modal;
    }

    window.showModal = function(title, message){
        let existing = document.getElementById('rg-modal');
        if (existing) {
            const h = existing.querySelector('h3');
            const p = existing.querySelector('p');
            if (h) h.textContent = title;
            if (p) p.innerHTML = message.replace(/\n/g, '<br>');
            existing.classList.remove('rg-modal-hidden');
            return;
        }
        const modal = createModalElements(title, message);
        document.body.appendChild(modal);
    };

    window.closeModal = function(){
        const m = document.getElementById('rg-modal');
        if (m && m.parentNode) m.parentNode.removeChild(m);
    };

    if (!window._rg_modal_keybound) {
        document.addEventListener('keydown', function(ev){ if (ev.key === 'Escape') { const m = document.getElementById('rg-modal'); if (m) closeModal(); } });
        window._rg_modal_keybound = true;
    }
})();
