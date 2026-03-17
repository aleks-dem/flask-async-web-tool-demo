import app_functions.document_builder as document_builder_module


def test_document_builder_status_not_started(admin_client):
    response = admin_client.get("/document_builder/status/document_builder")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "not_started"
    assert data["progress"] == 0


def test_document_builder_post_starts_processing(admin_client, monkeypatch):
    captured_delay_kwargs = {}

    def fake_delay(**kwargs):
        captured_delay_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(document_builder_module.build_document_process, "delay", fake_delay)

    response = admin_client.post(
        "/document_builder/build",
        data={
            "workspace": "workspace_a",
            "template": "demo_template",
            "reference_id": "12345",
            "file_format": "docx",
            "approval_code": "OK1",
            "network_reference": "NET1",
            "retrieval_reference": "RET1",
            "external_order_id": "EXT1",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "processing"
    assert data["progress"] == 0

    assert captured_delay_kwargs["function_key"] == "document_builder"
    assert captured_delay_kwargs["reference_id"] == 12345
    assert captured_delay_kwargs["workspace"] == "workspace_a"


def test_document_builder_post_invalid_reference_id_returns_400(admin_client):
    response = admin_client.post(
        "/document_builder/build",
        data={
            "workspace": "workspace_a",
            "template": "demo_template",
            "reference_id": "not-a-number",
            "file_format": "pdf",
            "approval_code": "",
            "network_reference": "",
            "retrieval_reference": "",
            "external_order_id": "",
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Reference ID must be a number"


def test_document_builder_download_blocks_path_traversal(admin_client):
    response = admin_client.get("/document_builder/download/document_builder/../../users.yaml")
    assert response.status_code == 404
