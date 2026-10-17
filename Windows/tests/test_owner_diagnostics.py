# MIT License - Copyright (c) 2026 eripum9

import json
import subprocess
from types import SimpleNamespace

import amazon_devtools


def _completed(stdout, returncode=0, stderr=""):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def _query(monkeypatch, result=None, error=None):
    def run(script, timeout):
        assert timeout == 4
        assert "Failure" in script and "Stage" in script and "Category" in script
        if error:
            raise error
        return result

    monkeypatch.setattr(amazon_devtools, "_run_powershell", run)
    return amazon_devtools._port_owner_entries(52856), amazon_devtools._PORT_OWNER_QUERY.value


def test_owner_query_classifies_timeout_and_os_launch_error(monkeypatch):
    entries, query = _query(monkeypatch, error=subprocess.TimeoutExpired(["powershell", "-Command", "SECRET-RAW-SCRIPT"], 4))
    assert entries == []
    assert query["status"] == "timeout"
    assert query["timeout_seconds"] == 4
    assert query["error"] == "PowerShell owner query timed out after 4 seconds"
    assert "SECRET-RAW-SCRIPT" not in query["error"]

    entries, query = _query(monkeypatch, error=FileNotFoundError("powershell.exe missing"))
    assert entries == []
    assert query["status"] == "launch_error"
    assert len(query["error"]) <= 240


def test_owner_query_classifies_nonzero_and_access_denied(monkeypatch, tmp_path, capsys):
    _, query = _query(monkeypatch, result=_completed("", returncode=1, stderr="command failed"))
    assert query["status"] == "command_failure"
    assert query["exit_code"] == 1

    envelope = {"Ok": False, "Items": [], "Failure": {
        "Stage": "process_query",
        "Category": "access_denied",
        "CategoryInfo": "SecurityError",
        "ErrorId": r"AccessDenied:C:\Users\private\query.ps1",
        "HResult": -2147024891,
        "NativeErrorCode": 2,
        "Error": "Access is denied",
    }}
    _, query = _query(monkeypatch, result=_completed(json.dumps(envelope)))
    assert query["status"] == "access_denied"
    assert query["stage"] == "process_query"
    assert query["error_category"] == "access_denied"
    assert query["windows_error_category"] == "SecurityError"
    assert query["windows_error_id"] == "AccessDenied:<path>"
    assert query["windows_hresult"] == -2147024891
    assert query["windows_native_error_code"] == 2
    assert "query.ps1" not in capsys.readouterr().out

    amazon_dir = tmp_path / "Amazon Music"
    amazon_dir.mkdir()
    amazon_exe = amazon_dir / "Amazon Music.exe"
    amazon_exe.write_bytes(b"test")
    partial = {
        "Ok": False,
        "Items": [{
            "Pid": 44,
            "Pids": [44],
            "Names": ["Amazon Music.exe"],
            "Paths": [str(amazon_exe)],
        }],
        "Failure": {"Stage": "process_query", "Category": "access_denied", "Error": "Access is denied"},
    }
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_CACHE", {"port": 0, "expires": 0.0, "value": None})
    monkeypatch.setattr(amazon_devtools, "_run_powershell", lambda script, timeout: _completed(json.dumps(partial)))
    trust = amazon_devtools._devtools_owner_trust(52856, launcher=str(amazon_exe), force=True)
    assert trust["trusted"] is True
    assert trust["query"]["status"] == "access_denied"


def test_owner_query_classifies_empty_invalid_and_missing_listener(monkeypatch):
    _, query = _query(monkeypatch, result=_completed("  "))
    assert query["status"] == "empty_response"

    _, query = _query(monkeypatch, result=_completed("not-json"))
    assert query["status"] == "malformed_response"

    _, query = _query(monkeypatch, result=_completed(json.dumps({"Ok": True, "Items": [], "Failure": None})))
    assert query["status"] == "no_listener"

    no_listener_failure = {
        "Ok": False,
        "Items": [],
        "Failure": {
            "Stage": "listener_query",
            "Category": "no_listener",
            "CategoryInfo": "ObjectNotFound",
            "ErrorId": "NoMatchingNetTCPConnectionFound",
            "Error": "No matching listener",
        },
    }
    _, query = _query(monkeypatch, result=_completed(json.dumps(no_listener_failure)))
    assert query["status"] == "no_listener"


def test_owner_query_rejects_invalid_ok_schema(monkeypatch):
    _, query = _query(monkeypatch, result=_completed(json.dumps({"Ok": "true", "Items": [], "Failure": None})))
    assert query["status"] == "malformed_response"


def test_owner_query_incomplete_identity_does_not_trust(monkeypatch):
    envelope = {"Ok": True, "Items": [{"Pid": 44, "Pids": [44], "Names": ["Amazon Music.exe"], "Paths": []}], "Failure": None}
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_CACHE", {"port": 0, "expires": 0.0, "value": None})
    monkeypatch.setattr(amazon_devtools, "_run_powershell", lambda script, timeout: _completed(json.dumps(envelope)))

    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["trusted"] is False
    assert result["status"] == "rejected"
    assert result["query"]["status"] == "listener_identity_incomplete"
    assert result["query"]["listener_pid"] == "44"
    assert "Pids" not in result["query"]
    assert "Paths" not in result["query"]


def test_owner_query_success_and_recovery_logging(monkeypatch, capsys):
    envelope = {"Ok": True, "Items": [{"Pid": 44, "Pids": [44], "Names": ["Amazon Music.exe"], "Paths": [r"C:\Amazon Music\Amazon Music.exe"]}], "Failure": None}
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_LOG_STATE", {})
    _query(monkeypatch, result=_completed(json.dumps({"Ok": False, "Items": [], "Failure": {"Stage": "listener_query", "Category": "command_failure", "Error": "temporary"}})))
    first_log = capsys.readouterr().out
    entries, query = _query(monkeypatch, result=_completed(json.dumps(envelope)))
    recovery_log = capsys.readouterr().out

    assert entries[0]["Pid"] == 44
    assert query["status"] == "success"
    assert query["diagnostic_build"] == "issue52-1"
    assert query["listener_pid"] == "44"
    assert "[Metadata owner]" in first_log
    assert "build=issue52-1" in first_log
    assert "status=recovered" in recovery_log


def test_owner_query_clears_stale_threadlocal_for_mocked_lookup(monkeypatch):
    _query(monkeypatch, result=_completed(json.dumps({"Ok": True, "Items": [], "Failure": None})))
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_CACHE", {"port": 0, "expires": 0.0, "value": None})
    monkeypatch.setattr(amazon_devtools, "_port_owner_entries", lambda port: [])

    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["query"]["status"] == "unavailable"
    assert result["query"]["error"] == "Owner query diagnostics unavailable"


def test_owner_query_repeated_identical_error_is_rate_limited(monkeypatch, capsys):
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_LOG_STATE", {})
    failed = {"Ok": False, "Items": [], "Failure": {"Stage": "listener_query", "Category": "command_failure", "Error": "same failure"}}
    response = _completed(json.dumps(failed))
    _query(monkeypatch, result=response)
    _query(monkeypatch, result=response)

    output = capsys.readouterr().out
    assert output.count("[Metadata owner]") == 1


def test_owner_query_script_classifies_structured_error_records(monkeypatch):
    script_holder = {}

    def run(script, timeout):
        script_holder["script"] = script
        return _completed(json.dumps({"Ok": True, "Items": [], "Failure": None}))

    monkeypatch.setattr(amazon_devtools, "_run_powershell", run)
    amazon_devtools._port_owner_entries(52856)
    script = script_holder["script"]
    assert "CategoryInfo.Category" in script
    assert "FullyQualifiedErrorId" in script
    assert "PermissionDenied" in script
    assert "SecurityError" in script
    assert "ObjectNotFound" in script
    assert "-2147217405" in script
    assert "HResult = $hresult" in script
    assert "NativeErrorCode = $nativeErrorCode" in script

