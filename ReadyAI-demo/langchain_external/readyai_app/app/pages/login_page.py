import os

import iris
import streamlit as st


IRIS_HOST = os.environ.get("IRIS_HOST", "iris")
IRIS_PORT = int(os.environ.get("IRIS_PORT", "1972"))
IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")


st.set_page_config(page_title="ReadyAI Login", page_icon="🩺", layout="centered")

st.session_state.setdefault("Username", "")
st.session_state.setdefault("Password", "")
st.session_state.setdefault("Roles", [])
st.session_state.setdefault("logged_in", False)

st.title("ReadyAI — Patient Encounter Briefing")

if st.session_state["logged_in"] and (
    "Doctor" in st.session_state["Roles"] or "Nurse" in st.session_state["Roles"]
):
    st.switch_page("pages/snapshot_page.py")

st.header("Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    conn = None
    try:
        conn = iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, username, password)
        irispy = iris.createIRIS(conn)
        user_info = irispy.classMethodValue("Utils.EchoUser", "EchoUser")

        raw_roles = user_info.get("Roles") if isinstance(user_info, dict) else ""
        if isinstance(raw_roles, str):
            roles = [role.strip() for role in raw_roles.split(",") if role.strip()]
        else:
            roles = [str(role).strip() for role in raw_roles if str(role).strip()]
    except Exception as exc:
        st.session_state["Username"] = ""
        st.session_state["Password"] = ""
        st.session_state["Roles"] = []
        st.session_state["logged_in"] = False
        st.error(f"Login failed: {exc}")
    else:
        st.session_state["Username"] = username
        st.session_state["Password"] = password
        st.session_state["Roles"] = roles
        st.session_state["logged_in"] = bool(roles)

        if "Doctor" in roles or "Nurse" in roles:
            st.switch_page("pages/snapshot_page.py")

        st.warning(f"Logged in as {username} with roles: {', '.join(roles)}.")
        st.warning("You do not have access to the patient snapshot feature. Talk to your administrator if you think this is an error.")
        if st.button("Log out"):
            st.session_state["Username"] = ""
            st.session_state["Password"] = ""
            st.session_state["Roles"] = []
            st.session_state["logged_in"] = False
            st.rerun()
    finally:
        if conn is not None:
            conn.close()