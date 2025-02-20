import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Пример конфигурации: используем URL Redis, заданный в .env
app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
