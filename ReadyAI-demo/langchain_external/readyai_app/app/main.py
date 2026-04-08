import streamlit as st


def _init_session_state():
    st.session_state.setdefault("Username", "")
    st.session_state.setdefault("Password", "")
    st.session_state.setdefault("Roles", [])
    st.session_state.setdefault("logged_in", False)


_init_session_state()

_LOGIN_PAGE = st.Page("pages/login_page.py", title="Login", icon="🩺", default=True)
_SNAPSHOT_PAGE = st.Page("pages/snapshot_page.py", title="Snapshot Chat", icon="💬")

st.navigation([_LOGIN_PAGE, _SNAPSHOT_PAGE], position="hidden").run()