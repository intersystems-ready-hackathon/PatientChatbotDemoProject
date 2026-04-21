import asyncio
import json
import streamlit as st

from agent.get_patient_snapshot import PatientSnapshotAgent

st.set_page_config(page_title="Snapshot Chat", page_icon="💬", layout="wide")

CHAT_STATE_KEY = "snapshot_chat_messages"
QUEUED_PROMPT_KEY = "snapshot_queued_prompt"
PATIENT_NAME_KEY = "snapshot_patient_name"
SUGGESTED_PROMPT_TEMPLATES = [
    
    "Give me a concise snapshot for {patient_name}.",
    "What are the most important recent labs for {patient_name}?",
    "Summarize active problems and likely next steps for {patient_name}.",
    "What tools do you have?",
]
DEFAULT_GREETING = (
    "Hello. Ask for a patient snapshot, recent clinical context, or a concise follow-up summary."
)


USER = st.session_state.get("Username")
ROLES = st.session_state.get("Roles", [])

if not st.session_state.get("logged_in") or not USER:
    st.switch_page("pages/login_page.py")

if "Doctor" not in ROLES and "Nurse" not in ROLES:
    st.error("You do not have access to the patient snapshot page.")
    st.switch_page("pages/login_page.py")


def _format_tool_status(status: str) -> tuple[str, str]:
    if status in ("success", "completed"):
        return "Completed", "complete"
    if status == "error":
        return "Errored", "error"
    return "Running", "running"


def _render_json_block(label: str, value: str) -> None:
    if not value:
        return
    st.caption(label)
    try:
        st.json(json.loads(value), expanded=2)
    except (TypeError, json.JSONDecodeError):
        st.code(value, language="json")


def _render_tool_activity(tool_placeholder, tool_events: dict) -> None:
    with tool_placeholder.container():
        st.markdown("#### Tool activity")
        for tool_event in tool_events.values():
            status_label, state = _format_tool_status(tool_event["status"])
            expander_label = f'{tool_event["name"]} - {status_label}'
            with st.expander(expander_label, expanded=state == "running"):
                if state == "running":
                    st.info("Tool call in progress")
                elif state == "complete":
                    st.success("Tool call completed")
                else:
                    st.error("Tool call failed")

                _render_json_block("Arguments", tool_event["args"])
                _render_json_block("Result", tool_event["content"])


async def _stream_reply(prompt: str, tool_container, response_placeholder) -> str:
    chunks = []
    tool_events = {}
    agent = PatientSnapshotAgent(st.session_state["Username"], st.session_state["Password"])
    with tool_container.container():
        tool_placeholder = st.empty()

    async for chunk in agent.stream_response(prompt):
        if isinstance(chunk, dict):
            if chunk["type"] == "tool_call":
                existing_event = tool_events.get(chunk["id"], {})
                tool_events[chunk["id"]] = {
                    "name": chunk["name"],
                    "status": existing_event.get("status", "running"),
                    "args": chunk["args"],
                    "content": existing_event.get("content", ""),
                }
            elif chunk["type"] == "tool_result":
                existing_event = tool_events.get(chunk["id"], {})
                tool_events[chunk["id"]] = {
                    "name": existing_event.get("name") or chunk.get("name", "Tool"),
                    "status": chunk["status"],
                    "args": existing_event.get("args", ""),
                    "content": chunk["content"],
                }

            _render_tool_activity(tool_placeholder, tool_events)
            continue

        chunks.append(chunk)
        response_placeholder.markdown("".join(chunks) + "▌")

    final_text = "".join(chunks).strip()
    if final_text:
        response_placeholder.markdown(final_text)
        return final_text

    fallback = "I could not generate a response from the snapshot agent."
    response_placeholder.markdown(fallback)
    return fallback


st.session_state.setdefault(
    CHAT_STATE_KEY,
    [{"role": "assistant", "content": DEFAULT_GREETING}],
)
st.session_state.setdefault(PATIENT_NAME_KEY, "Stewart Larson")
st.session_state.setdefault(QUEUED_PROMPT_KEY, "")

with st.sidebar:
    st.caption(f"Signed in as {USER}")
    mainrole = "Doctor" if "Doctor" in ROLES else 'Nurse' if 'Nurse' in ROLES else "No roles"
    st.caption(f"Role: {mainrole}")
    if st.button("New chat", use_container_width=True):
        st.session_state[CHAT_STATE_KEY] = [{"role": "assistant", "content": DEFAULT_GREETING}]
        st.session_state[QUEUED_PROMPT_KEY] = ""
        st.rerun()
    if st.button("Log out", type="primary", use_container_width=True):
        st.session_state["Username"] = ""
        st.session_state["Password"] = ""
        st.session_state["Roles"] = []
        st.session_state["logged_in"] = False
        st.session_state.pop(CHAT_STATE_KEY, None)
        st.session_state.pop(QUEUED_PROMPT_KEY, None)
        st.switch_page("pages/login_page.py")

with st.container(border=True):
    st.markdown(f"## {USER}'s Snapshot Chat")
    st.write(
        "Use the snapshot agent for patient briefs, quick follow-up questions, and concise handoff support."
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

for message in st.session_state[CHAT_STATE_KEY]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.caption("Suggested prompts")
prompt_columns = st.columns(len(suggested_prompts))
for column, suggested_prompt in zip(prompt_columns, suggested_prompts):
    if column.button(
        suggested_prompt,
        key=f"suggested_prompt_{suggested_prompt}",
        use_container_width=True,
    ):
        st.session_state[QUEUED_PROMPT_KEY] = suggested_prompt
        st.rerun()

prompt = st.chat_input("Ask about a patient, symptoms, labs, or next steps")
if not prompt:
    prompt = st.session_state.pop(QUEUED_PROMPT_KEY, "")

prompt = prompt.strip()

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
        tool_container = st.container()
        response_placeholder = st.empty()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                final_response = asyncio.run(_stream_reply(agent_prompt, tool_container, response_placeholder))
            except Exception as error:
                final_response = f"Snapshot agent failed: {error}"
                response_placeholder.error(final_response)
        else:
            loop = asyncio.new_event_loop()
            try:
                final_response = loop.run_until_complete(_stream_reply(agent_prompt, tool_container, response_placeholder))
            except Exception as error:
                final_response = f"Snapshot agent failed: {error}"
                response_placeholder.error(final_response)
            finally:
                loop.close()

    st.session_state[CHAT_STATE_KEY].append({"role": "assistant", "content": final_response})

