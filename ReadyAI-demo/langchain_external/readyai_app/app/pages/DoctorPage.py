import streamlit as st
from agent.get_patient_snapshot import PatientSnapshotAgent

st.title("Welcome Doctor")


patient_id = st.number_input("Enter patient ID to generate snapshot", value=0)


async def run_snapshot_gen(agent):
    async for chunk in agent.stream_response(f"Please generate a snapshot for patient {patient_id}"):
        st.write(chunk, end="", flush=True)

if patient_id: 
    if st.button("Generate Patient Snapshot"):
        agent = PatientSnapshotAgent(st.session_state["Username"], st.session_state["Password"])
        asyncio.run(run_snapshot_gen(agent))
