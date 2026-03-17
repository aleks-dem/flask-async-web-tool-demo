import json
import os
import time

import redis


PROCESS_LIFETIME = 3600


def get_redis_connection():
    """Initialize a Redis connection using environment configuration."""
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    return redis.from_url(redis_url)


def make_state_key(user_id, function_key):
    return f'process_state:{user_id}:{function_key}'


def set_process_state(user_id, function_key, state_dict):
    connection = get_redis_connection()
    key = make_state_key(user_id, function_key)
    if 'timestamp' not in state_dict:
        state_dict['timestamp'] = time.time()
    connection.set(key, json.dumps(state_dict), ex=PROCESS_LIFETIME)


def get_process_state(user_id, function_key):
    connection = get_redis_connection()
    key = make_state_key(user_id, function_key)
    data = connection.get(key)
    if data is None:
        return None
    return json.loads(data)


def delete_process_state(user_id, function_key):
    connection = get_redis_connection()
    key = make_state_key(user_id, function_key)
    connection.delete(key)


def cleanup_process_states_redis():
    connection = get_redis_connection()
    now = time.time()

    for key in connection.scan_iter(match='process_state:*'):
        data = connection.get(key)
        if not data:
            continue
        try:
            state = json.loads(data)
            if 'timestamp' in state and (now - state['timestamp']) > PROCESS_LIFETIME:
                connection.delete(key)
        except Exception:
            connection.delete(key)


def clear_in_progress_on_startup():
    """Remove stale states left from interrupted runs."""
    connection = get_redis_connection()
    for key in connection.scan_iter(match='process_state:*'):
        data = connection.get(key)
        if not data:
            continue
        try:
            state = json.loads(data)
            if state.get('status') in ['processing', 'in_progress', 'error']:
                connection.delete(key)
        except Exception:
            connection.delete(key)
