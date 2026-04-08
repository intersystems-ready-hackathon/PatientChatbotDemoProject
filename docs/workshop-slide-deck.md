# READY 2026 AI Hub Workshop — Slide Deck

**Duration:** 45–60 minutes
**Format:** Presentation + live demo + hands-on
**Audience:** Healthcare IT developers, IRIS developers, hackathon participants

---

## Slide 1 — Title

**Building AI-Powered Clinical Apps with IRIS AI Hub**
*READY 2026 Pre-Hackathon Workshop*

*[30 seconds]*

---

## Slide 2 — What We're Going to Build

**Live demo app: Patient Encounter Briefing Tool**

> A clinician asks: *"Give me a snapshot of Patient Vicente Aponte"*
> The app: queries real FHIR data, reasons over it, produces a structured summary

**[Screenshot of the working app]**

*What makes it interesting:*
- The LLM is configured in IRIS, not in code
- The tools the LLM uses are ObjectScript class methods
- Role-based access control is enforced by IRIS, not the app

*[2 minutes]*

---

## Slide 3 — The Three Patterns You'll Reuse

```
┌─────────────────────────────────────────────────┐
│  Pattern 1: IRIS MCP Server                      │
│  ObjectScript tools → LLM-callable via HTTP      │
├─────────────────────────────────────────────────┤
│  Pattern 2: ConfigStore + Wallet                 │
│  LLM credentials stored securely in IRIS         │
├─────────────────────────────────────────────────┤
│  Pattern 3: langchain-intersystems               │
│  Python SDK: ConfigStore → LLM → MCP → Agent    │
└─────────────────────────────────────────────────┘
```

*These work for any domain — not just healthcare.*

*[1 minute]*

---

## Slide 4 — Architecture Overview

```
[Browser :8501]
    ↓ login (IRIS auth)
[Streamlit + LangGraph Agent]
    ↓ init_chat_model("readyai", iris_conn)
[IRIS ConfigStore] → [IRIS Wallet] → [OpenAI API]
    ↓ get_tools() with Basic auth
[iris-mcp-server :8888]
    ↓ role check → dispatches tools
[IRIS READYAI namespace]
    ├── ObjectScript MCP tools
    └── AFHIRData.* (FHIR SQL Builder projection)
```

*[3 minutes — walk through each layer]*

---

## Slide 5 — Pattern 1: IRIS MCP Server

**"Define your tools in ObjectScript, serve them to any LLM"**

```objectscript
Class ReadyAI.SQLTools Extends %AI.Tool
{
  Method QueryTable(
    tableName As %String,
    patientIds As %DynamicArray) As %DynamicObject
  {
    // SQL query over AFHIRData schema
    // Returns %DynamicObject — auto-serialized to JSON
  }
}
```

The MCP server (`iris-mcp-server`) auto-discovers tools at startup.
The tool description comes from the method's docstring.

**RBAC is just XML:**
```xml
<Include Class="ReadyAI.SQLTools">
    <Requirement Name="Role" Value="Doctor"/>
</Include>
```

Doctors see the tool. Nurses don't. No app code involved.

*[5 minutes]*

---

## Slide 6 — Pattern 1: Live Demo Setup

**[Switch to terminal]**

```bash
# What the MCP server exposes
python3 -c "
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio, base64
auth = base64.b64encode(b'DScully:XFiles').decode()
client = MultiServerMCPClient({'readyai': {
    'transport': 'http',
    'url': 'http://localhost:8888/mcp/readyai',
    'headers': {'Authorization': f'Basic {auth}'}
}})
async def main():
    tools = await client.get_tools()
    for t in tools: print(t.name, '—', t.description[:60])
asyncio.run(main())
"
```

*Show: Doctor sees 5 tools, Nurse sees 1*

*[3 minutes]*

---

## Slide 7 — Pattern 2: ConfigStore + Wallet

**"The API key never touches source code or .env files"**

```
OPENAI_API_KEY (your shell env)
        ↓  scripts/fhir_setup.py
    ↓  Setup.ConfigStore.SetupWithAPIKey()
┌─────────────────────────────────────────┐
│ IRIS Wallet                             │
│  "ReadyAI-Secrets.OpenAI"              │
│  → encrypted { "api_key": "sk-proj-..." }│
└─────────────────────────────────────────┘
        ↓  referenced by
┌─────────────────────────────────────────┐
│ ConfigStore: AI.LLM.readyai             │
│  model_provider: openai                 │
    │  model: gpt-5-nano                      │
│  api_key: secret://ReadyAI-Secrets...   │
└─────────────────────────────────────────┘
```

**To swap LLM providers:** change the ConfigStore entry. Zero code changes.

*[4 minutes]*

---

## Slide 8 — Pattern 3: langchain-intersystems

**"Three lines to wire everything together"**

```python
from langchain_intersystems.chat_models import init_chat_model

conn = iris.connect(host, port, namespace, user, password)
model = init_chat_model("readyai", conn)  # ← reads ConfigStore + Wallet
conn.close()
```

That's it. `model` is a standard `langchain BaseChatModel`.
Works with `create_agent`, `ChatPromptTemplate`, chains — everything in the langchain ecosystem.

**MCP client is standard `langchain-mcp-adapters`:**
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "readyai": {
        "transport": "http",
        "url": MCP_URL,
        "headers": {"Authorization": f"Basic {auth}"},
    }
})
tools = await client.get_tools()
```

*[4 minutes]*

---

## Slide 9 — Putting It Together: The Agent

```python
agent = create_agent(
    model=model,          # from ConfigStore via langchain-intersystems
    tools=tools,          # from MCP server, RBAC-filtered per user
    system_prompt="..."
)

# Stream the response
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

LangGraph handles the tool call loop:
`LLM → calls tool → gets result → LLM → final answer`

*[3 minutes]*

---

## Slide 10 — Live Demo

**[Switch to browser: http://localhost:8501]**

Walk through:
1. Login as `DScully / XFiles` (Doctor) — Enter key works
2. Select patient from dropdown — note real patient names from FHIR data
3. Click Generate — watch the agent call tools and synthesize
4. Show the output: conditions table, observations, graceful handling of missing tables
5. Login as `NJoy / pokemon` (Nurse) — same UI, limited tools, different experience

**Key things to point out:**
- The LLM chose which tables to query based on the prompt
- The RBAC was enforced without any app-level code
- The API key was never in a config file

*[10 minutes]*

---

## Slide 11 — FHIR SQL Builder

**"FHIR data as SQL tables — no custom parsing"**

121 synthetic patients, loaded as FHIR R4 JSON bundles.

FHIR SQL Builder analyses the FHIR server and projects resources into:

| SQL Table | FHIR Resource | Key columns |
|---|---|---|
| `AFHIRData.Patient` | Patient | GivenName, FamilyName |
| `AFHIRData.Condition` | Condition | Description, SnomedCode, Status, Patient |
| `AFHIRData.Observation` | Observation | Code, Description, ValueQuantity, ValueUOM |
| `AFHIRData.DocumentReference` | DocumentReference | (text for RAG) |

The MCP tool just queries these like any SQL table.
**You don't need to understand FHIR to query it.**

*[3 minutes]*

---

## Slide 12 — For Your Hackathon Project

**You can use any of these three layers independently:**

| Layer | You need | You get |
|---|---|---|
| MCP Server only | ObjectScript methods | Any LLM client can call your IRIS logic |
| ConfigStore only | IRIS connection | Centrally managed, provider-swappable LLM |
| Full stack | Both + Streamlit | Working app template |

**You don't have to use FHIR.** Swap in any data source:
- `AFHIRData.*` → any SQL tables in IRIS
- Add new tools to `ToolSet.cls` in minutes
- Different `model_provider` in ConfigStore = different LLM

**Three hackathon tracks:**
1. Healthcare — extend this demo (more FHIR tools, RAG, clinical reasoning)
2. Non-Healthcare — same patterns, different domain
3. Experimental — push the boundaries (multi-agent, streaming, voice UI)

*[4 minutes]*

---

## Slide 13 — Hands-On Time

**[Everyone open their laptops]**

1. Clone the repo: `git clone https://gitlab.iscinternal.com/tdyar/ready2026-hackathon.git`
2. `cd ReadyAI-demo && OPENAI_API_KEY=$OPENAI_API_KEY docker-compose up -d iris langchain`
3. While it builds, read `docs/workshop-participant-guide.md`
4. When IRIS is healthy: `python3 scripts/fhir_setup.py`
5. `docker-compose up -d mcp-server`
6. Open http://localhost:8501

**Suggested first modification:**
Open `ReadyAI-demo/iris/projects/ObjectScript/ReadyAI/SQLTools.cls`
and add a new method that queries a table you're interested in.

*[15 minutes — circulate and help]*

---

## Slide 14 — Q&A + Wrap-Up

**What we covered:**
- ✅ IRIS MCP Server: ObjectScript tools → LLM
- ✅ ConfigStore + Wallet: secure, swappable LLM credentials
- ✅ langchain-intersystems: standard langchain + IRIS config resolution
- ✅ FHIR SQL Builder: FHIR data as queryable SQL

**Resources:**
- `docs/workshop-participant-guide.md` — everything from today
- `tests/` — 57 tests showing every pattern, good reference code
- `demos/langchain-vectorstore/` — IRISVectorStore standalone demo
- Ask the AI Core team about: `iris-mcp-server`, `langchain_intersystems`, `%AI.Tool`, `%ConfigStore`

**Hackathon starts:** Monday, April 27, 2026
**Repo:** https://gitlab.iscinternal.com/tdyar/ready2026-hackathon

*[5 minutes]*

---

## Speaker Notes

### Timing guide
| Slide | Time | Cumulative |
|---|---|---|
| 1-3 (intro + patterns) | 3 min | 3 min |
| 4 (architecture) | 3 min | 6 min |
| 5-6 (MCP server) | 8 min | 14 min |
| 7 (ConfigStore) | 4 min | 18 min |
| 8-9 (langchain) | 7 min | 25 min |
| 10 (live demo) | 10 min | 35 min |
| 11 (FHIR SQL Builder) | 3 min | 38 min |
| 12 (hackathon) | 4 min | 42 min |
| 13 (hands-on) | 15 min | 57 min |
| 14 (Q&A) | 5 min | 62 min |

### Things that might go wrong
- IRIS not healthy yet → show `docker-compose ps`, explain the healthcheck
- FHIR setup still running → show the setup in progress, explain what it's doing
- Agent error → "this is a known iris-mcp-server 2.0/mcp compatibility issue — we've worked around it with TOP 50 in queries"
- Login fails → restart IRIS, it may have hit the license limit from our setup

### Key demo patients
- `Patient/38229` — Vicente Aponte (good for demo: cardiac arrest, hypertension, COVID)
- `Patient/38631` — Victoria Bañuelos (has accented characters — good for showing robustness)
- `Patient/7` — Synthia Schinner (large history — good for showing TOP 50 truncation)
