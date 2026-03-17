import os
from celery import Celery

from utils.logging_config import setup_root_logger


setup_root_logger()


def make_celery(app=None):
    """Create and configure a Celery instance."""
    default_redis_host = 'redis'
    default_redis_port = '6379'
    default_redis_db = '0'

    redis_url = f'redis://{default_redis_host}:{default_redis_port}/{default_redis_db}'

    broker_url = os.environ.get('CELERY_BROKER_URL', redis_url)
    backend_url = os.environ.get('CELERY_RESULT_BACKEND', redis_url)

    celery = Celery(
        app.import_name if app else __name__,
        broker=broker_url,
        backend=backend_url,
        include=[
            'services.document_builder_task',
            'services.transaction_lookup_task',
        ],
    )

    if app:
        celery.conf.update(app.config)

    celery.conf.update(
        worker_hijack_root_logger=False,
        broker_connection_retry_on_startup=True,
    )

    return celery


celery = make_celery()
