import os
import streamlit as st
import iris

_IRIS_HOST = os.environ.get("IRIS_HOST", "iris")
_IRIS_PORT = int(os.environ.get("IRIS_PORT", "1972"))
_IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")

st.title("ReadyAI — Patient Encounter Briefing")

st.session_state.setdefault("Roles", [])


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
            roles = irispy.classMethodValue("Utils.GetRoles", "GetRoles")
        except Exception as e:
            st.error(f"Login failed: {e}")
            return
        finally:
            if conn is not None:
                conn.close()

        st.session_state["Username"] = username
        st.session_state["Password"] = password
        st.session_state["Roles"] = roles
        st.success("Login successful!")


login_page()

if "Doctor" in st.session_state["Roles"]:
    st.switch_page("pages/DoctorPage.py")
elif "Nurse" in st.session_state["Roles"]:
    st.switch_page("pages/NursePage.py")
