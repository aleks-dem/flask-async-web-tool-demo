from pathlib import Path
import uuid

import services.transaction_lookup_task as transaction_lookup_task_module


def test_transaction_lookup_task_finishes_with_completed_state(monkeypatch):
    state_updates = []

    def fake_update_state(
        user_id,
        function_key,
        status=None,
        progress=None,
        error=None,
        message=None,
        results=None,
        file_url=None,
        timestamp=None,
    ):
        state_updates.append(
            {
                "user_id": user_id,
                "function_key": function_key,
                "status": status,
                "progress": progress,
                "error": error,
                "message": message,
                "results": results,
                "file_url": file_url,
                "timestamp": timestamp,
            }
        )

    def fake_save_df_with_autowidth(_df, file_path):
        Path(file_path).write_text("ok", encoding="utf-8")

    monkeypatch.setattr(transaction_lookup_task_module, "update_state", fake_update_state)
    monkeypatch.setattr(
        transaction_lookup_task_module,
        "save_df_with_autowidth",
        fake_save_df_with_autowidth,
    )
    monkeypatch.setattr(transaction_lookup_task_module.time, "sleep", lambda _seconds: None)
    test_temp_dir = Path("data/temp/test_artifacts") / str(uuid.uuid4())
    test_temp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(transaction_lookup_task_module.g, "temp_dir", str(test_temp_dir))

    transaction_lookup_task_module.transaction_lookup_process.run(
        user_id="user_1001",
        function_key="transaction_lookup",
        start_date="2026-03-01",
        end_date="2026-03-10",
        reference_ids=["REF12345"],
    )

    assert state_updates, "Expected task to emit state updates."
    final_state = state_updates[-1]
    assert final_state["status"] == "completed"
    assert final_state["progress"] == 100
    assert final_state["file_url"].startswith("download/transaction_lookup/")
