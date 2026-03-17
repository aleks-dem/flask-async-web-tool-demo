import app as app_module
import app_functions.document_builder as document_builder_module
import app_functions.transaction_lookup as transaction_lookup_module
import pytest


@pytest.fixture
def app(monkeypatch):
    process_state = {}

    def set_process_state(user_id, function_key, state):
        process_state[(user_id, function_key)] = state

    def get_process_state(user_id, function_key):
        return process_state.get((user_id, function_key))

    def delete_process_state(user_id, function_key):
        process_state.pop((user_id, function_key), None)

    # Prevent scheduler and Redis cleanup startup hooks during tests.
    monkeypatch.setattr(app_module, "init_scheduler", lambda _app: None)
    monkeypatch.setattr(app_module, "clear_in_progress_on_startup", lambda: None)

    # Replace Redis-backed state repository with in-memory dictionary.
    monkeypatch.setattr(document_builder_module, "set_process_state", set_process_state)
    monkeypatch.setattr(document_builder_module, "get_process_state", get_process_state)
    monkeypatch.setattr(document_builder_module, "delete_process_state", delete_process_state)

    monkeypatch.setattr(transaction_lookup_module, "set_process_state", set_process_state)
    monkeypatch.setattr(transaction_lookup_module, "get_process_state", get_process_state)
    monkeypatch.setattr(transaction_lookup_module, "delete_process_state", delete_process_state)

    flask_app = app_module.create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    flask_app.test_process_state = process_state
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client
