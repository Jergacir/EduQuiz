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

        // We'll wire the click handler later so it can call the onClose callback
        btn.addEventListener('click', function(){
            // call the shared close handler which will also invoke any onClose callback
            if (typeof window._rg_modal_closeHandler === 'function') window._rg_modal_closeHandler();
            else closeModal();
        });

        box.appendChild(h);
        box.appendChild(p);
        box.appendChild(btn);
        modal.appendChild(box);

    // cerrar al click en overlay (use shared close handler)
    modal.addEventListener('click', function(ev){ if (ev.target === modal) { if (typeof window._rg_modal_closeHandler === 'function') window._rg_modal_closeHandler(); else closeModal(); } });

        return modal;
    }

    window.showModal = function(title, message){
        let existing = document.getElementById('rg-modal');
        // options may be passed as third argument: { onClose: function }
        var options = arguments.length > 2 ? arguments[2] : null;
        if (existing) {
            const h = existing.querySelector('h3');
            const p = existing.querySelector('p');
            if (h) h.textContent = title;
            if (p) p.innerHTML = message.replace(/\n/g, '<br>');
            existing.classList.remove('rg-modal-hidden');
            // update callback
            if (options && typeof options.onClose === 'function') window._rg_modal_onclose = options.onClose;
            else window._rg_modal_onclose = null;
            return;
        }
        const modal = createModalElements(title, message);
        document.body.appendChild(modal);
        // store onClose callback (if provided) in a place the handlers can use
        if (options && typeof options.onClose === 'function') window._rg_modal_onclose = options.onClose;
        else window._rg_modal_onclose = null;
        // define a shared close handler that both button, overlay and Esc will call
        window._rg_modal_closeHandler = function(){
            closeModal();
            try{ if (typeof window._rg_modal_onclose === 'function') window._rg_modal_onclose(); }catch(e){ console.error('modal onClose error', e); }
        };
    };

    window.closeModal = function(){
        const m = document.getElementById('rg-modal');
        if (m && m.parentNode) m.parentNode.removeChild(m);
    };

    if (!window._rg_modal_keybound) {
        document.addEventListener('keydown', function(ev){ if (ev.key === 'Escape') { const m = document.getElementById('rg-modal'); if (m) { if (typeof window._rg_modal_closeHandler === 'function') window._rg_modal_closeHandler(); else closeModal(); } } });
        window._rg_modal_keybound = true;
    }
})();
