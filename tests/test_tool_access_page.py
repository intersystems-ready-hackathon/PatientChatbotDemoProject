import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch


_APP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ReadyAI-demo", "langchain_external", "readyai_app", "app"
)
_TOOLS_ACCESS_PAGE_PY = os.path.join(_APP_PATH, "pages", "tools_access_page.py")


@contextmanager
def _patched_page_modules(mock_agent_module):
    inserted_path = False
    if _APP_PATH not in sys.path:
        sys.path.insert(0, _APP_PATH)
        inserted_path = True
    try:
        with patch.dict(
            "sys.modules",
            {
                "agent": MagicMock(get_patient_snapshot=mock_agent_module),
                "agent.get_patient_snapshot": mock_agent_module,
            },
        ):
            yield
    finally:
        if inserted_path:
            sys.path.remove(_APP_PATH)


class TestToolAccessPage:
    def test_tool_access_page_streams_agent_response(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_build_prompt():
            return "Tell me what tools you can access."

        async def _fake_stream(prompt):
            assert "tools" in prompt.lower()
            for chunk in ["You can use ", "EchoUser", " and SQLTools."]:
                yield chunk

        agent_instance = MagicMock()
        agent_instance.build_tools_access_prompt = _fake_build_prompt
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_TOOLS_ACCESS_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()

        assert not at.exception
        assert "EchoUser" in at.session_state["tool_access_response"]
        assert "SQLTools" in at.session_state["tool_access_response"]

    def test_tool_access_page_has_refresh_button(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_build_prompt():
            return "Tell me what tools you can access."

        async def _fake_stream(prompt):
            yield "EchoUser"

        agent_instance = MagicMock()
        agent_instance.build_tools_access_prompt = _fake_build_prompt
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_TOOLS_ACCESS_PAGE_PY)
            at.session_state["Username"] = "NJoy"
            at.session_state["Password"] = "pokemon"
            at.session_state["Roles"] = ["Nurse"]
            at.session_state["logged_in"] = True
            at = at.run()

        labels = [button.label for button in at.button]
        assert "Refresh Tool Access" in labels