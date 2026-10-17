"""Force le navigateur à ne jamais mettre en cache les pages HTML.

Garantit que les liens ?v=... des fichiers CSS/JS sont toujours à jour :
sans cela, un navigateur gardant une ancienne page charge un ancien
main.js et les modales de formulaires ne s'ouvrent plus.
"""


class NoCacheHtmlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response
