import app_functions.transaction_lookup as transaction_lookup_module


def test_transaction_lookup_status_not_started(admin_client):
    response = admin_client.get("/transaction_lookup/status/transaction_lookup")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "not_started"
    assert data["progress"] == 0


def test_transaction_lookup_rejects_invalid_date_range(admin_client):
    response = admin_client.post(
        "/transaction_lookup/lookup",
        data={
            "search_type": "single",
            "input_reference": "ABCDE12345",
            "start_date": "2026-03-10",
            "end_date": "2026-03-01",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["error"] == "End date is earlier than start date"


def test_transaction_lookup_single_id_starts_processing(admin_client, monkeypatch):
    captured_delay_kwargs = {}

    def fake_delay(**kwargs):
        captured_delay_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(transaction_lookup_module.transaction_lookup_process, "delay", fake_delay)

    response = admin_client.post(
        "/transaction_lookup/lookup",
        data={
            "search_type": "single",
            "input_reference": "ABCDE12345",
            "start_date": "2026-03-01",
            "end_date": "2026-03-10",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "processing"
    assert payload["reference_ids"] == ["ABCDE12345"]

    assert captured_delay_kwargs["function_key"] == "transaction_lookup"
    assert captured_delay_kwargs["reference_ids"] == ["ABCDE12345"]
