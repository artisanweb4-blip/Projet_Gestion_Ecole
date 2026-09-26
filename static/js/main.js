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

    // --- Disparition automatique des alertes (6 s) ---------------------------
    setTimeout(function () {
        document.querySelectorAll('.alert-dismiss').forEach(function (el) {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 500);
        });
    }, 6000);

    // --- Confirmation avant suppression --------------------------------------
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
})();
