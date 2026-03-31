# READY 2026 AI Hub Workshop — Participant Guide

## What You're Building

A **Patient Encounter Briefing Tool**: a clinician-facing web app that uses an LLM to query structured FHIR data via MCP tools and generate a patient snapshot.

By the end of this workshop, you'll have seen — and be able to reuse — the three core READY 2026 AI Hub patterns:

| Pattern | What it does |
|---|---|
| **IRIS MCP Server** | Exposes ObjectScript tools (SQL queries over FHIR data) as LLM-callable tools |
| **ConfigStore + Wallet** | Stores LLM credentials securely in IRIS, resolved at runtime |
| **langchain-intersystems** | Python SDK that wires ConfigStore → LLM → MCP tools → LangGraph agent |

---

## Stack at a Glance

```
Browser (Streamlit :8501)
    ↓  login → role check
Langchain Agent (Python 3.11, LangGraph)
    ↓  init_chat_model("readyai", iris_conn)   ← langchain-intersystems
IRIS ConfigStore  →  Wallet  →  OpenAI gpt-4o-mini
    ↓  get_tools() via MultiServerMCPClient
iris-mcp-server (:8888, HTTP streamable-http)
    ↓  dispatches to ReadyAI.ToolSet
IRIS READYAI namespace
    ├── AFHIRData.Observation  (34k rows)
    ├── AFHIRData.Condition    (1.5k rows)
    ├── AFHIRData.Patient      (119 rows)
    └── AFHIRData.DocumentReference
```

---

## Prerequisites

- Docker Desktop running (ARM64 Mac)
- `OPENAI_API_KEY` exported in your shell
- The repo cloned: `git clone https://gitlab.iscinternal.com/tdyar/ready2026-hackathon.git`

---

## Quick Start (10 minutes)

### 1. Build and start the stack

```bash
cd ReadyAI-demo

# Build IRIS for Health container (first time ~5 min)
docker-compose build

# Start IRIS + langchain app
OPENAI_API_KEY=$OPENAI_API_KEY docker-compose up -d iris langchain
```

Wait for IRIS to be healthy:
```bash
docker-compose ps   # iris should show "healthy"
```

### 2. Run one-time FHIR setup (~10 min)

```bash
# From repo root — run once per fresh container
python3 scripts/fhir_setup.py
```

This:
- Installs a FHIR R4 server and loads 121 synthetic patients
- Runs FHIR SQL Builder analysis → creates `AFHIRData` SQL tables
- Stores your `OPENAI_API_KEY` in the IRIS Wallet (never touches disk)

### 3. Start the MCP server

```bash
docker-compose up -d mcp-server
```

### 4. Open the app

http://localhost:8501

Login: `DScully / XFiles` (Doctor) or `NJoy / pokemon` (Nurse)

---

## Key Files to Know

```
ReadyAI-demo/
├── iris/projects/
│   ├── ObjectScript/ReadyAI/
│   │   ├── ToolSet.cls          # RBAC — which tools, which roles
│   │   ├── SQLTools.cls         # 4 MCP tools (ListTables, QueryTable, ...)
│   │   ├── MCPService.cls       # Registers the HTTP endpoint
│   │   └── ConfigStoreSetup.cls # Seeds AI.LLM.readyai in ConfigStore
│   └── config.toml              # iris-mcp-server config (port, namespace)
│
├── langchain_external/readyai_app/app/
│   ├── main.py                  # Login → role check → page routing
│   ├── pages/DoctorPage.py      # Patient picker + agent call
│   └── agent/get_patient_snapshot.py   # PatientSnapshotAgent
│
└── langchain_external/dist/
    └── langchain_intersystems-0.0.1-py3-none-any.whl
```

---

## Pattern 1: IRIS MCP Server (ObjectScript Tools)

The MCP server exposes ObjectScript class methods as LLM-callable tools.

**Define a tool** (`SQLTools.cls`):
```objectscript
Class ReadyAI.SQLTools Extends %AI.Tool
{
  Method QueryTable(
    tableName As %String,
    patientIds As %DynamicArray) As %DynamicObject
  {
    // SQL query → %DynamicObject response
  }
}
```

**Register it with RBAC** (`ToolSet.cls` XData):
```xml
<Include Class="ReadyAI.SQLTools">
    <Requirement Name="Role" Value="Doctor"/>
    <Requirement Name="ReadOnly" Value="1"/>
</Include>
```

**Discovery**: the MCP server auto-discovers tools from the ToolSet at first client connection.

---

## Pattern 2: ConfigStore + Wallet (Secure LLM Credentials)

The API key never touches `.env` or source code — it lives in the IRIS Wallet.

**Store the key** (once, via `scripts/fhir_setup.py` or manually):
```objectscript
do ##class(ReadyAI.ConfigStoreSetup).SetupWithAPIKey("sk-proj-...")
```

Internally this creates:
- `%Wallet.KeyValue "ReadyAI-Secrets.OpenAI"` — encrypted key storage
- `%ConfigStore.Configuration "AI.LLM.readyai"` → `{"model_provider":"openai","model":"gpt-4o-mini","api_key":"secret://ReadyAI-Secrets.OpenAI#api_key"}`

**Resolve the key at runtime** (Python):
```python
from langchain_intersystems.chat_models import init_chat_model

conn = iris.connect(host, port, namespace, username, password)
model = init_chat_model("readyai", conn)   # reads ConfigStore, resolves Wallet
conn.close()
# model is now a fully configured langchain BaseChatModel
```

---

## Pattern 3: langchain-intersystems Agent

```python
from langchain_intersystems.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

# 1. Get LLM from ConfigStore
conn = iris.connect(...)
model = init_chat_model("readyai", conn)
conn.close()

# 2. Get MCP tools (per-user credentials → RBAC enforced)
auth = base64.b64encode(f"{username}:{password}".encode()).decode()
client = MultiServerMCPClient({
    "readyai": {
        "transport": "http",
        "url": "http://iris:8888/mcp/readyai",
        "headers": {"Authorization": f"Basic {auth}"},
    }
})
tools = await client.get_tools()

# 3. Create agent
agent = create_agent(model=model, tools=tools, system_prompt="...")

# 4. Stream response
async for chunk in agent.astream(
    {"messages": [HumanMessage(content=prompt)]},
    stream_mode="messages",
):
    message, _ = chunk
    if message.type == "AIMessageChunk":
        for block in message.content_blocks:
            if block["type"] == "text":
                yield block["text"]
```

---

## RBAC in Action

Users authenticate against IRIS. Their role determines which MCP tools they see:

| User | Password | Role | Tools visible |
|---|---|---|---|
| `DScully` | `XFiles` | Doctor | All 5 tools (ListTables, QueryTable, GetConditionsList, GetPatientsByCondition, EchoUser) |
| `NJoy` | `pokemon` | Nurse | EchoUser only (SQLTools require Doctor role) |

The RBAC check happens inside `iris-mcp-server` — tools not accessible to the user's role are hidden from `get_tools()`.

---

## Adding Your Own Tool

1. Create `ReadyAI.MyTool.cls` extending `%AI.Tool`:
```objectscript
Class ReadyAI.MyTool Extends %AI.Tool
{
  Method MyMethod(param As %String) As %DynamicObject
  {
      quit {"Status": "OK", "Result": (param)}
  }
}
```

2. Register in `ToolSet.cls` XData:
```xml
<Include Class="ReadyAI.MyTool"/>
```

3. Compile and restart `mcp-server` — it auto-discovers.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Login fails: "Unable to allocate a license" | Restart IRIS: `docker-compose restart iris` |
| "Table not found in schema AFHIRData" | Run `python3 scripts/fhir_setup.py` |
| MCP server shows only `iris_status` tool | `docker-compose restart mcp-server` (waits for IRIS to be healthy) |
| Agent error: "Error initialising agent" | Check `OPENAI_API_KEY` is set and Wallet seeded |
| "Corrupt UTF-8 in IRIS response" | Likely large query result — add `TOP N` to SQL in SQLTools.cls |

---

## What to Hack

For the hackathon, you can extend this demo in any direction:

- **New FHIR tools**: Add `GetEncounterHistory`, `GetMedications`, `GetDocumentNotes` to `SQLTools.cls`
- **Vector search**: Use `RAG.DocRefSearchTool` — the vector store for `DocumentReference` text is pre-built
- **Different dataset**: Swap FHIR data for any domain (financial, operational) — the MCP + ConfigStore patterns are domain-agnostic
- **New LLM provider**: Change `model_provider` in ConfigStore — the code doesn't change
- **Nurse tools**: Remove the `<Requirement Name="Role" Value="Doctor"/>` restriction to give Nurses access, or create Nurse-specific tools

---

## Repository Layout

```
ready2026-hackathon/
├── ReadyAI-demo/               # Everything for the demo
│   ├── iris/                   # IRIS container (Dockerfile, scripts, ObjectScript, FHIR data)
│   │   └── projects/           # Volume-mounted at /home/irisowner/dev
│   ├── langchain_external/     # Python/Streamlit app
│   │   ├── dist/               # langchain_intersystems whl
│   │   └── readyai_app/app/    # Streamlit pages + agent
│   └── docker-compose.yaml
├── tests/                      # 57 tests (unit + integration + E2E)
├── scripts/fhir_setup.py       # One-time FHIR + Wallet setup
└── demos/langchain-vectorstore/ # IRISVectorStore standalone demo
```
