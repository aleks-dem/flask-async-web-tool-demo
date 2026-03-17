import os
import time
from datetime import datetime
from io import BytesIO

import openpyxl
from flask import (
    render_template,
    abort,
    url_for,
    request,
    jsonify,
    send_file,
    after_this_request,
    flash,
)
from flask import current_app as app
from flask_login import login_required, current_user
from flask_babel import gettext
from werkzeug.utils import safe_join

from . import transaction_lookup_bp
import utils.globals as g
from services.transaction_lookup_task import transaction_lookup_process
from utils.redis_state_repository import (
    set_process_state,
    get_process_state,
    delete_process_state,
)


@transaction_lookup_bp.route('/lookup', methods=['GET', 'POST'])
@login_required
def lookup():
    if not (current_user.is_admin or 'transaction_lookup' in current_user.functions):
        abort(403)

    function_key = 'transaction_lookup'

    if request.method == 'GET':
        state = get_process_state(current_user.id, function_key)
        is_processing = bool(state and state.get('status') in ['processing', 'in_progress'])
        percentage = state.get('progress', 0) if state else 0

        return render_template(
            'transaction_lookup.html',
            is_processing=is_processing,
            percentage=percentage,
            back_url=url_for('auth_bp.dashboard'),
        )

    user_id = current_user.id
    allowed_number_of_rows = 50

    search_type = request.form.get('search_type', 'single')
    input_reference = request.form.get('input_reference', '').strip()
    start_date_form = request.form.get('start_date', '').strip()
    end_date_form = request.form.get('end_date', '').strip()

    try:
        dt_start = datetime.strptime(start_date_form, '%Y-%m-%d')
        dt_end = datetime.strptime(end_date_form, '%Y-%m-%d')
    except ValueError:
        return jsonify({'status': 'error', 'error': gettext('Invalid date format')}), 400

    if dt_end < dt_start:
        return jsonify({'status': 'error', 'error': gettext('End date is earlier than start date')}), 400

    max_diff_days = 92
    if (dt_end - dt_start).days > max_diff_days:
        return jsonify({'status': 'error', 'error': gettext('Date range must not exceed 3 months')}), 400

    start_date = dt_start.strftime('%Y-%m-%d')
    end_date = dt_end.strftime('%Y-%m-%d')

    reference_ids = []
    if search_type == 'single':
        if not input_reference:
            return jsonify({'status': 'error', 'error': gettext('Reference ID is required')}), 400
        if len(input_reference) < 5:
            return jsonify(
                {
                    'status': 'error',
                    'error': gettext('Reference ID must be at least 5 characters long'),
                }
            ), 400
        reference_ids = [input_reference]
    else:
        file_obj = request.files.get('excel_file')
        if not file_obj:
            return jsonify({'status': 'error', 'error': gettext('Excel file is required')}), 400
        try:
            workbook = openpyxl.load_workbook(file_obj, data_only=True)
            sheet = workbook.worksheets[0]
            for row in sheet.iter_rows(min_col=1, max_col=1, values_only=True):
                value = row[0]
                if value is None:
                    continue
                candidate = str(value).strip()
                if len(candidate) < 5:
                    continue
                reference_ids.append(candidate)

            reference_ids = list(dict.fromkeys(reference_ids))

            if len(reference_ids) > allowed_number_of_rows:
                return jsonify(
                    {
                        'status': 'error',
                        'error': gettext('Max {rows_count} rows allowed').format(
                            rows_count=allowed_number_of_rows
                        ),
                    }
                ), 400
            if len(reference_ids) == 0:
                return jsonify(
                    {
                        'status': 'error',
                        'error': gettext('Excel file must contain at least 1 reference ID'),
                    }
                ), 400
        except Exception as exc:
            return jsonify(
                {
                    'status': 'error',
                    'error': gettext('Error reading Excel: {err_text}').format(err_text=str(exc)),
                }
            ), 400

    set_process_state(
        user_id,
        function_key,
        {
            'status': 'processing',
            'progress': 0,
            'parameters': None,
            'file_url': None,
            'timestamp': time.time(),
            'start_date': start_date,
            'end_date': end_date,
            'reference_ids': reference_ids,
        },
    )

    transaction_lookup_process.delay(
        user_id=user_id,
        function_key=function_key,
        start_date=start_date,
        end_date=end_date,
        reference_ids=reference_ids,
    )

    return jsonify(get_process_state(current_user.id, function_key))


@transaction_lookup_bp.route('/status/<function_key>', methods=['GET'])
@login_required
def get_status(function_key):
    user_id = current_user.id
    state = get_process_state(user_id, function_key)
    if state is None:
        return jsonify({'status': 'not_started', 'progress': 0})
    return jsonify(state)


@transaction_lookup_bp.route('/download/<function_key>/<filename>', methods=['GET'])
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
    return render_template('transaction_lookup.html'), 404
