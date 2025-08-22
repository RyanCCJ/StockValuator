import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# The Redis URL for Celery. Defaults to the service name in docker-compose.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    __name__,
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Autodiscover tasks from a 'tasks.py' file in apps that are part of INSTALLED_APPS
celery.autodiscover_tasks(['app.tasks'])
