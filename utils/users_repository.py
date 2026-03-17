import os
import uuid
import yaml

from flask_login import UserMixin
from werkzeug.security import generate_password_hash


USERS_FILE = os.path.join('data', 'users.yaml')


class User(UserMixin):
    def __init__(self, user_id, username, functions, is_admin=0, show_name=''):
        self.id = user_id
        self.username = username
        self.functions = functions
        self.is_admin = bool(is_admin)
        self.show_name = show_name


def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as file_obj:
        return yaml.safe_load(file_obj) or {}


def _save_users(users_dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as file_obj:
        yaml.safe_dump(users_dict, file_obj, allow_unicode=True, sort_keys=True)


def get_all_users_raw():
    return _load_users()


def get_all_users(*, sort_column='username', sort_direction='asc'):
    users_dict = _load_users()
    users = list(users_dict.items())

    def sort_key(item):
        user_id, data_list = item
        data = data_list[0]
        if sort_column == 'user_id':
            return user_id
        if sort_column == 'username':
            return data.get('username', '')
        if sort_column == 'is_admin':
            return int(data.get('is_admin', 0))
        if sort_column == 'functions':
            return len(data.get('functions', []))
        return data.get(sort_column, '')

    reverse = sort_direction.lower() == 'desc'
    users.sort(key=sort_key, reverse=reverse)
    return users


def load_user_by_id(user_id):
    users_dict = _load_users()
    user_info = users_dict.get(user_id)
    if user_info:
        data = user_info[0]
        return User(
            user_id,
            data['username'],
            data['functions'],
            data.get('is_admin', 0),
            data.get('show_name', data['username']),
        )
    return None


def username_exists(username, exclude_user_id=None):
    normalized = (username or '').strip().lower()
    if not normalized:
        return False

    users_dict = _load_users()
    for existing_user_id, user_info in users_dict.items():
        if exclude_user_id and existing_user_id == exclude_user_id:
            continue
        data = user_info[0]
        if data.get('username', '').strip().lower() == normalized:
            return True
    return False


def create_new_user(username, password, show_name, functions, is_admin):
    users_dict = _load_users()
    if username_exists(username):
        raise ValueError('Username already exists')

    user_id = f'user_{uuid.uuid4().hex[:12]}'

    users_dict[user_id] = [
        {
            'username': username.strip(),
            'password': generate_password_hash(password),
            'functions': functions,
            'is_admin': is_admin,
            'show_name': show_name.strip(),
        }
    ]
    _save_users(users_dict)
    return user_id


def delete_user_by_id(user_id):
    users_dict = _load_users()
    if user_id in users_dict:
        deleted_username = users_dict[user_id][0]['username']
        del users_dict[user_id]
        _save_users(users_dict)
        return deleted_username
    return None


def update_user(user_id, new_password=None, new_show_name=None, new_functions=None, new_is_admin=None):
    users_dict = _load_users()
    if user_id not in users_dict:
        return False

    user_data = users_dict[user_id][0]

    if new_password:
        user_data['password'] = generate_password_hash(new_password)
    if new_show_name:
        user_data['show_name'] = new_show_name
    if new_functions is not None:
        user_data['functions'] = new_functions
    if new_is_admin is not None:
        user_data['is_admin'] = new_is_admin

    users_dict[user_id][0] = user_data
    _save_users(users_dict)
    return True


def get_top_users(n=50):
    users_dict = _load_users()
    users = [(uid, data[0]) for uid, data in users_dict.items()]
    users_sorted = sorted(users, key=lambda item: len(item[1].get('functions', [])), reverse=True)
    return users_sorted[:n]
