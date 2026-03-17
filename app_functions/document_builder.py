import os
import time
from io import BytesIO

from flask import (
    render_template,
    request,
    jsonify,
    url_for,
    flash,
    send_file,
    after_this_request,
    abort,
)
from flask_login import login_required, current_user
from flask_babel import gettext
from flask import current_app as app
from werkzeug.utils import safe_join

from . import document_builder_bp
import utils.globals as g
from utils.redis_state_repository import (
    set_process_state,
    get_process_state,
    delete_process_state,
)
from services.document_builder_task import build_document_process


@document_builder_bp.route('/build', methods=['GET', 'POST'])
@login_required
def build_document():
    if not (current_user.is_admin or 'document_builder' in current_user.functions):
        abort(403)

    templates_path = os.path.join('data', 'templates')
    os.makedirs(templates_path, exist_ok=True)

    available_templates = [
        os.path.splitext(filename)[0]
        for filename in os.listdir(templates_path)
        if filename.endswith('.docx')
    ]
    if not available_templates:
        available_templates = ['demo_template']

    function_key = 'document_builder'

    if request.method == 'GET':
        state = get_process_state(current_user.id, function_key)
        is_processing = bool(state and state.get('status') in ['processing', 'in_progress'])
        percentage = state.get('progress', 0) if state else 0

        return render_template(
            'document_builder.html',
            templates=available_templates,
            is_processing=is_processing,
            percentage=percentage,
            back_url=url_for('auth_bp.dashboard'),
        )

    workspace = request.form['workspace']
    template = request.form['template']
    reference_id = request.form['reference_id']
    file_format = request.form['file_format']
    approval_code = request.form['approval_code']
    network_reference = request.form['network_reference']
    retrieval_reference = request.form['retrieval_reference']
    external_order_id = request.form['external_order_id']

    try:
        reference_id = int(reference_id)
    except ValueError:
        return jsonify({'error': gettext('Reference ID must be a number')}), 400

    set_process_state(
        current_user.id,
        function_key,
        {
            'status': 'processing',
            'progress': 0,
            'parameters': None,
            'file_url': None,
            'timestamp': time.time(),
        },
    )

    build_document_process.delay(
        user_id=current_user.id,
        function_key=function_key,
        workspace=workspace,
        template=template,
        templates_path=templates_path,
        reference_id=reference_id,
        file_format=file_format,
        approval_code=approval_code,
        network_reference=network_reference,
        retrieval_reference=retrieval_reference,
        external_order_id=external_order_id,
    )

    return jsonify(get_process_state(current_user.id, function_key))


@document_builder_bp.route('/download/<function_key>/<filename>', methods=['GET'])
@login_required
def download_file(function_key, filename):
    file_path = safe_join(g.temp_dir, filename)
    if file_path and os.path.isfile(file_path):

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
            except Exception as exc:
                app.logger.error(f'[download_file] Error deleting file {file_path}: {exc}')
            return response

        delete_process_state(current_user.id, function_key)

        with open(file_path, 'rb') as file_obj:
            return send_file(
                BytesIO(file_obj.read()),
                as_attachment=True,
                download_name=filename,
            )

    flash(gettext('File not found.'), 'danger')
    return render_template('document_builder.html', templates=['demo_template']), 404


@document_builder_bp.route('/status/<function_key>', methods=['GET'])
@login_required
def get_status(function_key):
    function_state = get_process_state(current_user.id, function_key)
    if function_state is None:
        return {'status': 'not_started', 'progress': 0}
    return function_state
