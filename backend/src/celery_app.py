import os

from celery import Celery

def get_celery_app():
    # Celery configuration using environment variables
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND_URL', 'redis://localhost:6379/0')

    app = Celery(
        'dev_storyteller',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
        include=['src.services.analysis_service'] # Include tasks from analysis_service
    )

    app.conf.update(
        task_track_started=True,
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
    )
    return app

celery_app = get_celery_app()
