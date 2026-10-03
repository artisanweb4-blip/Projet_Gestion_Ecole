"""Enregistre une visite par (visiteur, jour, page) — sans nuire aux performances."""
from django.utils import timezone

from .models import VisitLog

EXCLUDED_PREFIXES = (
    '/static/', '/media/', '/admin/', '/api/', '/favicon',
    '/robots.txt', '/sitemap.xml', '/maintenance/',
)


class VisitTrackingMiddleware:
    """Trace les consultations (1 ligne max par visiteur/jour/page).

    Volontairement silencieux : jamais d'erreur renvoyée à l'utilisateur.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._track(request)
        except Exception:
            pass
        return response

    def _track(self, request):
        if request.method != 'GET':
            return
        path = request.path
        for prefix in EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return
        if getattr(request, 'htmx', None) and request.htmx:
            return  # fragments : déjà comptés à la page complète

        user = getattr(request, 'user', None)
        session_key = getattr(getattr(request, 'session', None), 'session_key', None) or ''
        if (user is None or not user.is_authenticated) and not session_key:
            return

        from django.utils import timezone
        VisitLog.objects.get_or_create(
            user=user if (user and user.is_authenticated) else None,
            session_key='' if (user and user.is_authenticated) else session_key,
            day=timezone.localdate(),
            path=path[:200],
            defaults={
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': (request.META.get('HTTP_USER_AGENT') or '')[:250],
            },
        )
