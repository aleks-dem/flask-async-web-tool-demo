import contextvars
import threading
from collections import defaultdict


REQUEST_ID_CTX = contextvars.ContextVar('request_id', default='-')
USER_ID_CTX = contextvars.ContextVar('user_id', default='anonymous')

HTTP_DURATION_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
TASK_DURATION_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)


class MetricsRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(float)
        self._histograms = {}
        self._meta = {
            'app_http_requests_total': ('counter', 'Total HTTP requests by method, endpoint, and status.'),
            'app_http_request_duration_seconds': ('histogram', 'HTTP request duration in seconds.'),
            'app_celery_tasks_total': ('counter', 'Total Celery task executions by task and status.'),
            'app_celery_task_duration_seconds': ('histogram', 'Celery task duration in seconds.'),
        }

    @staticmethod
    def _labels_key(labels):
        return tuple(sorted((labels or {}).items()))

    def inc_counter(self, name, labels=None, value=1.0):
        with self._lock:
            self._counters[(name, self._labels_key(labels))] += float(value)

    def observe_histogram(self, name, value, labels=None, buckets=HTTP_DURATION_BUCKETS):
        value = float(value)
        labels_key = self._labels_key(labels)
        key = (name, labels_key)

        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = {
                    'buckets': tuple(sorted(buckets)),
                    'bucket_counts': defaultdict(float),
                    'count': 0.0,
                    'sum': 0.0,
                }

            histogram = self._histograms[key]
            histogram['count'] += 1.0
            histogram['sum'] += value

            for upper_bound in histogram['buckets']:
                if value <= upper_bound:
                    histogram['bucket_counts'][upper_bound] += 1.0
            histogram['bucket_counts']['+Inf'] += 1.0

    @staticmethod
    def _labels_to_str(labels_key, extra=None):
        pairs = list(labels_key)
        if extra:
            pairs.extend(extra)
        if not pairs:
            return ''

        def esc(raw):
            return str(raw).replace('\\', '\\\\').replace('"', '\\"')

        serialized = ','.join(f'{esc(k)}="{esc(v)}"' for k, v in pairs)
        return '{' + serialized + '}'

    def render_prometheus(self):
        lines = []

        for metric_name in sorted(self._meta.keys()):
            metric_type, metric_help = self._meta[metric_name]
            lines.append(f'# HELP {metric_name} {metric_help}')
            lines.append(f'# TYPE {metric_name} {metric_type}')

            if metric_type == 'counter':
                for (name, labels_key), value in sorted(self._counters.items()):
                    if name != metric_name:
                        continue
                    labels = self._labels_to_str(labels_key)
                    lines.append(f'{metric_name}{labels} {value}')
            else:
                for (name, labels_key), histogram in sorted(self._histograms.items()):
                    if name != metric_name:
                        continue
                    for upper_bound in histogram['buckets']:
                        labels = self._labels_to_str(labels_key, extra=[('le', upper_bound)])
                        value = histogram['bucket_counts'].get(upper_bound, 0.0)
                        lines.append(f'{metric_name}_bucket{labels} {value}')
                    inf_labels = self._labels_to_str(labels_key, extra=[('le', '+Inf')])
                    lines.append(
                        f'{metric_name}_bucket{inf_labels} {histogram["bucket_counts"].get("+Inf", 0.0)}'
                    )
                    base_labels = self._labels_to_str(labels_key)
                    lines.append(f'{metric_name}_count{base_labels} {histogram["count"]}')
                    lines.append(f'{metric_name}_sum{base_labels} {histogram["sum"]}')

        return '\n'.join(lines) + '\n'


METRICS = MetricsRegistry()


def set_request_context(request_id, user_id='anonymous'):
    token_request_id = REQUEST_ID_CTX.set(request_id or '-')
    token_user_id = USER_ID_CTX.set(user_id or 'anonymous')
    return token_request_id, token_user_id


def reset_request_context(tokens):
    if not tokens:
        return
    token_request_id, token_user_id = tokens
    try:
        REQUEST_ID_CTX.reset(token_request_id)
    except Exception:
        pass
    try:
        USER_ID_CTX.reset(token_user_id)
    except Exception:
        pass


def get_request_id():
    return REQUEST_ID_CTX.get()


def get_user_id():
    return USER_ID_CTX.get()


def observe_http_request(method, endpoint, status_code, duration_seconds):
    labels = {
        'method': method,
        'endpoint': endpoint,
        'status': status_code,
    }
    METRICS.inc_counter('app_http_requests_total', labels=labels)
    METRICS.observe_histogram(
        'app_http_request_duration_seconds',
        value=duration_seconds,
        labels={'method': method, 'endpoint': endpoint},
        buckets=HTTP_DURATION_BUCKETS,
    )


def observe_task(task_name, status, duration_seconds=None):
    labels = {'task': task_name, 'status': status}
    METRICS.inc_counter('app_celery_tasks_total', labels=labels)
    if duration_seconds is not None:
        METRICS.observe_histogram(
            'app_celery_task_duration_seconds',
            value=duration_seconds,
            labels=labels,
            buckets=TASK_DURATION_BUCKETS,
        )


def render_prometheus_metrics():
    return METRICS.render_prometheus()
