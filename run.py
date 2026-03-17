import os

from app import create_app


app = create_app()


def as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=as_bool(os.environ.get('FLASK_DEBUG'), False))
