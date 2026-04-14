import httpx
import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient
from tests.conftest import requires_iris, MCP_URL, MCP_TRANSPORT, USERS, _basic_auth_header, _mcp_config


pytestmark = requires_iris

# Module-level shared clients — created once, reused across tests to minimise IRIS licence slots
_shared_clients: dict[str, MultiServerMCPClient] = {}


def _get_client(username: str, password: str) -> MultiServerMCPClient:
    if username in (USERS["doctor"][0], USERS["nurse"][0]):
        if username not in _shared_clients:
            _shared_clients[username] = MultiServerMCPClient(_mcp_config(username, password))
        return _shared_clients[username]
    return MultiServerMCPClient(_mcp_config(username, password))


async def _get_tools_for_user(username: str, password: str) -> list:
    return await _get_client(username, password).get_tools()


@pytest.mark.asyncio
async def test_mcp_health_endpoint():
    url = MCP_URL.replace("/mcp/readyai", "/mcp/readyAI/v1/health")
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
    assert r.status_code in (200, 406), f"Expected 200 or 406, got {r.status_code}"


@pytest.mark.asyncio
async def test_tool_discovery_doctor_sees_sqltool_and_echo():
    tools = await _get_tools_for_user(*USERS["doctor"])
    names = {t.name for t in tools}
    assert any("EchoUser" in n for n in names), f"EchoUser missing from {names}"
    assert any("ListTables" in n for n in names), f"ListTables missing from {names}"
    assert any("QueryTable" in n for n in names), f"QueryTable missing from {names}"
    assert any("FindPatientsBySurname" in n for n in names), f"FindPatientsBySurname missing from {names}"


@pytest.mark.asyncio
async def test_tool_discovery_nurse_sees_echo_and_standard_queries():
    tools = await _get_tools_for_user(*USERS["nurse"])
    names = {t.name for t in tools}
    assert any("EchoUser" in n for n in names), f"EchoUser missing from {names}"
    assert any("FindPatientsBySurname" in n for n in names), f"FindPatientsBySurname missing from {names}"
    assert not any("ListTables" in n for n in names), "Nurse must not see ListTables (Doctor-only)"


_TOOL_INVOCATION_XFAIL = pytest.mark.xfail(
    reason="iris-mcp-server 2.0.0 uses WebSocket backchannel for tool calls; "
           "mcp 1.26.0 client sends incompatible WebSocket handshake. "
           "Works when called as the only active session.",
    strict=False,
)


@pytest.mark.asyncio
@_TOOL_INVOCATION_XFAIL
async def test_echo_user_returns_doctor_username():
    tools = await _get_tools_for_user(*USERS["doctor"])
    echo = next((t for t in tools if "EchoUser" in t.name), None)
    assert echo, "EchoUser tool not found"
    result = await echo.ainvoke({})
    assert "DScully" in str(result), f"Expected DScully in echo result, got: {result}"


@pytest.mark.asyncio
@_TOOL_INVOCATION_XFAIL
async def test_echo_user_returns_nurse_username():
    tools = await _get_tools_for_user(*USERS["nurse"])
    echo = next((t for t in tools if "EchoUser" in t.name), None)
    assert echo, "EchoUser tool not found"
    result = await echo.ainvoke({})
    assert "NJoy" in str(result), f"Expected NJoy in echo result, got: {result}"


@pytest.mark.asyncio
async def test_invalid_credentials_rejected():
    auth = _basic_auth_header(*USERS["invalid"])
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(MCP_URL, headers={"Authorization": auth})
    assert r.status_code in (401, 403, 406), f"Expected 401/403/406, got {r.status_code}"


@pytest.mark.asyncio
@_TOOL_INVOCATION_XFAIL
async def test_nurse_calling_sqltool_returns_result():
    tools = await _get_tools_for_user(*USERS["nurse"])
    list_tables = next((t for t in tools if "ListTables" in t.name), None)
    if list_tables is None:
        return
    result = await list_tables.ainvoke({})
    assert result is not None
