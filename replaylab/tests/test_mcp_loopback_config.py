"""Local Unity MCP configuration preserves its transport and runtime paths."""
from pathlib import Path

import pytest

from replaylab_agent.agent_tools_config import servers_for_runtime, validate_mcp_server
from replaylab_agent.errors import ConfigurationError


@pytest.mark.parametrize("url", ["http://127.0.0.1:8080/mcp", "http://localhost:8080/mcp", "http://[::1]:8080/mcp", "https://example.test/mcp?project=one"])
def test_loopback_http_and_existing_https_are_accepted(url):
    assert validate_mcp_server({"id": "unity", "transport": "http", "url": url}).url == url


@pytest.mark.parametrize("url", ["http://example.test/mcp", "http://127.0.0.1.example.test/mcp", "http://localhost.example.test/mcp", "http://127.0.0.1:8080/mcp?token=secret", "https://user:secret@example.test/mcp", "http://[::1]:99999/mcp", "http://localhost/mcp#secret", "ws://127.0.0.1:8080/mcp"])
def test_insecure_or_credential_bearing_urls_are_rejected_without_echo(url):
    with pytest.raises(ConfigurationError) as error:
        validate_mcp_server({"id": "unity", "transport": "http", "url": url})
    assert "secret" not in str(error.value)
    assert url not in str(error.value)


def test_bundled_stdio_paths_resolve_for_launch_but_stay_portable_in_settings(tmp_path, monkeypatch):
    app = tmp_path / "Relocated Bread"
    tools = app / "tools"
    monkeypatch.setenv("BREAD_APP_ROOT", str(app))
    monkeypatch.setenv("BREAD_TOOLS_ROOT", str(tools))
    command = "%BREAD_TOOLS%/unity-mcp/runtime/python.exe"
    entry = "%BREAD_TOOLS%/unity-mcp/runtime/bread_unity_entry.py"
    pidfile = "%BREAD_APP%/workspace/unity.pid"
    args = ["-I", entry, "--transport", "stdio", "--pidfile", pidfile]

    server = validate_mcp_server({"id": "unitymcp", "transport": "stdio", "command": command, "args": args})
    saved = server.to_dict()
    assert saved["command"] == command
    assert saved["args"] == args

    (runtime,) = servers_for_runtime([server])
    assert Path(runtime["command"]) == tools / "unity-mcp/runtime/python.exe"
    isolated, runtime_entry, transport_flag, transport, pidfile_flag, runtime_pidfile = runtime["args"]
    assert Path(runtime_entry) == tools / "unity-mcp/runtime/bread_unity_entry.py"
    assert Path(runtime_pidfile) == app / "workspace/unity.pid"
    assert (isolated, transport_flag, transport, pidfile_flag) == ("-I", "--transport", "stdio", "--pidfile")
