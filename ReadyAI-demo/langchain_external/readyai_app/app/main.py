import os
import streamlit as st
import iris

_IRIS_HOST = os.environ.get("IRIS_HOST", "iris")
_IRIS_PORT = int(os.environ.get("IRIS_PORT", "1972"))
_IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")


def _normalize_roles(raw_roles):
    if isinstance(raw_roles, str):
        return [role.strip() for role in raw_roles.split(",") if role.strip()]
    if isinstance(raw_roles, (list, tuple, set)):
        return [str(role).strip() for role in raw_roles if str(role).strip()]
    return []


def _init_session_state():
    st.session_state.setdefault("Username", "")
    st.session_state.setdefault("Password", "")
    st.session_state.setdefault("Roles", [])
    st.session_state.setdefault("logged_in", False)


def _clear_login_state():
    st.session_state["Username"] = ""
    st.session_state["Password"] = ""
    st.session_state["Roles"] = []
    st.session_state["logged_in"] = False


_init_session_state()

_SNAPSHOT_PAGE = st.Page("pages/snapshot_page.py", title="Patient Snapshot")

st.title("ReadyAI — Patient Encounter Briefing")


def login_page():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        conn = None
        try:
            conn = iris.connect(_IRIS_HOST, _IRIS_PORT, _IRIS_NAMESPACE, username, password)
            irispy = iris.createIRIS(conn)
            user_info = irispy.classMethodValue("Utils.EchoUser", "EchoUser")
            roles = _normalize_roles(user_info.get("Roles", ""))
        except Exception as e:
            _clear_login_state()
            st.error(f"Login failed: {e}")
            return
        finally:
            if conn is not None:
                conn.close()

        st.session_state["Username"] = username
        st.session_state["Password"] = password
        st.session_state["Roles"] = roles
        st.session_state["logged_in"] = bool(roles)
        st.success("Login successful!")
        st.rerun()


if st.session_state["logged_in"] and "Doctor" in st.session_state["Roles"]:
    st.navigation([_SNAPSHOT_PAGE], position="hidden").run()
else:
    login_page()

if st.session_state["logged_in"] and "Doctor" not in st.session_state["Roles"]:
    st.warning(f"Logged in as {st.session_state['Username']} with roles: {', '.join(st.session_state['Roles'])}.")
    st.warning("You do not have access to the patient snapshot feature. Talk to your administrator if you think this is an error.")
    if st.button("Log out"):
        _clear_login_state()
        st.rerun()