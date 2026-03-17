import logging
import os
import json
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from utils.observability import get_request_id, get_user_id


class JsonFormatter(logging.Formatter):
    """Emit structured JSON logs for easier ingestion and filtering."""

    EXTRA_FIELDS = (
        'event',
        'path',
        'method',
        'endpoint',
        'status_code',
        'duration_ms',
        'function_key',
        'task_id',
    )

    def format(self, record):
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'message': record.getMessage(),
            'request_id': get_request_id(),
            'user_id': get_user_id(),
        }

        for field in self.EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_root_logger():
    """Configure root logger with a rotating file handler."""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    formatter = JsonFormatter()

    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1_000_000, backupCount=30)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if not any(isinstance(handler, RotatingFileHandler) for handler in root_logger.handlers):
        root_logger.addHandler(file_handler)

    if not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, RotatingFileHandler)
        for handler in root_logger.handlers
    ):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    root_logger.setLevel(logging.INFO)
    return root_logger
