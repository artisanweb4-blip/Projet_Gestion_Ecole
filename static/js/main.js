/* Gestion d'École — scripts globaux */
(function () {
    'use strict';

    // --- Sidebar (mobile) ---------------------------------------------------
    var toggle = document.getElementById('sidebarToggle');
    var overlay = document.getElementById('sidebarOverlay');
    if (toggle) {
        toggle.addEventListener('click', function () {
            document.body.classList.toggle('sidebar-open');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', function () {
            document.body.classList.remove('sidebar-open');
        });
    }

    // --- Fermeture des alertes ----------------------------------------------
    document.addEventListener('click', function (e) {
        if (e.target.classList && e.target.classList.contains('alert-close')) {
            var alert = e.target.closest('.alert');
            if (alert) { alert.remove(); }
        }
    });

    // --- Disparition automatique des alertes (3 s) ---------------------------
    setTimeout(function () {
        document.querySelectorAll('.alert-dismiss').forEach(function (el) {
            el.style.transition = 'opacity 0.3s ease';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 300);
        });
    }, 3000);

    // --- Confirmation avant suppression (formulaires non-modaux) -------------
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (form.matches('[data-confirm]')) {
            if (!window.confirm(form.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        }
    });

    // --- Recherche client-side sur les tableaux (input#searchInput) ----------
    var search = document.getElementById('searchInput');
    if (search) {
        search.addEventListener('keyup', function () {
            var term = search.value.toLowerCase();
            document.querySelectorAll('tbody tr').forEach(function (row) {
                var text = row.textContent.toLowerCase();
                row.style.display = text.indexOf(term) !== -1 ? '' : 'none';
            });
        });
    }

    // =========================================================================
    // MODALE GLOBALE (formulaires ajout / modification / suppression via HTMX)
    // =========================================================================
    var modalOverlay = document.getElementById('modalOverlay');
    var modalBody = document.getElementById('modal-body');

    function openModal() {
        if (!modalOverlay) return;
        modalOverlay.classList.add('show');
        modalOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        if (!modalOverlay) return;
        modalOverlay.classList.remove('show');
        modalOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        if (modalBody) { modalBody.innerHTML = ''; }
    }

    // Expose pour d'autres scripts
    window.gceOpenModal = openModal;
    window.gceCloseModal = closeModal;

    // Clic sur l'arrière-plan / bouton de fermeture / touche Échap
    document.addEventListener('click', function (e) {
        if (e.target === modalOverlay) { closeModal(); }
        if (e.target.closest('[data-close-modal]')) { closeModal(); }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('show')) {
            closeModal();
        }
    });

    // Dès que HTMX injecte du contenu dans la modale → on l'ouvre
    document.body.addEventListener('htmx:afterSwap', function (e) {
        if (modalBody && e.target.id === 'modal-body') { openModal(); }
    });

    // Erreur serveur pendant une requête de modale → message dans la modale
    document.body.addEventListener('htmx:responseError', function (e) {
        if (modalBody && e.target && e.target.closest && e.target.closest('.modal-box')) {
            modalBody.innerHTML =
                '<div class="modal-head"><h3>Erreur</h3>' +
                '<button type="button" class="modal-close" data-close-modal>&times;</button></div>' +
                '<div class="alert alert-error"><i class="fa-solid fa-circle-exclamation"></i>' +
                '<span>Une erreur est survenue. Merci de réessayer.</span></div>';
            openModal();
        }
    });

    // Ferme la modale automatiquement quand le serveur demande une redirection
    document.body.addEventListener('htmx:beforeHistorySave', closeModal);
})();
