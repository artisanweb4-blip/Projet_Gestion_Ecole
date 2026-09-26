"""
Wrapper de compatibilité : exécute la commande de peuplement `seed_demo`.
(docker-compose appelle `python seed_data.py`)
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_config.settings')
django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    call_command('seed_demo')
