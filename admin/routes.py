from math import ceil
from functools import wraps

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session,
    jsonify,
)
from flask_login import login_required, current_user
from flask_babel import gettext

from . import admin_bp
from utils.users_repository import (
    get_all_users,
    get_top_users,
    create_new_user,
    delete_user_by_id,
    update_user,
    load_user_by_id,
    username_exists,
)
import utils.globals as g


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_admin:
            return func(*args, **kwargs)
        abort(403)

    return decorated_function


def _filtered_sorted_users(*, q, sort_column, sort_direction, page, per_page):
    users_sorted = get_all_users(sort_column=sort_column, sort_direction=sort_direction)

    if q:
        users_sorted = [
            (uid, data) for uid, data in users_sorted if q.lower() in data[0]['username'].lower()
        ]

    total_pages = max(1, ceil(len(users_sorted) / per_page))
    page = min(max(1, page), total_pages)
    start, end = (page - 1) * per_page, page * per_page
    users_page = users_sorted[start:end]
    return users_page, total_pages, page


def _page_window(total_pages, current_page, window=2):
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    pages = [1]
    if current_page - window > 2:
        pages.append(None)

    start = max(2, current_page - window)
    end = min(total_pages - 1, current_page + window)
    pages.extend(range(start, end + 1))

    if end < total_pages - 1:
        pages.append(None)

    pages.append(total_pages)
    return pages


def _back_to_panel():
    return redirect(
        url_for(
            'admin_bp.admin_panel',
            per_page=session.get('per_page', 10),
            q=session.get('q', ''),
            sort_column=session.get('sort_column', 'user_id'),
            sort_direction=session.get('sort_direction', 'asc'),
        )
    )


@admin_bp.route('/', methods=['GET'])
@login_required
@admin_required
def admin_panel():
    sort_column = request.args.get('sort_column', session.get('sort_column', 'user_id'))
    sort_direction = request.args.get('sort_direction', session.get('sort_direction', 'asc'))
    session['sort_column'], session['sort_direction'] = sort_column, sort_direction

    arg_per_page = request.args.get('per_page', type=int)
    if arg_per_page in (5, 10, 20, 50):
        per_page = arg_per_page
        session['per_page'] = per_page
    else:
        per_page = session.get('per_page', 10)

    q_param = request.args.get('q')
    if q_param is not None and q_param.strip() != session.get('q', ''):
        session['q'] = q_param.strip()
    q = session.get('q', '')

    page_req = request.args.get('page', 1, type=int)

    users_page, total_pages, current_page = _filtered_sorted_users(
        q=q,
        sort_column=sort_column,
        sort_direction=sort_direction,
        page=page_req,
        per_page=per_page,
    )

    return render_template(
        'admin.html',
        all_users=users_page,
        top_users=get_top_users(50),
        function_details=g.function_details,
        total_pages=total_pages,
        current_page=current_page,
        per_page=per_page,
        sort_column=sort_column,
        sort_direction=sort_direction,
        q=q,
        page_numbers=_page_window(total_pages, current_page),
    )


@admin_bp.route('/api/users')
@login_required
@admin_required
def api_users():
    sort_column = request.args.get('sort_column', 'user_id')
    sort_direction = request.args.get('sort_direction', 'asc')
    per_page = request.args.get('per_page', 10, type=int)
    if per_page not in (5, 10, 20, 50):
        per_page = 10
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    session['q'] = q
    session['sort_column'] = sort_column
    session['sort_direction'] = sort_direction
    session['per_page'] = per_page

    users_page, total_pages, current_page = _filtered_sorted_users(
        q=q,
        sort_column=sort_column,
        sort_direction=sort_direction,
        page=page,
        per_page=per_page,
    )

    return jsonify(
        {
            'users': [
                {
                    'id': uid,
                    'username': data[0]['username'],
                    'is_admin': int(data[0]['is_admin']),
                    'functions': data[0]['functions'],
                }
                for uid, data in users_page
            ],
            'total_pages': total_pages,
            'current_page': current_page,
        }
    )


@admin_bp.route('/create_user', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password')
    show_name = (request.form.get('show_name') or '').strip()
    functions = request.form.getlist('functions')
    is_admin = 1 if request.form.get('is_admin') == 'on' else 0

    if not username or not password or not show_name:
        flash(gettext('Username, password and show_name are required.'), 'danger')
        return _back_to_panel()

    if username_exists(username):
        flash(gettext("Username '{username}' already exists.").format(username=username), 'danger')
        return _back_to_panel()

    create_new_user(username, password, show_name, functions, is_admin)
    flash(gettext("User '{show_name}' created.").format(show_name=show_name), 'success')
    return _back_to_panel()


@admin_bp.route('/delete_user/<user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash(gettext('Cannot delete the currently logged-in admin.'), 'danger')
        return _back_to_panel()

    deleted_username = delete_user_by_id(user_id)
    if deleted_username:
        flash(
            gettext("User '{deleted_username}' deleted.").format(
                deleted_username=deleted_username
            ),
            'success',
        )
    else:
        flash(gettext('User not found.'), 'warning')
    return _back_to_panel()


@admin_bp.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user_data = load_user_by_id(user_id)
    if not user_data:
        flash(gettext('User not found.'), 'danger')
        return _back_to_panel()

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        if new_password:
            flash(gettext('Password updated.'), 'success')

        new_show_name = request.form.get('show_name')
        if not new_show_name:
            flash(gettext('Show name cannot be empty.'), 'danger')
            return redirect(url_for('admin_bp.edit_user', user_id=user_id))

        new_functions = request.form.getlist('functions')
        new_is_admin = 1 if request.form.get('is_admin') == 'on' else 0

        if user_id == current_user.id and current_user.is_admin:
            new_is_admin = 1

        updated = update_user(
            user_id,
            new_password=new_password,
            new_show_name=new_show_name,
            new_functions=new_functions,
            new_is_admin=new_is_admin,
        )

        if updated:
            flash(
                gettext("User '{show_name}' updated.").format(
                    show_name=user_data.show_name
                ),
                'success',
            )
        else:
            flash(gettext('Error updating user.'), 'danger')

        return _back_to_panel()

    return render_template(
        'edit_user.html',
        user_id=user_id,
        user_data=user_data,
        function_details=g.function_details,
    )
