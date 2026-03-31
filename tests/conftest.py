import base64
import os

import pytest

IRIS_HOST = os.environ.get("IRIS_HOST", "localhost")
IRIS_PORT = int(os.environ.get("IRIS_PORT", "1973"))
IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")
MCP_URL = os.environ.get("MCP_URL", "http://localhost:8888/mcp/readyai")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable_http")
SKIP_IRIS_TESTS = os.environ.get("SKIP_IRIS_TESTS", "false").lower() == "true"

USERS = {
    "superuser": ("SuperUser", "SYS"),
    "doctor": ("DScully", "XFiles"),
    "nurse": ("NJoy", "pokemon"),
    "invalid": ("nobody", "wrongpassword"),
}


def _iris_connect(username: str, password: str):
    import iris  # noqa: PLC0415

    return iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, username, password)


@pytest.fixture(scope="function")
def iris_conn_doctor():
    conn = _iris_connect(*USERS["doctor"])
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def iris_conn_nurse():
    conn = _iris_connect(*USERS["nurse"])
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def iris_conn_superuser():
    conn = _iris_connect(*USERS["superuser"])
    yield conn
    conn.close()


def _basic_auth_header(username: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def _mcp_config(username: str, password: str) -> dict:
    return {
        "readyai": {
            "transport": MCP_TRANSPORT,
            "url": MCP_URL,
            "headers": {"Authorization": _basic_auth_header(username, password)},
        }
    }


@pytest.fixture(scope="session")
def mcp_client_doctor():
    from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: PLC0415

    return MultiServerMCPClient(_mcp_config(*USERS["doctor"]))


@pytest.fixture(scope="session")
def mcp_client_nurse():
    from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: PLC0415

    return MultiServerMCPClient(_mcp_config(*USERS["nurse"]))


requires_iris = pytest.mark.skipif(
    SKIP_IRIS_TESTS,
    reason="SKIP_IRIS_TESTS=true — set to false to run against live stack",
)


def _fhir_tables_exist() -> bool:
    if SKIP_IRIS_TESTS:
        return False
    conn = None
    try:
        import iris  # noqa: PLC0415

        conn = iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, *USERS["superuser"])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='AFHIRData'")
        count = cur.fetchone()[0]
        return count > 0
    except Exception:
        return False
    finally:
        if conn is not None:
            conn.close()


requires_fhir = pytest.mark.skipif(
    not _fhir_tables_exist(),
    reason="AFHIRData schema not set up — run FHIR SQL Builder setup first",
)
