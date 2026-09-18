from backend.app import main


def test_health_reports_runtime_readiness_and_required_data():
    payload = main.health()

    assert payload["status"] == "ok"
    assert payload["readiness"] == "ready"
    assert "demo_mode" in payload
    assert payload["data"]["anatomy"]["exists"] is True
    assert payload["data"]["atlas_manifest"]["exists"] is True
    assert isinstance(payload["ai"]["external_calls_disabled"], bool)
