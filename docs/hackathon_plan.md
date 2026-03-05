READY 2026 Mini-Hackathon — Revised Plan
The Core Insight
ai-hub is already the risk mitigation layer. The hackathon repo vendors a minimal slice of it, with every integration point clearly labeled for swap-out. No pip install iris_agent at hackathon time — just pip install -r requirements.txt (public PyPI only) and a kit-installed IRIS per team.
---
The Abstraction Model (replacing the wrong if/elif)
# hackathon/core/backend.py  — vendored from ai-hub backends/registry.py pattern
class IRISBackend:
    """Single interface. Swap the constructor, nothing else changes."""
    
    # TODAY (hackathon day):
    @staticmethod
    def from_fastmcp(iris_conn) -> "IRISBackend":
        # Uses python/aihub/mcp/server.py bridge (vendored)
        ...
    # MIGRATION PATH A — when Dave's kit ships (Build 125):
    @staticmethod  
    def from_iris_mcp_server(host, port) -> "IRISBackend":
        # iris-mcp-server binary, MCP_SERVER_GUIDE.md
        ...
    # MIGRATION PATH B — when Aleks ships:
    @staticmethod
    def from_amp_gateway(endpoint) -> "IRISBackend":
        # AMP REST MCP gateway
        ...
    # LLM side — TODAY:
    @staticmethod
    def llm_from_iris_llm(provider_name) -> BaseChatModel:
        # iris_llm (kit-installed)
        ...
    # LLM MIGRATION PATH — when langchain_intersystems ships:
    @staticmethod
    def llm_from_langchain_intersystems(config_name) -> BaseChatModel:
        # IRISChatModel, Aleks/Aohan
        ...
    # LLM FALLBACK — always works, no kit needed:
    @staticmethod
    def llm_direct(model="gpt-4.1-nano") -> BaseChatModel:
        # plain langchain + openai key
        ...
Every attendee file touches only IRISBackend.from_*() — one line to change when a new path ships. Migration is documented in MIGRATION.md, not scattered across the code.
---
Repo Structure
../ready2026-hackathon/
│
├── README.md                  # 5-minute setup, schedule, track choice
├── MIGRATION.md               # Clear swap-out guide: FastMCP→iris-mcp-server→AMP
├── requirements.txt           # Public PyPI only: langchain, openai, fastmcp,
│                              # intersystems-irispython, kaggle, pandas, streamlit
├── docker-compose.yml         # Wraps ../aicore Build 124; one per team
├── .env.example               # OPENAI_API_KEY, IRIS_HOST, IRIS_PORT, IRIS_NS
│
├── core/                      # Vendored minimal slice of ai-hub
│   ├── backend.py             # IRISBackend abstraction (above)
│   ├── mcp_bridge.py          # FastMCP bridge — vendored from aihub/mcp/server.py
│   ├── tools/
│   │   ├── iris_sql.py        # vendored from aihub/mcp/tools/iris_sql.py
│   │   └── iris_vector.py     # vendored from aihub/mcp/tools/iris_vector.py
│   └── README.md              # "These files vendored from ai-hub @ commit XXX.
│                              #  Replace with pip install iris_agent when kit ships."
│
├── template/                  # BASE AGENT — everyone starts here (Workshop hour)
│   ├── agent.py               # Wired to IRISBackend; 50 lines max
│   ├── tools.py               # 2 starter tools: iris.sql.query + iris.vector.search
│   ├── config.py              # Reads .env; selects backend path
│   └── README.md              # Step-by-step: run this first, then pick a track
│
├── tracks/
│   ├── healthcare/            # FHIR + clinical data track
│   │   ├── data/
│   │   │   ├── seed_fhir.py   # Seeds MIMIC-style FHIR resources into IRIS
│   │   │   └── sample.fhir.json
│   │   ├── starter/
│   │   │   ├── agent.py       # Extends template/ — AppointIT scenario
│   │   │   └── tools.py       # FHIR-specific tools (patient lookup, scheduling)
│   │   └── challenges/
│   │       ├── 01_basic.md    # "Add a tool that finds available appointment slots"
│   │       ├── 02_medium.md   # "Add semantic search over clinical notes"
│   │       └── 03_hard.md     # "Build a triage routing agent"
│   │
│   └── general/               # EmployMe job-routing track
│       ├── data/
│       │   ├── seed_jobs.py   # Downloads Kaggle dataset, seeds into IRIS
│       │   ├── kaggle.json    # Dataset ref (e.g. job postings dataset)
│       │   └── README.md      # "Run seed_jobs.py first"
│       ├── starter/
│       │   ├── agent.py       # Extends template/ — Jane/Joe scenario
│       │   └── tools.py       # Job search, resume match, routing tools
│       └── challenges/
│           ├── 01_basic.md    # "Add multilingual input handling"
│           ├── 02_medium.md   # "Add semantic job matching via vector search"
│           └── 03_hard.md     # "Build a full routing agent with memory"
│
├── mentors/
│   ├── guide.md               # Table mentor runbook
│   ├── scoring_rubric.md      # Judging criteria
│   └── troubleshooting.md     # Top 10 issues + fixes
│
└── sim-reveal/                # STRETCH GOAL — isolated, no dependency on above
    ├── README.md              # "Only attempt if sim backend swap is complete"
    └── swap_to_aicore.py      # Hot-swaps sim tool config to use IRISBackend
---
Schedule → Repo Mapping
| Time | Activity | What they're in |
|---|---|---|
| 9:00–10:00 | Workshop: IRIS AI Hub overview + template walk-through | template/ |
| 10:00–11:00 | Guided Early Win: pick track, run starter, make first tool work | tracks/*/starter/ |
| 11:00–13:30 | Free hacking: extend toward challenges | tracks/*/challenges/ |
| 13:30–14:20 | Presentations | Live demo from their fork |
| 14:20–15:00 | Judging + (stretch) sim reveal | sim-reveal/ |
---
Kaggle Dataset for EmployMe
Suggested: LinkedIn Job Postings dataset (https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) — 124K job listings with title, description, skills, company, location. Reasons:
- Rich enough for vector semantic search (job description embeddings)
- Clean enough to seed into IRIS SQL tables in one script
- Natural fit for routing (job category → counsellor team)
- Multilingual challenge is realistic
seed_jobs.py would: download via kaggle CLI → load into IRIS SQL table → embed descriptions via IRIS EMBEDDING column → done.
---
Key Design Decisions
| Decision | Rationale |
|---|---|
| Vendor core/ instead of pip install | Avoids kit dependency; comment trail keeps migration path visible |
| IRISBackend abstraction with named constructors | One-line swap when Dave's binary or Aleks' AMP ships; attendees never touch internals |
| FastMCP bridge as Day-1 MCP path | Already working in this repo; no Build 125 dependency |
| iris_llm as Day-1 LLM path | Kit-installed, works today; llm_direct() fallback if team has API key issues |
| Both tracks use same core/ | Tech story is identical; only data + tools differ — judges can compare apples to apples |
| sim-reveal fully isolated | Stretch goal doesn't block anything; can be dropped with zero impact |
---
Three Questions Remaining Before Starting the Repo
1. Kaggle dataset — LinkedIn Job Postings OK, or do you have a different one in mind?
2. FHIR data — use the MIMIC data already seeded in ../ai-hub (MIMIC-CXR + radiology notes), or a simpler synthetic FHIR dataset so setup is faster for attendees?
3. Workshop slide deck — is that in scope for this repo (e.g. docs/workshop.md as speaker notes), or handled separately?
