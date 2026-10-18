# MIT License - Copyright (c) 2026 eripum9

import pytest

import amazon_devtools


def _native_result(status="success", entries=None, error="", code=None):
    result = {
        "status": status,
        "entries": entries or [],
        "duration_ms": 2,
        "backend": "win32",
        "stage": "complete" if status == "success" else "process_image",
        "error": error,
    }
    if code is not None:
        result["windows_error_code"] = code
    return result


def _forbid_powershell(*args, **kwargs):
    raise AssertionError("Owner verification must not invoke PowerShell")


@pytest.mark.parametrize("status,code", [("access_denied", 5), ("api_error", 50), ("listener_changed", None), ("identity_unavailable", 87), ("no_listener", None)])
def test_native_failure_preserves_reason_and_stays_untrusted(monkeypatch, status, code):
    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: _native_result(status, error="Windows query failed", code=code))
    monkeypatch.setattr(amazon_devtools, "_run_powershell", _forbid_powershell)
    monkeypatch.setattr(amazon_devtools, "_launcher_candidates", _forbid_powershell)
    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["trusted"] is False
    assert result["status"] == "unavailable"
    assert result["query"]["status"] == status
    assert result["query"]["backend"] == "win32"
    assert result["query"]["diagnostic_build"] == "issue52-2"
    if code is not None:
        assert result["query"]["windows_error_code"] == code


def test_unexpected_native_failure_does_not_reuse_previous_success(monkeypatch):
    amazon_devtools._PORT_OWNER_QUERY.value = {"status": "success"}

    def fail(port):
        raise OSError("Unexpected failure")

    monkeypatch.setattr(amazon_devtools, "query_listener_owners", fail)
    monkeypatch.setattr(amazon_devtools, "_launcher_candidates", _forbid_powershell)
    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["trusted"] is False
    assert result["query"]["status"] == "api_error"


def test_exact_store_owner_never_needs_powershell_discovery(monkeypatch, tmp_path):
    package = tmp_path / "WindowsApps" / "AmazonMobileLLC.AmazonMusic_9.5.2.0_x86__kc6t79cpj4tp0"
    package.mkdir(parents=True)
    image = package / "Amazon Music.exe"
    image.write_bytes(b"test")
    entry = {"Pid": 44, "Pids": [44], "Names": [image.name], "Paths": [str(image)]}
    monkeypatch.setattr(amazon_devtools, "_LAST_LAUNCH", {})
    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: _native_result(entries=[entry]))
    monkeypatch.setattr(amazon_devtools, "_run_powershell", _forbid_powershell)
    monkeypatch.setattr(amazon_devtools, "_launcher_candidates", _forbid_powershell)
    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["trusted"] is True
    assert result["pids"] == ["44"]
    assert result["query"]["status"] == "success"


def test_unrelated_native_listener_stays_rejected(monkeypatch, tmp_path):
    image = tmp_path / "unrelated.exe"
    image.write_bytes(b"test")
    entry = {"Pid": 44, "Pids": [44], "Names": [image.name], "Paths": [str(image)]}
    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: _native_result(entries=[entry]))
    monkeypatch.setattr(amazon_devtools, "_launcher_candidates", _forbid_powershell)
    result = amazon_devtools._devtools_owner_trust(52856, force=True)
    assert result["trusted"] is False
    assert result["status"] == "rejected"


def test_native_failure_logging_is_bounded_and_reports_recovery(monkeypatch, capsys):
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_LOG_STATE", {})
    failure = _native_result("access_denied", error=r"Cannot query C:\Users\private\AmazonMusic.exe" + "x" * 300, code=5)
    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: failure)
    amazon_devtools._port_owner_entries(52856)
    amazon_devtools._port_owner_entries(52856)
    first = capsys.readouterr().out
    assert first.count("[Metadata owner]") == 1
    assert "build=issue52-2 backend=win32" in first
    assert "private" not in first
    assert len(amazon_devtools._PORT_OWNER_QUERY.value["error"]) <= 240

    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: _native_result())
    amazon_devtools._port_owner_entries(52856)
    assert "status=recovered" in capsys.readouterr().out


def test_ten_second_owner_cache_is_preserved(monkeypatch):
    calls = []
    monkeypatch.setattr(amazon_devtools, "_PORT_OWNER_CACHE", {"port": 0, "expires": 0.0, "value": None})
    monkeypatch.setattr(amazon_devtools.time, "time", lambda: 100.0)
    monkeypatch.setattr(amazon_devtools, "query_listener_owners", lambda port: calls.append(port) or _native_result("no_listener"))
    first = amazon_devtools._devtools_owner_trust(52856)
    second = amazon_devtools._devtools_owner_trust(52856)
    assert first is second
    assert calls == [52856]
    assert amazon_devtools._PORT_OWNER_CACHE["expires"] == 110.0
