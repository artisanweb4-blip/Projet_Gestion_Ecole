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

    // Si la requête de modale échoue (erreur réseau/serveur) → formulaire
    // en pleine page : les formulaires restent TOUJOURS accessibles.
    function modalFallback(e) {
        var elt = e.detail.elt;
        if (elt && elt.getAttribute &&
            elt.getAttribute('hx-target') === '#modal-body' &&
            elt.getAttribute('hx-get')) {
            window.location.href = elt.getAttribute('hx-get');
        }
    }
    document.body.addEventListener('htmx:sendError', modalFallback);
    document.body.addEventListener('htmx:responseError', modalFallback);

    // Ferme la modale automatiquement quand le serveur demande une redirection
    document.body.addEventListener('htmx:beforeHistorySave', closeModal);
})();

// =========================================================================
// NAVIGATION BOOSTÉE : barre de progression + lien actif du menu
// =========================================================================
(function () {
    'use strict';

    var loader = document.getElementById('pageLoader');

    // Barre de progression pendant les navigations HTMX
    document.body.addEventListener('htmx:beforeRequest', function (e) {
        var elt = e.detail.elt;
        // Uniquement pour les navigations de page (pas les modales)
        if (elt && elt.closest && elt.closest('#page-area') &&
            !(elt.hasAttribute && elt.hasAttribute('hx-target'))) {
            if (loader) { loader.classList.add('active'); }
        }
    });
    document.body.addEventListener('htmx:afterRequest', function () {
        if (loader) {
            loader.classList.add('done');
            setTimeout(function () {
                loader.classList.remove('active', 'done');
            }, 300);
        }
    });

    // Met à jour le lien actif du menu après chaque navigation boostée
    function updateActiveMenu() {
        var path = window.location.pathname;
        var links = Array.prototype.slice.call(
            document.querySelectorAll('.menu-link')
        );
        // Correspondance exacte ou préfixe propre ; le lien le plus
        // spécifique (préfixe le plus long) gagne.
        var best = null;
        links.forEach(function (link) {
            var href = link.getAttribute('href');
            var match = href && href !== '/' && path.indexOf(href) === 0;
            if (match && (best === null || href.length > best.length)) {
                best = href;
            }
        });
        links.forEach(function (link) {
            var href = link.getAttribute('href');
            link.classList.toggle('active', href !== null && href === best);
        });
    }

    document.body.addEventListener('htmx:afterSwap', updateActiveMenu);
    document.body.addEventListener('htmx:pushedIntoHistory', updateActiveMenu);
    window.addEventListener('popstate', function () { setTimeout(updateActiveMenu, 50); });
})();
