import json

import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient
from tests.conftest import requires_iris, requires_fhir, _mcp_config, USERS


pytestmark = [requires_iris, requires_fhir]

KNOWN_PATIENT_ID = "Patient/7"
KNOWN_TABLE = "Observation"
NONEXISTENT_TABLE = "NoSuchTable"


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
@pytest.mark.xfail(reason="Corrupt UTF-8 in IRIS response via iris-mcp-server 2.0 WebSocket backchannel", strict=False)
async def test_query_table_returns_rows_for_known_patient():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": KNOWN_TABLE, "patientIds": [KNOWN_PATIENT_ID]})
    result = _parse_tool_result(raw)

    assert result.get("Status") == "OK", f"QueryTable failed: {result}"
    assert result.get("Table") == KNOWN_TABLE
    assert len(result.get("Rows", [])) > 0


@pytest.mark.asyncio
async def test_query_table_empty_patient_list_returns_ok():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": KNOWN_TABLE, "patientIds": []})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "OK"
    assert result.get("Rows") in ([], None)


@pytest.mark.asyncio
async def test_query_table_nonexistent_table_returns_error():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": NONEXISTENT_TABLE, "patientIds": [KNOWN_PATIENT_ID]})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "ERROR"


@pytest.mark.asyncio
async def test_query_table_multiple_patients():
    tools = await _doctor_tools()
    query_table = next((t for name, t in tools.items() if "QueryTable" in name), None)
    assert query_table
    raw = await query_table.ainvoke({"tableName": KNOWN_TABLE, "patientIds": ["Patient/1", "Patient/2"]})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "OK"
    assert isinstance(result.get("Rows", []), list)


@pytest.mark.asyncio
async def test_get_conditions_list_returns_snomed_entries():
    tools = await _doctor_tools()
    get_conditions = next((t for name, t in tools.items() if "GetConditionsList" in name), None)
    assert get_conditions
    raw = await get_conditions.ainvoke({})
    result = _parse_tool_result(raw)

    assert result.get("Status") == "OK", f"GetConditionsList failed: {result}"
    conditions = result.get("Conditions", [])
    assert len(conditions) > 0
    assert "Code" in conditions[0]
    assert "Description" in conditions[0]


@pytest.mark.asyncio
@pytest.mark.xfail(reason="iris-mcp-server 2.0/mcp 1.26 WebSocket backchannel mismatch on tool invocation", strict=False)
async def test_get_patients_by_condition_known_code():
    tools = await _doctor_tools()
    get_conditions = next((t for name, t in tools.items() if "GetConditionsList" in name), None)
    get_patients = next((t for name, t in tools.items() if "GetPatientsByCondition" in name), None)
    assert get_conditions and get_patients

    conditions_raw = await get_conditions.ainvoke({})
    conditions = _parse_tool_result(conditions_raw)
    first_code = conditions["Conditions"][0]["Code"]

    raw = await get_patients.ainvoke({"pConditionCode": first_code})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "OK"
    patients = result.get("Patients", [])
    assert len(patients) > 0
    assert all(p.startswith("Patient/") for p in patients)


@pytest.mark.asyncio
async def test_get_patients_by_condition_unknown_code_returns_empty():
    tools = await _doctor_tools()
    get_patients = next((t for name, t in tools.items() if "GetPatientsByCondition" in name), None)
    assert get_patients
    raw = await get_patients.ainvoke({"pConditionCode": 9999999999})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "OK"
    assert result.get("Patients") == []


@pytest.mark.asyncio
async def test_get_patients_by_condition_missing_code_returns_error():
    tools = await _doctor_tools()
    get_patients = next((t for name, t in tools.items() if "GetPatientsByCondition" in name), None)
    assert get_patients
    raw = await get_patients.ainvoke({"pConditionCode": ""})
    result = _parse_tool_result(raw)
    assert result.get("Status") == "ERROR"
    assert "required" in result.get("Error", "").lower()


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
