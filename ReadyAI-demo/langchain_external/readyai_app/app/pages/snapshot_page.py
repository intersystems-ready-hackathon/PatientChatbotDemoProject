import streamlit as st
from agent.get_patient_snapshot import PatientSnapshotAgent
import asyncio
st.set_page_config(page_title="Snapshot Page", page_icon="🩺", layout="centered")


USER = st.session_state.get("Username")
ROLES = st.session_state.get("Roles", [])

if not st.session_state.get("logged_in") or not USER:
    st.error("Please log in before generating a patient snapshot.")
    st.stop()

if "Doctor" not in ROLES and "Nurse" not in ROLES:
    st.error("You do not have access to the patient snapshot page.")
    st.stop()


st.title(f"Welcome {USER}")
st.subheader(f"Role: {', '.join(ROLES)}")
st.caption("Enter a patient identifier and generate a concise snapshot. The response will stream below as it is produced.")


patient_id = st.text_input("Enter the patient's name to begin generating a snapshot", value="John Doe", max_chars=50)



async def run_snapshot_gen(agent):
    chunks = []
    stream_placeholder = st.empty()
    snapshot_text = ""

    stream_placeholder.info("Waiting for the agent to return content...")

    async for chunk in agent.stream_response(f"Please generate a snapshot for patient {patient_id}"):
        chunk_text = str(chunk)
        chunks.append(chunk_text)
        snapshot_text += chunk_text

        stream_placeholder.markdown(
            f"""
            **Streaming response**

            {snapshot_text}
            """
        )

    return chunks

if patient_id:
    st.caption(f"Ready to generate a snapshot for patient {patient_id}.")

    if st.button("Generate Patient Snapshot", type="primary", use_container_width=True):
        agent = PatientSnapshotAgent(st.session_state["Username"], st.session_state["Password"])
        with st.spinner("Generating patient snapshot..."):
            snapshot_chunks = asyncio.run(run_snapshot_gen(agent))

        final_snapshot = "".join(snapshot_chunks).strip()
        if final_snapshot:
            st.success("Snapshot generated successfully.")
            st.text_area("Final snapshot", value=final_snapshot, height=240)
        else:
            st.info("The agent completed, but no snapshot text was returned.")
        
