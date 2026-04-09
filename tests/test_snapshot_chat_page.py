import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch


_APP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ReadyAI-demo", "langchain_external", "readyai_app", "app"
)
_SNAPSHOT_PAGE_PY = os.path.join(_APP_PATH, "pages", "snapshot_page.py")


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


class TestSnapshotChatPage:
    def test_chat_page_renders_greeting_and_controls(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            yield "stub"

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()

        assert not at.exception
        assert at.text_input[0].label == "Patient name"
        assert at.text_input[0].value == "Stewart Larson"
        button_labels = [button.label for button in at.button]
        assert "New chat" in button_labels
        assert "Log out" in button_labels
        assert "What tools do you have?" in button_labels
        assert "Give me a concise snapshot for Stewart Larson." in button_labels
        markdown_output = " ".join(str(item.value) for item in at.markdown)
        assert "Snapshot Chat" in markdown_output
        assert "Ask for a patient snapshot" in markdown_output

    def test_suggested_prompt_button_starts_chat(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            assert "Give me a concise snapshot for Stewart Larson." in prompt
            assert "The active patient is Stewart Larson." in prompt
            yield "Stewart Larson summary"

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()

            prompt_index = [button.label for button in at.button].index("Give me a concise snapshot for Stewart Larson.")
            at.button[prompt_index].click().run()

        history = at.session_state["snapshot_chat_messages"]
        assert history[1]["role"] == "user"
        assert history[1]["content"] == "Give me a concise snapshot for Stewart Larson."
        assert history[2]["role"] == "assistant"
        assert history[2]["content"] == "Stewart Larson summary"

    def test_chat_page_streams_response_and_saves_history(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            assert "Summarize Jane Doe" in prompt
            assert "The active patient is Stewart Larson." in prompt
            for chunk in ["Jane Doe is ", "clinically stable."]:
                yield chunk

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()
            at.chat_input[0].set_value("Summarize Jane Doe").run()

        history = at.session_state["snapshot_chat_messages"]
        assert history[1]["role"] == "user"
        assert history[1]["content"] == "Summarize Jane Doe"
        assert history[2]["role"] == "assistant"
        assert history[2]["content"] == "Jane Doe is clinically stable."

    def test_chat_page_shows_tool_activity(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            yield {"type": "tool_call", "id": "call-1", "name": "EchoUser", "status": "running", "args": '{"patient":"Stewart Larson"}'}
            yield {"type": "tool_result", "id": "call-1", "name": "EchoUser", "status": "success", "content": '{"Roles":"Doctor"}'}
            yield "Tool summary here."

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()
            at.button[[button.label for button in at.button].index("What tools do you have?")].click().run()

        markdown_output = " ".join(str(item.value) for item in at.markdown)
        assert "Tool activity" in markdown_output
        assert len(at.expander) == 1
        assert at.expander[0].label == "EchoUser - Completed"
        assert len(at.json) == 2
        json_values = [item.value for item in at.json]
        assert '{"patient": "Stewart Larson"}' in json_values
        assert '{"Roles": "Doctor"}' in json_values

    def test_blank_patient_name_blocks_chat(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            yield "stub"

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            at = at.run()
            at.text_input[0].set_value(" ").run()

        assert len(at.info) > 0
        assert "Enter a patient name" in str(at.info[0].value)
        assert len(at.chat_input) == 0

    def test_logout_clears_session_and_redirects_home(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            yield "stub"

        agent_instance = MagicMock()
        agent_instance.stream_response = _fake_stream

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=agent_instance)

        with patch("streamlit.switch_page") as switch_page_mock:
            with _patched_page_modules(mock_agent_module):
                at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
                at.session_state["Username"] = "DScully"
                at.session_state["Password"] = "XFiles"
                at.session_state["Roles"] = ["Doctor"]
                at.session_state["logged_in"] = True
                at.session_state["snapshot_chat_messages"] = [
                    {"role": "assistant", "content": "Hello."},
                    {"role": "user", "content": "Prior question"},
                ]
                at = at.run()

                logout_index = [button.label for button in at.button].index("Log out")
                at.button[logout_index].click().run()

        assert at.session_state["Username"] == ""
        assert at.session_state["Password"] == ""
        assert at.session_state["Roles"] == []
        assert at.session_state["logged_in"] is False
        assert "snapshot_chat_messages" not in at.session_state
        switch_page_mock.assert_called_once_with("pages/login_page.py")