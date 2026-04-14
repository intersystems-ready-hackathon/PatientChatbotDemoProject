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
    ↓  login → role check → snapshot_page.py
Langchain Agent (Python 3.12, LangGraph)
    ↓  init_chat_model("gpt-5-nano", iris_conn)   ← langchain-intersystems
IRIS ConfigStore  →  Wallet  →  OpenAI gpt-5-nano
    ↓  get_tools() via MultiServerMCPClient  (Basic auth per-user)
iris-mcp-server (:8888, HTTP streamable-http)
    ↓  ReadyAI.MCPService
IRIS READYAI namespace
    ├── ReadyAI.StandardToolSet      ← EchoUser + FHIR SQL queries (all users)
    ├── ReadyAI.RestrictedAccessToolSet  ← ListTables, QueryTable (Doctor only)
    └── AFHIRData SQL schema
        ├── Patient      (121 rows)
        ├── Observation
        ├── Condition
        └── DocumentReference
```

---

## Prerequisites

- Docker Desktop running
- An `OPENAI_API_KEY`
- The repo: `git clone https://gitlab.iscinternal.com/tdyar/ready2026-hackathon.git`
- (First time only) An IRIS for Health AI Hub build kit — see [README.md](../README.md#building-ai-hub)

---

## Quick Start

### 1. Build base IRIS AI Hub image (first time only, ~5 min)

Follow the instructions in [README.md](../README.md#building-ai-hub) to build `i4h-aihub` from the downloaded kit.

### 2. Create `.env` and start the stack

```bash
cd ReadyAI-demo
echo 'OPENAI_API_KEY="sk-..."' > .env

docker-compose up -d --build
```

This builds: IRIS for Health + webgateway + the Streamlit/Langchain container.

Wait for IRIS to be healthy:
```bash
docker-compose ps   # iris should show "healthy"
```

The IRIS build (`iris.script`) automatically:
- Creates the `READYAI` namespace
- Loads ObjectScript classes via IPM
- Sets up FHIR server and loads 121 synthetic patients
- Registers the MCP web application at `/mcp/readyAI`
- Creates `DScully` (Doctor) and `NJoy` (Nurse) users
- Seeds the ConfigStore with your OpenAI API key

> **If the automated FHIR setup didn't run** (check `docker-compose logs iris` for errors), run it manually:
> ```bash
> docker exec -it iris iris session iris
> ```
> ```objectscript
> ZN "READYAI"
> Do ##class(Setup.FSB).RunAll()
> ```
> This takes 5-10 minutes.

### 3. Start the MCP server transport

The MCP *web application* is registered automatically, but the `iris-mcp-server` transport process must be started manually:

```bash
docker-compose exec -it iris bash
iris-mcp-server -c config.toml run
```

Leave this running in its terminal.

### 4. Verify the MCP server

```
http://localhost:32783/mcp/readyAI/v1/health
http://localhost:32783/mcp/readyAI/v1/services
```

Or test tool discovery locally:
```bash
pip install langchain langchain-mcp-adapters
python3 ReadyAI-demo/langchain_external/langchain_discovery.py
```

### 5. Open the app

http://localhost:8501

Login with either user to see the chat interface:

| User | Password | Role |
|---|---|---|
| `DScully` | `xfiles` | Doctor |
| `NJoy` | `pokemon` | Nurse |

---

## Key Files to Know

```
ReadyAI-demo/
├── iris/projects/
│   ├── src/ReadyAI/
│   │   ├── MCPService.cls             # HTTP MCP endpoint — specifies toolsets
│   │   ├── StandardToolSet.cls        # EchoUser + FHIR SQL queries (all roles)
│   │   ├── RestrictedAccessToolset.cls # ListTables, QueryTable (Doctor only)
│   │   ├── Tools/FHIRSQLQueryTools.cls # ListTables + QueryTable method bodies
│   │   ├── Tools/StandardTools.cls    # SearchForPatient + allergy/medication methods
│   │   └── Policies/RoleAuth.cls      # Doctor-only RBAC enforcement
│   ├── src/Setup/
│   │   ├── ConfigStore.cls            # Seeds AI.LLM.gpt-5-nano in ConfigStore
│   │   ├── Roles.cls                  # Creates DScully / NJoy users + roles
│   │   └── FSB.cls                    # FHIR server + SQL Builder setup
│   └── config.toml                    # iris-mcp-server config (port 8888)
│
├── langchain_external/readyai_app/app/
│   ├── main.py                        # Navigation: login_page → snapshot_page
│   ├── pages/login_page.py            # Login form → role check → redirect
│   ├── pages/snapshot_page.py         # Chat UI — works for Doctor and Nurse
│   └── agent/get_patient_snapshot.py  # PatientSnapshotAgent (LangGraph + MCP)
│
└── docker-compose.yaml                # iris + webgateway + langchain services
```

---

## Pattern 1: IRIS MCP Server (ObjectScript Tools)

The MCP server exposes ObjectScript class methods as LLM-callable tools via two ToolSets.

**`MCPService.cls`** declares which ToolSets to serve:
```objectscript
Class ReadyAI.MCPService Extends %AI.MCP.Service
{
  Parameter SPECIFICATION = "ReadyAI.RestrictedAccessToolSet,ReadyAI.StandardToolSet";
}
```

**`StandardToolSet.cls`** — available to all users, uses inline SQL queries in XData:
```xml
<ToolSet Name="ReadyAI.StandardToolSet">
    <Policies>
        <Audit Class="ReadyAI.Policies.AuditTable"/>
    </Policies>
    <Tool Name="EchoUser" Method="EchoUser"/>
    <Query Name="FindPatientsBySurname" Type="SQL" ...>
        SELECT ID, GivenName, FamilyName, BirthDate
        FROM AFHIRData.Patient WHERE FamilyName = :patientSurname
    </Query>
    ...
</ToolSet>
```

**`RestrictedAccessToolSet.cls`** — Doctor role required (enforced by `RoleAuth.cls`):
```xml
<ToolSet Name="ReadyAI.RestrictedAccessToolSet">
    <Policies>
        <Audit Class="ReadyAI.Policies.AuditTable"/>
        <Authorization Class="ReadyAI.Policies.RoleAuth"/>
    </Policies>
    <Include Class="ReadyAI.Tools.FHIRSQLQueryTools"/>
</ToolSet>
```

**Methods in `FHIRSQLQueryTools.cls`** (Extends `%AI.Tool`):
```objectscript
Method ListTables() As %DynamicObject {...}
Method QueryTable(tableName As %String, patientId As %Integer) As %DynamicObject {...}
```

---

## Pattern 2: ConfigStore + Wallet (Secure LLM Credentials)

The API key never touches a file — it lives in the IRIS Wallet.

**Store the key** (done automatically at build time, or run manually):
```objectscript
do ##class(Setup.ConfigStore).SetupWithAPIKey("sk-proj-...")
```

Internally this creates:
- `%Wallet.KeyValue "ReadyAI-Secrets.OpenAI"` — encrypted key storage
- `%ConfigStore.Configuration "AI.LLM.gpt-5-nano"` → `{"model_provider":"openai","model":"gpt-5-nano","api_key":"secret://ReadyAI-Secrets.OpenAI#api_key"}`

**Resolve the key at runtime** (Python):
```python
from langchain_intersystems.chat_models import init_chat_model

conn = iris.connect(host, port, namespace, username, password)
model = init_chat_model("gpt-5-nano", conn)   # reads ConfigStore, resolves Wallet
conn.close()
# model is now a fully configured langchain BaseChatModel
```

---

## Pattern 3: langchain-intersystems Agent

From `agent/get_patient_snapshot.py`:

```python
from langchain_intersystems.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

# 1. Get LLM from ConfigStore
conn = iris.connect(os.environ["IRIS_HOST"], 1972, "READYAI", username, password)
model = init_chat_model("gpt-5-nano", conn)
conn.close()

# 2. Get MCP tools — per-user Basic auth → RBAC enforced server-side
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
agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

# 4. Stream response (text + tool activity events)
async for chunk in agent.astream(
    {"messages": [HumanMessage(content=prompt)]},
    stream_mode="messages",
):
    message, _ = chunk
    if message.type in ("ai", "AIMessageChunk"):
        for block in message.content_blocks:
            if block["type"] == "text":
                yield block["text"]
```

---

## RBAC in Action

Users authenticate against IRIS. Their role is checked server-side — tools not accessible to the user's role are hidden from `get_tools()`.

| User | Password | Role | Tools visible |
|---|---|---|---|
| `DScully` | `xfiles` | Doctor | All tools: `EchoUser`, `FindPatientsBySurname`, `QueryAllergies`, `QueryMedications` (StandardToolSet) + `ListTables`, `QueryTable` (RestrictedAccessToolSet) |
| `NJoy` | `pokemon` | Nurse | StandardToolSet only: `EchoUser`, `FindPatientsBySurname`, `QueryAllergies`, `QueryMedications` |

Both users see the same `snapshot_page.py` — the agent automatically gets only the tools their role permits.

---

## Adding Your Own Tool

**Option A — Add an inline SQL query to `StandardToolSet.cls`** (no ObjectScript method needed):

```xml
<Query
    Name="GetRecentEncounters"
    Type="SQL"
    Description="Get recent encounters for a patient"
    Arguments="patientId As %Integer"
    MaxRows="20">
  SELECT TOP 20 Status, Class, Period FROM AFHIRData.Encounter
  WHERE Patient = CONCAT('Patient/', :patientId)
  ORDER BY Period DESC
</Query>
```

**Option B — Add a method to a `%AI.Tool` class** and include it in a ToolSet:

1. Create `ReadyAI/Tools/MyTool.cls`:
```objectscript
Class ReadyAI.Tools.MyTool Extends %AI.Tool
{
  Method MyMethod(param As %String) As %DynamicObject
  {
      quit {"Status": "OK", "Result": (param)}
  }
}
```

2. Include in `StandardToolSet.cls` XData (or create a new ToolSet):
```xml
<Include Class="ReadyAI.Tools.MyTool"/>
```

3. After editing, the class is auto-compiled (volume-mounted). Restart the `iris-mcp-server` process to pick up the new tool.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Login shows "Login failed" | Check IRIS is healthy: `docker-compose ps`; restart if needed |
| `docker-compose build` succeeds but no AFHIRData tables | Run FSB manually — see Step 2 above |
| MCP tool discovery returns no tools | Ensure `iris-mcp-server -c config.toml run` is active in the container |
| "Failed to retrieve tools from MCP" in app | MCP transport not started — see Step 3 |
| Agent error: "RuntimeError: Failed to initialise chat model" | ConfigStore not seeded — rerun `Setup.ConfigStore.SetupWithAPIKey()` |
| Tool invocations hang or return WebSocket errors | Known issue with `iris-mcp-server` 2.0 + `mcp` 1.26 WebSocket backchannel; tool discovery works, tool execution may fail |
| App shows blank page after login | Check `docker-compose logs langchain` |

---

## What to Hack

- **New FHIR tools**: Add inline `<Query>` entries to `StandardToolSet.cls` to expose `Encounter`, `MedicationRequest`, or `DocumentReference` data
- **Vector search**: Uncomment `RAG.DocRefSearchTool` in a ToolSet — the `AFHIRData.DocRefVectorStore` global is pre-built
- **Different LLM provider**: Change `model_provider` in `Setup.ConfigStore.SetupWithAPIKey()` — the Python agent code doesn't change
- **Stricter Nurse tools**: Add a `NurseToolSet` with its own `Authorization` policy
- **Audit log viewer**: Query `ReadyAI.ToolLog` — every tool call is logged via `ReadyAI.Policies.AuditTable`

---

## Repository Layout

```
ready2026-hackathon/
├── ReadyAI-demo/
│   ├── iris/                   # IRIS container (Dockerfile, iris.script, ObjectScript, FHIR data)
│   │   └── projects/src/       # Volume-mounted ObjectScript classes
│   ├── langchain_external/     # Python/Streamlit app (Docker container)
│   │   └── readyai_app/app/    # main.py + pages/ + agent/
│   ├── webgateway/             # Webgateway config (CSP.conf/ini)
│   └── docker-compose.yaml
├── tests/                      # Unit + integration + E2E tests
├── scripts/fhir_setup.py       # Manual FHIR setup fallback (seeds Wallet + runs FSB)
└── demos/langchain-vectorstore/ # Standalone IRISVectorStore demo
```
