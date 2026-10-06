"""
The streamable HTTP transport (MCP_TRANSPORT=http), exercised in-process.

These hit the Starlette app directly, so they never open a socket or contact
Zendesk; tool calls that need Zendesk are out of scope here.
"""
import pytest
from starlette.testclient import TestClient

from zendesk_mcp_server import server

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


@pytest.fixture
def client():
    with TestClient(server.create_http_app()) as c:
        yield c


def rpc(client, method, params=None, path="/mcp", req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    return client.post(path, json=body, headers=HEADERS)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_initialize_reports_server_identity(client):
    resp = rpc(client, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    info = resp.json()["result"]["serverInfo"]
    assert info == {"name": "Zendesk Server", "version": "0.1.0"}


def test_stateless_tools_list_needs_no_session(client):
    resp = rpc(client, "tools/list")
    assert resp.status_code == 200
    assert "mcp-session-id" not in resp.headers
    names = {t["name"] for t in resp.json()["result"]["tools"]}
    assert names == {
        "get_ticket",
        "get_tickets",
        "get_ticket_comments",
        "get_ticket_attachment",
        "create_ticket",
        "create_ticket_comment",
        "update_ticket",
    }


def test_trailing_slash_is_served_without_redirect(client):
    resp = rpc(client, "tools/list", path="/mcp/")
    assert resp.status_code == 200
    assert resp.json()["result"]["tools"]


def test_other_paths_are_not_mcp(client):
    assert rpc(client, "tools/list", path="/").status_code == 404
    assert rpc(client, "tools/list", path="/mcpx").status_code == 404
