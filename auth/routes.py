from datetime import timedelta

from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from flask_babel import gettext
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from . import auth_bp
from utils.users_repository import get_all_users_raw, User
import utils.globals as g


def _password_matches(stored_password, candidate_password):
    try:
        return check_password_hash(stored_password, candidate_password)
    except ValueError:
        return False


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        all_users = get_all_users_raw()

        for user_id, user_info_list in all_users.items():
            data = user_info_list[0]
            if data['username'] == username and _password_matches(data['password'], password):
                user_obj = User(
                    user_id,
                    data['username'],
                    data['functions'],
                    data.get('is_admin', 0),
                    data.get('show_name', ''),
                )
                login_user(user_obj, duration=timedelta(days=30))
                flash(gettext('Welcome back, ') + user_obj.show_name + '!', 'success')
                return redirect(url_for('auth_bp.dashboard'))

        flash(gettext('Invalid credentials'), 'danger')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash(gettext('Logged out successfully'), 'success')
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    available_functions = []

    if current_user.is_admin:
        for _, function_data in g.function_details.items():
            available_functions.append(
                {
                    'name': function_data['name'],
                    'description': function_data['description'],
                    'endpoint': function_data['endpoint'],
                }
            )
    else:
        for function_key in current_user.functions:
            if function_key in g.function_details:
                available_functions.append(
                    {
                        'name': g.function_details[function_key]['name'],
                        'description': g.function_details[function_key]['description'],
                        'endpoint': g.function_details[function_key]['endpoint'],
                    }
                )

    return render_template('dashboard.html', available_functions=available_functions)


@auth_bp.route('/change_lang/<lang>')
def change_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['lang'] = lang
    return redirect(url_for('home'))
