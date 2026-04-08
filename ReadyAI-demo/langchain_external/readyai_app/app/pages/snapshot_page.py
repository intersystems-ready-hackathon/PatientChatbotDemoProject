import asyncio
import streamlit as st

from agent.get_patient_snapshot import PatientSnapshotAgent

st.set_page_config(page_title="Snapshot Chat", page_icon="💬", layout="wide")

CHAT_STATE_KEY = "snapshot_chat_messages"
PENDING_PROMPT_KEY = "snapshot_pending_prompt"
PATIENT_NAME_KEY = "snapshot_patient_name"
SUGGESTED_PROMPT_TEMPLATES = [
    "What tools do you have?",
    "Give me a concise snapshot for {patient_name}.",
    "What are the most important recent labs for {patient_name}?",
    "Summarize active problems and likely next steps for {patient_name}.",
]
DEFAULT_GREETING = (
    "Hello. Ask for a patient snapshot, recent clinical context, or a concise follow-up summary."
)


USER = st.session_state.get("Username")
ROLES = st.session_state.get("Roles", [])

if not st.session_state.get("logged_in") or not USER:
    st.error("Please log in before generating a patient snapshot.")
    st.stop()

if "Doctor" not in ROLES and "Nurse" not in ROLES:
    st.error("You do not have access to the patient snapshot page.")
    st.stop()


async def _stream_reply(prompt: str, placeholder) -> str:
    chunks = []
    agent = PatientSnapshotAgent(st.session_state["Username"], st.session_state["Password"])
    async for chunk in agent.stream_response(prompt):
        chunk_text = str(chunk)
        chunks.append(chunk_text)
        placeholder.markdown("".join(chunks) + "▌")

    final_text = "".join(chunks).strip()
    if final_text:
        placeholder.markdown(final_text)
        return final_text

    fallback = "I could not generate a response from the snapshot agent."
    placeholder.markdown(fallback)
    return fallback


st.session_state.setdefault(
    CHAT_STATE_KEY,
    [{"role": "assistant", "content": DEFAULT_GREETING}],
)
st.session_state.setdefault(PATIENT_NAME_KEY, "Stewart Larson")

st.markdown(
    """
    <style>
    .chat-shell {
        padding: 1.25rem 1.4rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
        margin-bottom: 1rem;
    }
    .chat-shell h1 {
        margin: 0;
        font-size: 2rem;
    }
    .chat-shell p {
        margin: 0.4rem 0 0;
        color: #475569;
    }
    .suggested-prompts-label {
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #64748b;
        margin: 0.35rem 0 0.6rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.caption(f"Signed in as {USER}")
    st.caption(f"Role: {', '.join(ROLES)}")
    if st.button("New chat", use_container_width=True):
        st.session_state[CHAT_STATE_KEY] = [{"role": "assistant", "content": DEFAULT_GREETING}]
        st.rerun()
    if st.button("Log out", type="primary", use_container_width=True):
        st.session_state["Username"] = ""
        st.session_state["Password"] = ""
        st.session_state["Roles"] = []
        st.session_state["logged_in"] = False
        st.session_state.pop(CHAT_STATE_KEY, None)
        st.session_state.pop(PENDING_PROMPT_KEY, None)
        st.switch_page("pages/login_page.py")

st.markdown(
    f"""
    <div class="chat-shell">
        <h1>{USER}'s Snapshot Chat</h1>
        <p>Use the snapshot agent for patient briefs, quick follow-up questions, and concise handoff support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

patient_name = st.text_input(
    "Patient name",
    key=PATIENT_NAME_KEY,
    help="Enter a patient name to unlock the snapshot chat.",
)

if not patient_name.strip():
    st.info("Enter a patient name to start the snapshot chat.")
    st.stop()

suggested_prompts = [
    template.format(patient_name=patient_name.strip()) for template in SUGGESTED_PROMPT_TEMPLATES
]

st.markdown('<div class="suggested-prompts-label">Suggested prompts</div>', unsafe_allow_html=True)
prompt_columns = st.columns(len(suggested_prompts))
selected_prompt = None
for column, suggested_prompt in zip(prompt_columns, suggested_prompts):
    if column.button(
        suggested_prompt,
        key=f"suggested_prompt_{suggested_prompt}",
        use_container_width=True,
    ):
        selected_prompt = suggested_prompt

for message in st.session_state[CHAT_STATE_KEY]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


prompt = selected_prompt
if prompt is None:
    prompt = st.chat_input("Ask about a patient, symptoms, labs, or next steps")

if prompt:
    st.session_state[CHAT_STATE_KEY].append({"role": "user", "content": prompt})

    transcript = []
    for message in st.session_state[CHAT_STATE_KEY][-8:]:
        speaker = "Clinician" if message["role"] == "user" else "Assistant"
        transcript.append(f"{speaker}: {message['content']}")

    agent_prompt = (
        "Continue this clinician chat using the patient snapshot agent. "
        "Be concise, clinically useful, and structured. "
        f"The active patient is {patient_name.strip()}. "
        "When patient identity is unclear, ask a short clarifying question.\n\n"
        "Conversation so far:\n"
        + "\n".join(transcript)
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        try:
            final_response = asyncio.run(_stream_reply(agent_prompt, response_placeholder))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                final_response = loop.run_until_complete(_stream_reply(agent_prompt, response_placeholder))
            finally:
                loop.close()

    st.session_state[CHAT_STATE_KEY].append({"role": "assistant", "content": final_response})

