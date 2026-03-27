import streamlit as st 
import iris
st.title("ReadyAI MCP Tool Discovery Demo")


st.session_state["Roles"]=[]

def login_page():
    st.header("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        
        try:
            conn = iris.connect('localhost', 1973, 'READYAI', username, password)
            st.success("Login successful!")

        except Exception as e:
            st.error(f"Login failed, do you have the right credentials? ({e})")
            return -1
        irispy = iris.createIRIS(conn)
        roles = irispy.classMethodValue("Utils.GetRoles", "GetRoles")
        conn.close()
            

        st.session_state["Username"] = username
        st.session_state["Password"] = password
        st.session_state["Roles"] = roles
        return roles
    
login_page()

if "Doctor" in st.session_state["Roles"]:
    st.switch_page("pages/DoctorPage.py")
elif "Nurse" in st.session_state["Roles"]:
    st.switch_page("pages/NursePage.py")