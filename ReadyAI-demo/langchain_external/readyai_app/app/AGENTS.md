# AGENTS.md — readyai_app/app/

Streamlit application. Entry: `main.py` (login + role routing). Pages: `pages/`. Agent: `agent/`.

## Structure

```
app/
├── main.py                     # Login form → role check → st.switch_page()
├── pages/
│   ├── DoctorPage.py           # Patient ID input → PatientSnapshotAgent stream
│   └── NursePage.py            # Nurse view (same agent, Nurse role = no SQLTools)
└── agent/
    └── get_patient_snapshot.py # PatientSnapshotAgent: MCP tools + LLM streaming
```

## Auth Flow

```
main.py: iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, user, pass)
    → iris.createIRIS(conn).classMethodValue("Utils.GetRoles", "GetRoles")
    → st.session_state["Roles"] = roles
    → switch_page to DoctorPage or NursePage
```

## PatientSnapshotAgent

- `__init__(username, password)` — stores creds for downstream MCP auth
- `_iris_conn()` — opens IRIS connection using env vars (IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE)
- `get_snapshot_agent()` — `init_chat_model(LLM_CONFIG_NAME, conn)` + `MultiServerMCPClient` + agent
- `get_tools()` — `MultiServerMCPClient` with Basic auth header, HTTP transport
- `stream_response(prompt)` — async generator yielding text chunks
- MCP endpoint: `MCP_URL` env var (default: `http://iris:8888/mcp/readyai`)
- LLM: resolved from IRIS ConfigStore via `LLM_CONFIG_NAME` (default: `readyai`)

## Environment Variables

| Var | Default | Purpose |
|-----|---------|---------|
| `IRIS_HOST` | `iris` | IRIS hostname (docker service name) |
| `IRIS_PORT` | `1972` | IRIS superserver port |
| `IRIS_NAMESPACE` | `READYAI` | IRIS namespace |
| `MCP_URL` | `http://iris:8888/mcp/readyai` | iris-mcp-server HTTP endpoint |
| `LLM_CONFIG_NAME` | `readyai` | ConfigStore key under `AI.LLM.*` |

## ConfigStore Setup (one-time, run inside IRIS after docker-compose up)

```objectscript
zn "READYAI"
do ##class(ReadyAI.ConfigStoreSetup).Setup()
```

Or with API key stored in Wallet:
```objectscript
do ##class(ReadyAI.ConfigStoreSetup).SetupWithAPIKey("sk-...")
```

## Conventions

- `st.session_state["Username"]`, `["Password"]`, `["Roles"]` — shared across pages
- Agent methods are all `async` — collect via `asyncio.run()` from Streamlit sync context
- Patient IDs are FHIR references: `Patient/{id}` — not bare integers
- Do NOT store plain-text passwords beyond session scope

## Anti-Patterns

- Do NOT hardcode IRIS host/port/credentials — use env vars only
- Do NOT import from `agent/` using relative paths outside the `app/` root
- Do NOT call `st.write(chunk, end="", flush=True)` — those kwargs don't exist on `st.write`
