import asyncio
import os
import iris
import streamlit as st
from agent.get_patient_snapshot import PatientSnapshotAgent

_IRIS_HOST = os.environ.get("IRIS_HOST", "iris")
_IRIS_PORT = int(os.environ.get("IRIS_PORT", "1972"))
_IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")

st.title("Welcome Doctor")


@st.cache_data(ttl=300)
def load_patients(username, password):
    conn = None
    try:
        conn = iris.connect(_IRIS_HOST, _IRIS_PORT, _IRIS_NAMESPACE, username, password)
        cur = conn.cursor()
        cur.execute("SELECT ID, GivenName, FamilyName FROM AFHIRData.Patient ORDER BY FamilyName, GivenName")
        rows = cur.fetchall()
        return [{"id": f"Patient/{r[0]}", "label": f"Patient/{r[0]} — {r[1]} {r[2]}"} for r in rows]
    except Exception:
        return []
    finally:
        if conn is not None:
            conn.close()


username = st.session_state.get("Username", "")
password = st.session_state.get("Password", "")
patients = load_patients(username, password)

if patients:
    labels = [p["label"] for p in patients]
    selected = st.selectbox("Select patient", labels)
    default_id = next(p["id"] for p in patients if p["label"] == selected)
else:
    default_id = ""

patient_id = st.text_input("Or enter patient ID directly", value=default_id)

if patient_id and st.button("Generate Patient Snapshot"):
    agent = PatientSnapshotAgent(username, password)

    async def _collect():
        return [c async for c in agent.stream_response(f"Please generate a snapshot for patient {patient_id}")]

    chunks = asyncio.run(_collect())
    st.write("".join(chunks))
