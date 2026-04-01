# AGENTS.md — ready2026-hackathon

**Generated:** 2026-03-30 | **Commit:** a675f7e | **Branch:** main

## Overview

Patient Encounter Briefing Tool — demonstrates IRIS AI Hub integration patterns for READY 2026.
Two layers: IRIS container (FHIR data + MCP server + ObjectScript tools) + Python app (Streamlit + Langchain).

**Stack**: Python 3.12, Streamlit, `langchain-intersystems`, `langchain-mcp-adapters`, InterSystems IRIS 2025.1+, FHIR SQL Builder

## Structure

```
ready2026-hackathon/
├── ReadyAI-demo/               # Main demo: IRIS container + Streamlit app
│   ├── iris/                   # IRIS Docker build (Dockerfile, .cpf, ObjectScript, FHIR data)
│   │   └── projects/           # Mounted at /home/irisowner/dev inside container
│   │       ├── ObjectScript/   # .cls tool definitions (ReadyAI.*, Examples.*, RAG.*)
│   │       └── FHIR/           # FHIR SQL Builder setup request bodies
│   ├── langchain_external/     # Python app (Streamlit + Langchain agent)
│   │   └── readyai_app/app/    # Entry: main.py (login), pages/ (DoctorPage, NursePage), agent/
│   └── iris4h-aicore-build/    # Alternative aicore Dockerfile (unused in default compose)
├── demos/
│   └── langchain-vectorstore/  # Standalone IRISVectorStore demo (separate IRIS instance)
├── docs/hackathon_plan.md      # Detailed feature plan
├── HackathonPlan.md            # Architecture overview + dependencies
└── .specify/                   # SpecKit workflow artifacts (constitution, templates)
```

## Where to Look

| Task | Location |
|------|----------|
| Add/modify MCP tools (ObjectScript) | `ReadyAI-demo/iris/projects/ObjectScript/ReadyAI/` |
| Add MCP tool example | `ReadyAI-demo/iris/projects/ObjectScript/Examples/` |
| RAG / vector search tools | `ReadyAI-demo/iris/projects/ObjectScript/RAG/` |
| MCP server config (port, transport) | `ReadyAI-demo/iris/projects/config.toml` |
| ToolSet RBAC config | `ReadyAI.ToolSet` XData in `ToolSet.cls` |
| Streamlit app entry point | `ReadyAI-demo/langchain_external/readyai_app/app/main.py` |
| Langchain agent (snapshot) | `ReadyAI-demo/langchain_external/readyai_app/app/agent/get_patient_snapshot.py` |
| Role-based page routing | `DoctorPage.py`, `NursePage.py` in `app/pages/` |
| FHIR SQL Builder setup | `ReadyAI-demo/iris/projects/FHIR/SetupRequestBodies/` + `fhirsqlSetupCommands.txt` |
| IRIS build customization | `ReadyAI-demo/iris/iris.script`, `iris.cpf` |
| Synthetic patient FHIR data | `ReadyAI-demo/iris/fhirsampledata/patients/` (121 JSON files) |
| IRISVectorStore standalone demo | `demos/langchain-vectorstore/` |

## Development Rules

1. **Tests before implementation** — write tests first for every component
2. **No hardcoded IRIS connection strings** — use AI Hub managed connections or env vars
3. **No real patient PHI** — synthetic/demo data only
4. **LangGraph state**: use `TypedDict` for state, never plain dicts (breaks serialization)
5. See `.specify/memory/constitution.md` for full project principles

## Running

```bash
# Start IRIS + app containers
cd ReadyAI-demo && docker-compose up -d --build

# FHIR SQL Builder setup (run once after containers are up, inside IRIS session)
docker exec -it iris iris session iris
# Then run commands from ReadyAI-demo/iris/fhirsqlSetupCommands.txt

# Start MCP server (inside container)
docker-compose exec -it iris bash
iris-mcp-server -c config.toml run

# Run Streamlit app locally (after pip install)
streamlit run ReadyAI-demo/langchain_external/readyai_app/app/main.py

# Test MCP tools discovery
python3 ReadyAI-demo/langchain_external/langchain_discovery.py

# Run tests
pytest
```

## Architecture: MCP Tool Flow

```
Streamlit (login → role check) → PatientSnapshotAgent
    → MultiServerMCPClient (HTTP, Basic auth)
        → iris-mcp-server (port 8888) → IRIS (port 1972/1973, namespace READYAI)
            → ReadyAI.MCPService → ReadyAI.ToolSet
                → ReadyAI.SQLTools (Doctor-only, ReadOnly)
                → Examples.EchoUser
                → RAG.DocRefSearchTool
```

## RBAC Pattern

- IRIS roles drive tool access: `Doctor` role → full SQLTools; `Nurse` → restricted
- Role check: `Utils.GetRoles.GetRoles()` via `iris.createIRIS(conn).classMethodValue(...)`
- Tool-level enforcement: `<Requirement Name="Role" Value="Doctor"/>` in `ToolSet.cls` XData
- Unauthorized tool calls: agent continues, reports access denial in final response

## FHIR SQL Builder

- Schema: `AFHIRData` (UpperCamelCase table names — IRIS convention)
- Key tables: `Observation`, `Condition`, `MedicationRequest`, `Encounter`, `Patient`, `DocumentReference`
- Patient column detection: looks for `Patient`, `PatientId`, `PatientID` variants
- Vector store for `DocumentReference` text: global `AFHIRData.DocRefVectorStore`

## Key Dependencies

| Package | Source | Notes |
|---------|--------|-------|
| `langchain-intersystems` | ISC internal (Aohan Dang, CRE-14103) | `IRISVectorStore`, `init_chat_model` |
| `langchain-mcp-adapters` | PyPI | `MultiServerMCPClient` for HTTP MCP |
| `iris` (Python) | InterSystems | DB-API + Native API (`createIRIS`) |
| `iris-mcp-server` binary | AI Core team | Must be present in IRIS container |
| `%AI.*` ObjectScript classes | AI Core team | `%AI.Tool`, `%AI.ToolSet`, `%AI.MCP.Service` |

## Known Gotchas

- `iris-mcp-server` and `langchain-intersystems` are provided by separate ISC teams — mock if unavailable
- FHIR SQL Builder setup POSTs fail during Docker build (web-gateway dependency) — run manually post-start
- `get_patient_snapshot.py` hardcodes `localhost:1973` — needs env-var extraction
- `NursePage.py` is empty — not yet implemented
- `DoctorPage.py` missing `import asyncio` (will error at runtime)
- `langchain_discovery.py` hardcodes `SuperUser:SYS` credentials in commented-out lines
