import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

_APP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ReadyAI-demo", "langchain_external", "readyai_app", "app"
)
_MAIN_PY = os.path.join(_APP_PATH, "main.py")
_SNAPSHOT_PAGE_PY = os.path.join(_APP_PATH, "pages", "snapshot_page.py")


def _make_iris_mock(roles: str, fail: bool = False):
    mock_conn = MagicMock()
    mock_irispy = MagicMock()
    mock_irispy.classMethodValue.return_value = roles

    def _connect(*args, **kwargs):
        if fail:
            raise ConnectionError("bad credentials")
        return mock_conn

    return _connect, mock_irispy, mock_conn


def _iris_module_for_roles(roles: str, fail: bool = False):
    connect_fn, mock_irispy, _ = _make_iris_mock(roles, fail=fail)
    return MagicMock(connect=connect_fn, createIRIS=lambda c: mock_irispy)


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
                "iris": MagicMock(),
                "langchain_intersystems": MagicMock(),
                "langchain_mcp_adapters": MagicMock(),
                "langchain_mcp_adapters.client": MagicMock(),
                "agent": MagicMock(get_patient_snapshot=mock_agent_module),
                "agent.get_patient_snapshot": mock_agent_module,
            },
        ):
            yield
    finally:
        if inserted_path:
            sys.path.remove(_APP_PATH)


class TestLoginPage:
    def test_login_page_renders_title(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("Doctor")}):
            at = AppTest.from_file(_MAIN_PY).run()

        assert not at.exception
        assert any("ReadyAI" in str(t.value) for t in at.title)

    def test_login_page_renders_login_header(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("Doctor")}):
            at = AppTest.from_file(_MAIN_PY).run()

        assert any("Login" in str(h.value) for h in at.header)

    def test_login_page_has_username_and_password_inputs(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("Doctor")}):
            at = AppTest.from_file(_MAIN_PY).run()

        labels = [ti.label for ti in at.text_input]
        assert "Username" in labels
        assert "Password" in labels

    def test_successful_doctor_login_sets_session_state(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("Doctor,%DB_READYAI,%SQL")}):
            at = AppTest.from_file(_MAIN_PY).run()
            at.text_input[0].set_value("DScully").run()
            at.text_input[1].set_value("XFiles").run()
            at.button[0].click().run()

        assert at.session_state["Username"] == "DScully"
        assert at.session_state["Password"] == "XFiles"
        assert "Doctor" in at.session_state["Roles"]

    def test_successful_nurse_login_sets_session_state(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("Nurse,%DB_READYAI,%SQL")}):
            at = AppTest.from_file(_MAIN_PY).run()
            at.text_input[0].set_value("NJoy").run()
            at.text_input[1].set_value("pokemon").run()
            at.button[0].click().run()

        assert "Nurse" in at.session_state["Roles"]

    def test_failed_login_shows_error(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("", fail=True)}):
            at = AppTest.from_file(_MAIN_PY).run()
            at.text_input[0].set_value("nobody").run()
            at.text_input[1].set_value("wrongpassword").run()
            at.button[0].click().run()

        assert len(at.error) > 0
        assert any("Login failed" in str(e.value) for e in at.error)

    def test_failed_login_does_not_set_roles(self):
        from streamlit.testing.v1 import AppTest

        with patch.dict("sys.modules", {"iris": _iris_module_for_roles("", fail=True)}):
            at = AppTest.from_file(_MAIN_PY).run()
            at.text_input[0].set_value("nobody").run()
            at.text_input[1].set_value("wrong").run()
            at.button[0].click().run()

        roles = at.session_state.get("Roles") if hasattr(at.session_state, "get") else at.session_state["Roles"] if "Roles" in at.session_state else []
        assert "Doctor" not in roles
        assert "Nurse" not in roles


class TestDoctorSnapshotPage:
    """Smoke tests for snapshot_page.py with Doctor role session state."""

    def _at(self, snapshot_chunks=None):
        from streamlit.testing.v1 import AppTest

        chunks = snapshot_chunks or ["Patient summary here."]

        async def _fake_stream(prompt):
            for c in chunks:
                yield c

        instance = MagicMock()
        instance.stream_response = _fake_stream
        agent_cls_mock = MagicMock(return_value=instance)

        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = agent_cls_mock

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "DScully"
            at.session_state["Password"] = "XFiles"
            at.session_state["Roles"] = ["Doctor"]
            at.session_state["logged_in"] = True
            return at.run()

    def test_doctor_snapshot_page_renders_without_exception(self):
        at = self._at()
        assert not at.exception

    def test_doctor_snapshot_page_has_patient_name_input(self):
        at = self._at()
        assert len(at.text_input) > 0
        assert at.text_input[0].label == "Patient name"

    def test_doctor_snapshot_page_has_new_chat_and_logout_buttons(self):
        at = self._at()
        labels = [b.label for b in at.button]
        assert "New chat" in labels
        assert "Log out" in labels

    def test_doctor_snapshot_page_shows_suggested_prompts(self):
        at = self._at()
        labels = [b.label for b in at.button]
        assert any("snapshot" in lbl.lower() or "tools" in lbl.lower() for lbl in labels)


class TestNurseSnapshotPage:
    """Smoke tests for snapshot_page.py with Nurse role session state."""

    def _at(self):
        from streamlit.testing.v1 import AppTest

        async def _fake_stream(prompt):
            yield "Nurse response."

        instance = MagicMock()
        instance.stream_response = _fake_stream
        mock_agent_module = MagicMock()
        mock_agent_module.PatientSnapshotAgent = MagicMock(return_value=instance)

        with _patched_page_modules(mock_agent_module):
            at = AppTest.from_file(_SNAPSHOT_PAGE_PY)
            at.session_state["Username"] = "NJoy"
            at.session_state["Password"] = "pokemon"
            at.session_state["Roles"] = ["Nurse"]
            at.session_state["logged_in"] = True
            return at.run()

    def test_nurse_snapshot_page_renders_without_exception(self):
        at = self._at()
        assert not at.exception

    def test_nurse_snapshot_page_has_patient_name_input(self):
        at = self._at()
        assert len(at.text_input) > 0
        assert at.text_input[0].label == "Patient name"
