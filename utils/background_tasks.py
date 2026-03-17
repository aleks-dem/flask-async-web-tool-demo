import os
import time

from apscheduler.schedulers.background import BackgroundScheduler

from utils.redis_state_repository import cleanup_process_states_redis
from . import globals as g


TEMP_FILE_LIFETIME = 3600
PROCESS_LIFETIME = 3600

scheduler = BackgroundScheduler()


def clean_temp_folder(app):
    with app.app_context():
        if not os.path.exists(g.temp_dir):
            return

        now = time.time()
        for filename in os.listdir(g.temp_dir):
            file_path = os.path.join(g.temp_dir, filename)
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > TEMP_FILE_LIFETIME:
                    try:
                        os.remove(file_path)
                        app.logger.info(f'[clean_temp_folder] Deleted old temp file: {file_path}')
                    except Exception as exc:
                        app.logger.error(f'[clean_temp_folder] Error deleting file {file_path}: {exc}')


def cleanup_process_states(app):
    with app.app_context():
        app.logger.info('[cleanup_process_states] Start cleaning process_states...')
        cleanup_process_states_redis()
        app.logger.info('[cleanup_process_states] Done.')


def init_scheduler(app):
    if not scheduler.running:
        scheduler.add_job(func=clean_temp_folder, trigger='interval', minutes=60, args=[app])
        scheduler.add_job(func=cleanup_process_states, trigger='interval', minutes=60, args=[app])
        scheduler.start()
        app.logger.info('[init_scheduler] APScheduler started')
