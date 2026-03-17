import os
import time
import uuid

from flask import Flask, request, redirect, url_for, session, jsonify, flash, Response, g as flask_g
from flask_babel import Babel, gettext
from flask_login import LoginManager, current_user, login_required
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv

from admin.routes import admin_bp
from auth.routes import auth_bp
from app_functions.document_builder import document_builder_bp
from app_functions.transaction_lookup import transaction_lookup_bp

from utils.background_tasks import init_scheduler
from utils.users_repository import load_user_by_id
from utils.redis_state_repository import clear_in_progress_on_startup
from utils.logging_config import setup_root_logger
from utils.observability import (
    set_request_context,
    reset_request_context,
    observe_http_request,
    render_prometheus_metrics,
)
import utils.globals as g


load_dotenv()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'demo-secret-key-change-me')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ru']
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600

    Session(app)
    csrf.init_app(app)
    setup_root_logger()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'
 
    @login_manager.user_loader
    def load_user(user_id):
        return load_user_by_id(user_id)

    babel = Babel()

    def get_locale():
        return session.get('lang', 'en')

    babel.init_app(app, locale_selector=get_locale)

    os.makedirs(g.temp_dir, exist_ok=True)

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_builder_bp)
    app.register_blueprint(transaction_lookup_bp)

    init_scheduler(app)
    clear_in_progress_on_startup()

    @app.before_request
    def before_request_observability():
        flask_g.request_started_at = time.perf_counter()
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        user_id = current_user.get_id() if current_user.is_authenticated else 'anonymous'
        flask_g.request_id = request_id
        flask_g.ctx_tokens = set_request_context(request_id=request_id, user_id=user_id)

    @app.after_request
    def after_request_observability(response):
        started_at = getattr(flask_g, 'request_started_at', None)
        duration_seconds = max(0.0, time.perf_counter() - started_at) if started_at else 0.0
        endpoint = request.endpoint or request.path
        observe_http_request(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        response.headers['X-Request-ID'] = getattr(flask_g, 'request_id', '-')

        app.logger.info(
            'http_request',
            extra={
                'event': 'http_request',
                'method': request.method,
                'path': request.path,
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration_ms': round(duration_seconds * 1000, 2),
            },
        )

        tokens = getattr(flask_g, 'ctx_tokens', None)
        if tokens:
            reset_request_context(tokens)
            flask_g.ctx_tokens = None
        return response

    @app.teardown_request
    def teardown_observability(_error):
        tokens = getattr(flask_g, 'ctx_tokens', None)
        if tokens:
            reset_request_context(tokens)
            flask_g.ctx_tokens = None

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        message = gettext('CSRF token is missing or invalid. Refresh the page and try again.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'error': message}), 400
        flash(message, 'danger')
        return redirect(request.referrer or url_for('auth_bp.login'))

    @app.context_processor
    def inject_title():
        endpoint = request.endpoint or ''
        parts = endpoint.split('.') if endpoint else []
        root_endpoint = parts[0].removesuffix('_bp') if parts else ''
        sub_endpoint = '.'.join(parts[:2]) if len(parts) > 1 else root_endpoint

        title = gettext('Dashboard')

        if root_endpoint == 'auth':
            if parts and parts[-1] == 'login':
                title = gettext('Login')
            elif parts and parts[-1] == 'logout':
                title = gettext('Logout')
        elif root_endpoint == 'admin':
            if len(parts) > 1 and parts[1] == 'create_user':
                title = gettext('Create user')
            elif len(parts) > 1 and parts[1] == 'edit_user':
                title = gettext('Edit user')
            else:
                title = gettext('Admin panel')
        elif root_endpoint == 'home':
            title = gettext('Analytics Toolkit Demo')
        elif root_endpoint in g.function_details:
            title = gettext(g.function_details[root_endpoint]['name'])
        elif sub_endpoint in g.function_details:
            title = gettext(g.function_details[sub_endpoint]['name'])

        return {'title': title}

    @app.context_processor
    def inject_user_functions():
        if current_user.is_authenticated:
            if current_user.is_admin:
                all_functions = []
                for _, function_data in g.function_details.items():
                    all_functions.append(
                        {
                            'name': function_data['name'],
                            'description': function_data['description'],
                            'endpoint': function_data['endpoint'],
                        }
                    )
                return {'user_functions': all_functions}

            user_functions = []
            for function_key in current_user.functions:
                if function_key in g.function_details:
                    user_functions.append(
                        {
                            'name': g.function_details[function_key]['name'],
                            'description': g.function_details[function_key]['description'],
                            'endpoint': g.function_details[function_key]['endpoint'],
                        }
                    )
            return {'user_functions': user_functions}

        return {'user_functions': []}

    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('auth_bp.dashboard'))
        return redirect(url_for('auth_bp.login'))

    @app.route('/metrics')
    @login_required
    def metrics():
        if not current_user.is_admin:
            return jsonify({'error': gettext('Forbidden')}), 403
        return Response(
            render_prometheus_metrics(),
            mimetype='text/plain; version=0.0.4; charset=utf-8',
        )

    return app
