import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain.agents.middleware import ToolCallRequest
from langchain_core.messages import ToolMessage
from tests.conftest import requires_iris, USERS

_APP_PATH = os.path.join(os.path.dirname(__file__), "..", "ReadyAI-demo", "langchain_external", "readyai_app", "app")


def _ensure_app_on_path():
    if _APP_PATH not in sys.path:
        sys.path.insert(0, _APP_PATH)


@pytest.fixture(autouse=True)
def _app_on_path():
    _ensure_app_on_path()


class TestPatientSnapshotAgentUnit:
    def test_init_stores_credentials(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent

        agent = PatientSnapshotAgent("DScully", "XFiles")
        assert agent.username == "DScully"
        assert agent.password == "XFiles"

    def test_system_prompt_mentions_roles(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent

        agent = PatientSnapshotAgent("DScully", "XFiles")
        assert "Doctor" in agent.SYSTEM_PROMPT
        assert "Nurse" in agent.SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_get_tools_builds_basic_auth_header(self):
        mock_tools = [MagicMock(name="mcp_readyai_ListTables")]
        mock_client = MagicMock()
        mock_client.get_tools = AsyncMock(return_value=mock_tools)

        with patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_client) as mock_cls:
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            tools = await agent.get_tools()

            call_kwargs = mock_cls.call_args[0][0]
            auth_header = call_kwargs["readyai"]["headers"]["Authorization"]
            assert auth_header.startswith("Basic ")
            import base64
            decoded = base64.b64decode(auth_header[6:]).decode()
            assert decoded == "DScully:XFiles"

        assert tools == mock_tools

    @pytest.mark.asyncio
    async def test_get_snapshot_agent_calls_init_chat_model_with_conn(self):
        mock_model = MagicMock()
        mock_tools = [MagicMock()]
        mock_mcp_client = MagicMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=mock_tools)
        mock_conn = MagicMock()
        mock_iris = MagicMock()
        mock_iris.connect.return_value = mock_conn

        with patch("agent.get_patient_snapshot.iris", mock_iris), \
             patch("agent.get_patient_snapshot.init_chat_model", return_value=mock_model) as mock_icm, \
             patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_mcp_client), \
             patch("agent.get_patient_snapshot.create_agent") as mock_create:
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            await agent.get_snapshot_agent()

            mock_icm.assert_called_once()
            assert mock_icm.call_args[0][1] is mock_conn, "init_chat_model must be called with the IRIS connection"

    @pytest.mark.asyncio
    async def test_get_snapshot_agent_passes_tools_to_create_agent(self):
        mock_model = MagicMock()
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_mcp_client = MagicMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=mock_tools)

        with patch("agent.get_patient_snapshot.iris"), \
             patch("agent.get_patient_snapshot.init_chat_model", return_value=mock_model), \
             patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_mcp_client), \
             patch("agent.get_patient_snapshot.create_agent") as mock_create:
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            await agent.get_snapshot_agent()

            mock_create.assert_called_once()
            create_kwargs = mock_create.call_args
            passed_tools = create_kwargs[1].get("tools") if create_kwargs[1] else (create_kwargs[0][1] if len(create_kwargs[0]) > 1 else None)
            assert passed_tools == mock_tools
            assert create_kwargs[1]["middleware"], "Tool error middleware should be registered"

    @pytest.mark.asyncio
    async def test_get_snapshot_agent_closes_iris_connection(self):
        mock_conn = MagicMock()
        mock_iris = MagicMock()
        mock_iris.connect.return_value = mock_conn
        mock_mcp_client = MagicMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=[])

        with patch("agent.get_patient_snapshot.iris", mock_iris), \
             patch("agent.get_patient_snapshot.init_chat_model"), \
             patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_mcp_client), \
             patch("agent.get_patient_snapshot.create_agent"):
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            await agent.get_snapshot_agent()

        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_response_yields_text_chunks(self):
        async def fake_astream(*args, **kwargs):
            for text in ["Patient ", "summary ", "here."]:
                msg = MagicMock()
                msg.type = "ai"
                msg.content_blocks = [{"type": "text", "text": text}]
                yield msg, {}

        mock_agent = MagicMock()
        mock_agent.astream = fake_astream

        mock_mcp_client = MagicMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=[])

        with patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_mcp_client), \
             patch("agent.get_patient_snapshot.init_chat_model"), \
             patch("agent.get_patient_snapshot.create_agent", return_value=mock_agent), \
             patch("agent.get_patient_snapshot.iris"):
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            chunks = []
            async for chunk in agent.stream_response("Summarize patient 1"):
                chunks.append(chunk)

        assert chunks == ["Patient ", "summary ", "here."]

    @pytest.mark.asyncio
    async def test_stream_response_skips_non_text_blocks(self):
        async def fake_astream(*args, **kwargs):
            msg = MagicMock()
            msg.type = "ai"
            msg.content_blocks = [
                {"type": "tool_use", "id": "abc"},
                {"type": "text", "text": "Final answer."},
            ]
            yield msg, {}

        mock_agent = MagicMock()
        mock_agent.astream = fake_astream

        mock_mcp_client = MagicMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=[])

        with patch("agent.get_patient_snapshot.MultiServerMCPClient", return_value=mock_mcp_client), \
             patch("agent.get_patient_snapshot.init_chat_model"), \
             patch("agent.get_patient_snapshot.create_agent", return_value=mock_agent), \
             patch("agent.get_patient_snapshot.iris"):
            from agent.get_patient_snapshot import PatientSnapshotAgent

            agent = PatientSnapshotAgent("DScully", "XFiles")
            chunks = [c async for c in agent.stream_response("test")]

        assert chunks == ["Final answer."]

    @pytest.mark.asyncio
    async def test_tool_error_middleware_returns_error_tool_message(self):
        from agent.get_patient_snapshot import _handle_tool_call_error

        request = ToolCallRequest(
            tool_call={"id": "call-123", "name": "mcp_readyai_QueryTable", "args": {"patientId": 1}},
            tool=None,
            state={},
            runtime=MagicMock(),
        )

        async def _failing_handler(_request):
            raise RuntimeError("database unavailable")

        result = await _handle_tool_call_error.awrap_tool_call(request, _failing_handler)

        assert isinstance(result, ToolMessage)
        assert result.status == "error"
        assert result.tool_call_id == "call-123"
        assert "mcp_readyai_QueryTable" in result.content
        assert "RuntimeError: database unavailable" in result.content

    @pytest.mark.asyncio
    async def test_stream_response_formats_exception_group_details(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent

        agent = PatientSnapshotAgent("DScully", "XFiles")

        with patch.object(
            agent,
            "get_snapshot_agent",
            AsyncMock(side_effect=ExceptionGroup("unhandled errors in a TaskGroup", [ConnectionError("name resolution failed")])),
        ):
            chunks = [chunk async for chunk in agent.stream_response("test")]

        assert len(chunks) == 1
        assert "ConnectionError: name resolution failed" in chunks[0]


@requires_iris
class TestPatientSnapshotAgentE2E:
    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Requires OPENAI_API_KEY and a live LLM — set env var to run",
        strict=False,
    )
    async def test_stream_response_doctor_produces_output(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent

        username, password = USERS["doctor"]
        agent = PatientSnapshotAgent(username, password)
        chunks = []
        async for chunk in agent.stream_response("What tools do you have?"):
            chunks.append(chunk)

        assert len(chunks) > 0, "Agent should produce at least one text chunk"
        full_response = "".join(chunks)
        assert len(full_response) > 10, f"Response too short: {full_response!r}"

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Requires OPENAI_API_KEY, live LLM, and FHIR data loaded",
        strict=False,
    )
    async def test_stream_response_doctor_real_patient_snapshot(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent

        username, password = USERS["doctor"]
        agent = PatientSnapshotAgent(username, password)
        chunks = []
        async for chunk in agent.stream_response("Please generate a snapshot for patient Patient/7"):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert len(full_response) > 50, f"Expected substantive patient summary, got: {full_response!r}"
        assert any(word in full_response.lower() for word in ("patient", "observation", "condition", "synthia", "schinner")), (
            f"Expected patient details in response, got: {full_response[:300]!r}"
        )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Requires OPENAI_API_KEY and live LLM",
        strict=False,
    )
    async def test_init_chat_model_used_not_hardcoded_provider(self):
        from agent.get_patient_snapshot import PatientSnapshotAgent
        from langchain_intersystems.chat_models import init_chat_model as real_init_chat_model

        call_log = []

        def tracking_init_chat_model(config_name, conn):
            call_log.append({"config_name": config_name, "conn": conn})
            return real_init_chat_model(config_name, conn)

        username, password = USERS["doctor"]

        with patch("agent.get_patient_snapshot.init_chat_model", side_effect=tracking_init_chat_model):
            agent = PatientSnapshotAgent(username, password)
            await agent.get_snapshot_agent()

        assert len(call_log) == 1, "init_chat_model should be called exactly once"
        assert call_log[0]["config_name"] == "readyai", (
            f"Expected LLM_CONFIG_NAME='readyai', got {call_log[0]['config_name']!r}"
        )
        assert call_log[0]["conn"] is not None, "init_chat_model must receive an IRIS connection"
