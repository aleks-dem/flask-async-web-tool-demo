def test_login_success_redirects_to_dashboard(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_login_invalid_credentials_shows_error(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data


def test_protected_route_requires_authentication(client):
    response = client.get("/transaction_lookup/lookup", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_rejects_duplicate_username(admin_client):
    response = admin_client.post(
        "/admin/create_user",
        data={
            "username": "admin",
            "password": "some-pass",
            "show_name": "Duplicate",
            "functions": ["transaction_lookup"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already exists" in response.data
