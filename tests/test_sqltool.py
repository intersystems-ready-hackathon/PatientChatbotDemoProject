import json

import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient
from tests.conftest import requires_iris, requires_fhir, _mcp_config, USERS


pytestmark = [requires_iris, requires_fhir]

# QueryTable takes a single integer patientId; the ObjectScript prepends "Patient/" internally.
KNOWN_PATIENT_ID = 7
KNOWN_TABLE = "Observation"
NONEXISTENT_TABLE = "NoSuchTable"
KNOWN_SURNAME = "Larson"


def _parse_tool_result(raw) -> dict:
    text = ""
    if isinstance(raw, list):
        text = raw[0].get("text", "") if raw else ""
    elif isinstance(raw, str):
        text = raw
    else:
        text = str(raw)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"raw": text}


async def _doctor_tools():
    client = MultiServerMCPClient(_mcp_config(*USERS["doctor"]))
    tools = await client.get_tools()
    return {t.name: t for t in tools}


@pytest.mark.asyncio
async def test_list_tables_returns_afhrdata_tables():
    tools = await _doctor_tools()
    list_tables = next((t for name, t in tools.items() if "ListTables" in name), None)
    assert list_tables
    raw = await list_tables.ainvoke({})
    result = _parse_tool_result(raw)

    assert result.get("Status") in ("OK", 1, "$$$OK"), f"ListTables failed: {result}"
    tables_raw = result.get("Tables", "")
    tables = json.loads(tables_raw) if isinstance(tables_raw, str) and tables_raw else (tables_raw or [])
    table_names = {t["TABLE_NAME"] for t in tables}
    for expected in ("Observation", "Condition", "Patient", "DocumentReference"):
        assert expected in table_names, f"Expected {expected} in {table_names}"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="iris-mcp-server 2.0 WebSocket backchannel mismatch — tool invocation may fail", strict=False)
async def test_query_table_returns_rows_for_known_patient():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": KNOWN_TABLE, "patientId": KNOWN_PATIENT_ID})
    result = _parse_tool_result(raw)

    assert result.get("Status") == "OK", f"QueryTable failed: {result}"
    assert result.get("Table") == KNOWN_TABLE
    assert len(result.get("Rows", [])) > 0


@pytest.mark.asyncio
@pytest.mark.xfail(reason="iris-mcp-server 2.0 WebSocket backchannel mismatch — tool invocation may fail", strict=False)
async def test_query_table_nonexistent_table_returns_error():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": NONEXISTENT_TABLE, "patientId": KNOWN_PATIENT_ID})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "ERROR"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="iris-mcp-server 2.0 WebSocket backchannel mismatch — tool invocation may fail", strict=False)
async def test_find_patients_by_surname_returns_results():
    """FindPatientsBySurname is an inline SQL query in StandardToolSet — available to all roles."""
    tools = await _doctor_tools()
    find_patients = next((t for name, t in tools.items() if "FindPatientsBySurname" in name), None)
    assert find_patients, "FindPatientsBySurname missing from doctor tools"
    raw = await find_patients.ainvoke({"patientSurname": KNOWN_SURNAME})
    rows = _parse_tool_result(raw)
    # Returns a list directly (inline SQL query)
    assert isinstance(rows, list), f"Expected list from FindPatientsBySurname, got: {rows}"
    assert len(rows) > 0, "Expected at least one patient with surname Larson"


@pytest.mark.asyncio
async def test_tool_calls_are_audited(iris_conn_doctor):
    tools = await _doctor_tools()
    list_tables = next((t for name, t in tools.items() if "ListTables" in name), None)
    assert list_tables
    await list_tables.ainvoke({})

    cursor = iris_conn_doctor.cursor()
    cursor.execute("SELECT COUNT(*) FROM ReadyAI.ToolLog WHERE ToolName LIKE '%ListTables%'")
    row = cursor.fetchone()
    assert row[0] > 0, "Expected at least one ToolLog entry for ListTables"
