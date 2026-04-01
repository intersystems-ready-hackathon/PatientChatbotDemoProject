# AI Hub EAP Documentation Gap Analysis

**Context:** While building the READY 2026 hackathon demo (Patient Encounter Briefing Tool), we relied heavily on the [AI Hub EAP repo](https://github.com/intersystems/ai-hub-eap) documentation. This document captures what worked, what was missing, and what EAP doc additions would help hackathon participants (and future AI Hub users) succeed.

**Audience for this doc:** Gabriel (demo co-author), Dave/Benjamin (AI Hub EAP owners)

**Date:** 2026-03-31

---

## What We Built

A Streamlit web app where a clinician selects a patient, and an LLM agent queries FHIR data via MCP tools and generates a patient snapshot. The stack:

- **IRIS for Health** (IRISHealth-2026.2.0AI.142.0) with FHIR SQL Builder
- **iris-mcp-server 2.0.0** (HTTP transport) exposing ObjectScript tools
- **langchain-intersystems 0.0.1** (`init_chat_model`, `init_mcp_client`)
- **LangGraph agent** with `create_agent` from `langchain.agents`
- **ConfigStore + Wallet** for LLM credential management

---

## EAP Docs We Used Successfully

These sections were accurate and directly applicable:

| EAP Doc | Section | What we used |
|---|---|---|
| `ObjectScript_SDK_Guide.md` | Building Tools | `%AI.Tool` subclass pattern for `SQLTools.cls` |
| `ObjectScript_SDK_Guide.md` | Building ToolSets | `%AI.ToolSet` XData with `<Requirement Name="Role">` for Doctor/Nurse RBAC |
| `MCP_Server_Guide.md` | Quick Start | `%AI.MCP.Service` subclass + CSP web app registration |
| `MCP_Server_Guide.md` | Configuration | `config.toml` with `[[iris]]` blocks, `endpoints`, `pool` |
| `MCP_Server_Examples.md` | Programmatic CSP app creation | `AutheEnabled=64` pattern (line 48) — this was critical |
| `langchain_SDK.md` | Full demo | `init_chat_model`, `init_mcp_client`, `create_agent` |

---

## Part A: AI Hub EAP Documentation Gaps

These gaps are specific to the AI Hub SDK, `iris-mcp-server`, `langchain-intersystems`, and ConfigStore — i.e., the content owned by the AI Hub team.

### P1: Blocking

#### 1. ConfigStore + Wallet: Storing API Keys Securely

**Current state:** `langchain_SDK.md` references `ConfigStoreTest.cls` for setup but doesn't show the Wallet integration pattern. The `secret://` URI syntax for referencing Wallet secrets from ConfigStore is undocumented.

**What we had to figure out:**
```objectscript
// Step 1: Create Wallet collection and store the key
Do ##class(%Wallet.Collection).Create("ReadyAI-Secrets", {
    "UseResource": "ReadyAI.UseResource",
    "EditResource": "ReadyAI.EditResource"
})
Do ##class(%Wallet.KeyValue).Create("ReadyAI-Secrets.OpenAI", {
    "Usage": "CUSTOM",
    "Secret": {"api_key": (pAPIKey)}
})

// Step 2: Reference the Wallet secret from ConfigStore
set llmConfig = {
    "model_provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "secret://ReadyAI-Secrets.OpenAI#api_key"
}
Do ##class(%ConfigStore.Configuration).Create("AI", "LLM", "", "readyai", llmConfig)
```

**What the doc needs:** A complete "Storing API Keys in the IRIS Wallet" section in `langchain_SDK.md` showing:
- Wallet collection naming rules (must match pattern `1(1"%",1A).(1AN,1"-",1"_")` — dots not allowed!)
- The `secret://CollectionName.KeyName#field` URI syntax
- How `init_chat_model` resolves the secret at runtime
- How to seed from an environment variable (the `OPENAI_API_KEY → Wallet → ConfigStore` pattern)

#### 2. `AutheEnabled=64` for MCP Web Applications

**Current state:** `MCP_Server_Examples.md` shows `AutheEnabled=64` on line 48 but doesn't explain WHY this specific value is required.

**What happens without it:** If you use `AutheEnabled=4` (Password/Basic auth), `iris-mcp-server` tool discovery fails with HTTP 401 because the server uses wgproto delegated auth (not Basic auth) for its internal discovery calls to `/v1/services`.

**What the doc needs:** In `MCP_Server_Guide.md` → "Configure Web Application", add:

> **Important:** Set `AutheEnabled=64` (delegated authentication) on the CSP web application. The `iris-mcp-server` uses the Web Gateway protocol (wgproto) for tool discovery, which authenticates via delegated session tokens — not HTTP Basic auth. Using `AutheEnabled=4` (Password only) will cause tool discovery to fail with 401.

#### 3. `langchain_intersystems` Whl Distribution

**Current state:** The README says "download from the EAP portal" but `langchain_SDK.md` doesn't have a direct link or version-specific instructions.

**What the doc needs:** Explicit instructions:
```
1. Download langchain_intersystems-0.0.1-py3-none-any.whl from the EAP portal
2. pip install ./langchain_intersystems-0.0.1-py3-none-any.whl
3. Also install: pip install mcp langchain-openai
```

And note: the whl has no upper bound on `mcp`, so pip will install the latest. This is fine for Python 3.11 but causes issues on Python 3.14.

### P2: Significant Time Savings

#### 4. `iris-mcp-server` Large Response Bug

**Current state:** Not documented.

**What happens:** Tool responses larger than ~15KB are corrupted by the `iris-mcp-server 2.0.0` WebSocket backchannel. The error message is misleading: `"Corrupt UTF-8 in IRIS response at byte 1: invalid utf-8 sequence of 1 bytes from index 1"`. This is NOT a UTF-8 encoding issue — it's a binary WebSocket frame being parsed as text.

**Workaround:** Add `TOP N` to SQL queries in tools to limit response size. We use `TOP 50`.

**Recommendation:** Add to `MCP_Server_Guide.md` → Troubleshooting:
> **Problem:** `Corrupt UTF-8 in IRIS response` when calling tools that return large results
>
> This occurs when a tool response exceeds the WebSocket frame buffer. Limit query results (e.g., `SELECT TOP 50 ...`) or paginate large responses. A fix is planned for a future iris-mcp-server release.

#### 5. Agent Streaming Output Pattern

**Current state:** `langchain_SDK.md` shows `agent.ainvoke()` (blocking) but not streaming.

**What we needed for Streamlit:**
```python
async for chunk in agent.astream(
    {"messages": [HumanMessage(content=prompt)]},
    stream_mode="messages",
):
    message, metadata = chunk
    if message.type not in ("ai", "AIMessageChunk"):
        continue  # skip tool results, only yield LLM text
    for block in message.content_blocks:
        if block["type"] == "text":
            yield block["text"]
```

**Key gotcha:** `stream_mode="messages"` yields ALL message types (AI, Tool, Human). Without filtering on `message.type`, raw tool JSON leaks into the UI output.

#### 6. Connection Pool Sizing for Limited Licenses

**Current state:** `MCP_Server_Guide.md` has a Connection Pool Sizing section but doesn't mention license constraints.

**What we discovered:** `pool = { min = 5, max = 10 }` (the example default) immediately exhausts a development license (5 slots). We had to use `pool = { min = 1, max = 3 }`.

**Recommendation:** Add a note:
> **Development licenses:** Set `min = 1` to avoid exhausting limited license slots. Each pool connection consumes one IRIS license slot.

### P3: Nice to Have

#### 7. `%AI.Tools.SQL` vs Custom SQL Tools

The EAP docs show `%AI.Tools.SQL` as a built-in. We wrote custom `SQLTools.cls` instead because we needed FHIR-specific patient ID resolution and the `AFHIRData` schema prefix. In hindsight, we could have used `%AI.Tools.SQL` with `<Requirement Name="ReadOnly" Value="1"/>` and let the LLM figure out the schema.

**Recommendation:** Add an example of `%AI.Tools.SQL` with a FHIR SQL Builder schema, showing that the built-in tool is often sufficient.

---

## Part B: Non-AI-Hub Gaps (IRIS Platform / HealthShare / Infrastructure)

These gaps are not in the AI Hub EAP's scope but caused significant friction during development. They relate to general IRIS platform behavior, HealthShare/FHIR SQL Builder, and Docker infrastructure.

### P1: Blocking

#### 8. Docker Image: IRIS vs IRISHealth

**Current state:** The EAP README shows `iris-2026.2.0AI.141.0` (plain IRIS). No mention of IRISHealth.

**What we discovered:** For FHIR SQL Builder, you MUST use an `IRISHealth` kit (e.g., `IRISHealth-2026.2.0AI.142.0`). The plain IRIS kit doesn't include `HS.FHIRServer.*`, `HS.HC.FHIRSQL.*`, or the FHIR SQL Builder UI.

**Where this belongs:** The EAP README could add a note, but the real owner is the IRIS platform/packaging team. The IRISHealth AI variant should be listed on the EAP portal alongside the plain IRIS one.

### P2: Significant Time Savings

#### 9. FHIR SQL Builder Programmatic Setup

**Current state:** Not documented anywhere — not in EAP docs, not in HealthShare docs, not in FHIR SQL Builder docs. The FHIR SQL Builder has a REST API at `/csp/fhirsql/api/ui/v1/...` but it's undocumented.

**What we had to build:** `FSBSetup.cls` which:
1. Calls `HS.FHIRServer.Installer.InstallNamespace("READYAI")`
2. Calls `HS.FHIRServer.Installer.InstallInstance(appKey, strategyClass, metadataPackages)`
3. Starts the Ensemble production (`Ens.Director.StartProduction`)
4. Loads FHIR data via `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles`
5. Enables `/csp/fhirsql/api/ui` and `/csp/fhirsql/api/repository` CSP apps
6. Grants `FSB_Admin`, `FSB_Analyst`, `FSB_Data_Steward` roles to users
7. Drives the REST API: POST credentials → POST fhirrepository → POST analysis (wait) → POST transformspec → POST projection

**Where this belongs:** HealthShare / FHIR SQL Builder documentation. Not AI Hub EAP scope.

**Existing docs:** [FHIR SQL Builder](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=FHIRSQL) has 6 sections (Introduction, Generate Schema, Access the Builder, Analyze Repo, Create Specification, Create Projection) — all describe the **UI workflow only**. [Install FHIR Server](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install) documents `HS.FHIRServer.Installer` but not the SQL Builder REST endpoints. **No programmatic/REST API documentation exists.**

#### 10. `%Service_Bindings` Auth for Non-Privileged Users

**What we discovered:** Non-`%All` users cannot connect via the Python DB-API (`iris.connect`) unless `%Service_Bindings` has the correct authentication bits set. The `aicore-iris:140` base image had `AutheEnabled=96` (Kerberos-only) on `%Service_Bindings`, which meant only `%All` users could connect. We worked around this by giving Doctor/Nurse the `%All` role.

**Where this belongs:** IRIS platform documentation on `%Service_Bindings` and the DB-API driver. Not AI Hub EAP scope.

**Existing docs:** [Managing Services](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services) covers service configuration. [Authentication Overview](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AAUTHN) covers auth mechanisms. [Python DB-API intro](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=BPYDBAPI_about) covers connection setup. **None connect the dots:** "to connect via Python DB-API, `%Service_Bindings` must have password auth enabled for non-%All users."

#### 11. Ensemble Production Must Be Started for FHIR Data Loading

`Ens.Director.StartProduction()` must be called before `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles()`. Without it, the data loader silently does nothing.

**Where this belongs:** HealthShare FHIR Server documentation.

**Existing docs:** [Install FHIR Server](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install) likely mentions this implicitly — the production is started as part of `HS.FHIRServer.Installer.InstallNamespace`. But the `DataLoader.SubmitResourceFiles` prerequisite for a running production **is not called out explicitly**.

### P3: Nice to Have

#### 12. IPM Package with `WebApplication` Element

We used `module.xml` to auto-register the CSP web app during `zpm load`:
```xml
<WebApplication
    Url="/mcp/readyAI"
    AutheEnabled="64"
    DispatchClass="ReadyAI.MCPService"
    MatchRoles=":%All"
/>
```

This is cleaner than manual `Security.Applications.Create` calls. Worth documenting as a best practice.

**Where this belongs:** IPM / ZPM documentation.

**Existing docs:** No official docs.intersystems.com page. Best community resources: [Anatomy of a ZPM Module](https://community.intersystems.com/post/anatomy-zpm-module-packaging-your-intersystems-solution), [Describing module.xml](https://community.intersystems.com/post/describing-module-xml-objectscript-package-manager), [ZPM + CSP pages](https://community.intersystems.com/post/zpm-adding-csp-pages-existing-namespace). The [IPM GitHub repo](https://github.com/intersystems/ipm) has some docs but **no formal reference for the `WebApplication` XML element**.

---

## Existing docs.intersystems.com References (for cross-linking)

| Topic | URL | Coverage |
|---|---|---|
| IRIS containers | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK | Good — but no IRIS vs IRISHealth comparison |
| IRIS for Health containers | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK | Separate doc set — implies IRISHealth is different |
| Container Registry | https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=PAGE_containerregistry | Lists both image types |
| Managing Services | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services | `%Service_Bindings` config |
| Authentication mechanisms | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AAUTHN | AutheEnabled bitmask values |
| Python DB-API | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=BPYDBAPI_about | Connection setup |
| CSP web application config | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCSP_appdef | AutheEnabled for CSP apps |
| FHIR SQL Builder | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=FHIRSQL | UI workflow only |
| Install FHIR Server | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install | `HS.FHIRServer.Installer` |
| Secrets Management (Wallet) | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ROARS_secrets_mgmt | `%Wallet` API |

---

## Things the EAP Docs Got Right

Credit where due — these sections saved us significant time:

- **`MCP_Server_Guide.md`** — The full TOML reference is excellent. We could copy-paste and adjust.
- **`MCP_Server_Examples.md`** — The `Security.Applications.Create` with `AutheEnabled=64, Type=18` was the key to making discovery work.
- **`ObjectScript_SDK_Guide.md`** — The `%AI.ToolSet` XData pattern with `<Requirement>` and `<Include>` was clear and worked first try.
- **`langchain_SDK.md`** — The 4-step demo (init_chat_model → init_mcp_client → create_agent → ainvoke) was exactly right. Short, complete, and it works.

---

## Action Items

### Part A: AI Hub EAP team (Benjamin/Dave/Aohan)

| # | Action | Suggested Owner | Priority |
|---|---|---|---|
| 1 | Add ConfigStore + Wallet API key pattern to `langchain_SDK.md` | Benjamin/Dave | P1 |
| 2 | Add `AutheEnabled=64` explanation to MCP Server Guide | Benjamin/Dave | P1 |
| 3 | Add explicit whl download instructions to `langchain_SDK.md` | Aohan | P1 |
| 4 | Add large response workaround to MCP Server troubleshooting | MCP team | P2 |
| 5 | Add agent streaming pattern to `langchain_SDK.md` | Aohan | P2 |
| 6 | Add pool sizing note for dev licenses | Benjamin/Dave | P2 |
| 7 | Add `%AI.Tools.SQL` + FHIR example | Gabriel/Tom | P3 |

### Part B: Outside AI Hub EAP scope (IRIS platform / HealthShare / IPM)

| # | Action | Area | Priority |
|---|---|---|---|
| 8 | List IRISHealth AI variant on EAP portal | IRIS Packaging | P1 |
| 9 | Document FHIR SQL Builder REST API for programmatic setup | HealthShare / FHIR SQL Builder team | P2 |
| 10 | Document `%Service_Bindings` auth for non-%All DB-API users | IRIS Security docs | P2 |
| 11 | Document `Ens.Director.StartProduction` prerequisite for FHIR data loading | HealthShare FHIR Server docs | P2 |
| 12 | Document IPM `WebApplication` element for CSP app auto-registration | IPM / ZPM docs | P3 |

---

## Skills We Should Write

Based on what we actually struggled with during this session, these are the agent skills that would have saved the most time. Each maps to a specific failure mode we hit and the resolution we eventually found.

### Skill 1: `iris-security-prereqs` — IRIS Security Prerequisite Checker

**What went wrong:** We spent 2+ hours on `%Service_Bindings` `AutheEnabled=96` blocking non-%All users from connecting via DB-API. We tried every combination of `AutheEnabled` values, `Security.Applications.Modify`, `Security.Users.Create` with different role strings — none of which were the actual problem. The real fix was giving users `%All` (workaround) or changing `%Service_Bindings` auth (which we couldn't do from Python).

**What the skill does:** When an IRIS connection fails with "Access Denied" or similar, the skill:
1. Connects as SuperUser to check `%Service_Bindings`, `%Service_CallIn`, `%Service_Gateway` auth settings
2. Checks the target user's roles vs what the service requires
3. Checks the target namespace's `%DB_*` resource permissions
4. Reports the specific fix needed (which service, which auth bit, which role)

**Key doc links to embed:**
- https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services
- https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AAUTHN

**Gaps this doesn't cover:** The docs don't explain the `AutheEnabled` bitmask values for `%Service_Bindings` in the context of Python DB-API specifically. The skill needs to hardcode the knowledge that `AutheEnabled=96` = Kerberos-only = blocks password-based DB-API connections.

### Skill 2: `iris-mcp-server-setup` — MCP Server Configuration & Troubleshooting

**What went wrong:** We spent hours on:
- `iris-mcp-server` returning 0 tools (discovery failure) — root cause: `AutheEnabled=4` on the CSP app instead of `64`
- `CSPSystem` vs `SuperUser` in `config.toml` — CSPSystem had empty roles, couldn't access READYAI namespace
- WebSocket backchannel corruption on large responses — workaround: `TOP 50` in SQL

**What the skill does:** Given an `iris-mcp-server` config.toml and a running IRIS instance:
1. Verifies the CSP web app exists with `AutheEnabled=64`
2. Checks that the `server.username` in config.toml can access the endpoint namespace
3. Tests tool discovery via a direct wgproto call
4. If tools return 0: checks SPECIFICATION parameter, class compilation, namespace mapping
5. If tool calls fail: checks response size, suggests `TOP N` workaround

**Key doc links to embed:**
- The EAP `MCP_Server_Guide.md` (the full TOML reference is excellent)
- The EAP `MCP_Server_Examples.md` (the `AutheEnabled=64, Type=18` pattern)
- https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCSP_appdef

**Gaps this doesn't cover:** The large response corruption is a `iris-mcp-server 2.0.0` bug with no doc reference — the skill must encode the workaround directly.

### Skill 3: `fhir-sql-builder-setup` — FHIR SQL Builder Automation

**What went wrong:** We spent the longest single stretch (40+ minutes watching an analysis poll) because:
- No documentation for the REST API at `/csp/fhirsql/api/ui/v1/...`
- The first analysis errored (FHIR server not installed yet) and subsequent POSTs returned the old errored result
- We didn't know `Ens.Director.StartProduction()` was required before data loading
- The `HS.FHIRServer.Installer.InstallNamespace/InstallInstance` prerequisites weren't documented in the FSB context

**What the skill does:** Given an IRIS for Health instance with FHIR data loaded:
1. Checks prerequisites: `HS.FHIRServer.Installer` exists, production is running, FHIR endpoint exists
2. Enables FSB CSP apps (`/csp/fhirsql/api/ui`, `/csp/fhirsql/api/repository`) with correct auth
3. Grants `FSB_Admin/FSB_Analyst/FSB_Data_Steward` roles
4. Drives the REST API: credentials → fhirrepository → analysis (poll with correct ID) → transformspec → projection
5. Verifies `AFHIRData` tables are created

**Key doc links to embed:**
- https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=FHIRSQL
- https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install

**Gaps this doesn't cover:** The REST API is entirely undocumented. The skill must encode the endpoint paths, request/response formats, and polling logic from our `FSBSetup.cls` experience.

### Skill 4: `iris-configstore-wallet` — ConfigStore + Wallet Setup

**What went wrong:** We wrote `ConfigStoreSetup.cls` from scratch because:
- The `secret://` URI syntax was undocumented
- The Wallet collection naming rules (`1(1"%",1A).(1AN,1"-",1"_")` — no dots!) caused `ReadyAI.Secrets` to fail validation
- The `%ConfigStore.Configuration.Create` API signature (5 positional args: category, subcategory, subsubcategory, name, config) was hard to discover

**What the skill does:** Given a provider name, model, and API key:
1. Creates a Wallet collection with valid naming (replaces dots with hyphens)
2. Stores the API key in the Wallet
3. Creates a ConfigStore entry with `secret://` reference
4. Verifies the round-trip: `init_chat_model` can resolve the config and instantiate the model

**Key doc links to embed:**
- https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ROARS_secrets_mgmt
- The EAP `langchain_SDK.md` (the ConfigStoreTest.cls pattern)
- The EAP `ObjectScript_SDK_Guide.md` (Getting Started: API Key Setup)

**Gaps this doesn't cover:** The `%ConfigStore.Configuration` class API is not documented on docs.intersystems.com (it's new in the AI Hub EAP). The `secret://` URI syntax is entirely undocumented anywhere.

### Existing Skills That Should Be Updated

| Skill | What to add |
|---|---|
| `iris-python-connection` | Add: "If connection fails with Access Denied, check `%Service_Bindings` AutheEnabled — must include password auth for non-%All users" |
| `iris-kit-container` | Add: IRISHealth variant for FHIR/HealthShare use cases. Add: `iris-mcp-server` binary is in `dist/*/bin/` inside the tar |
| `iris-objectscript-eval` | Add: After `zpm load`, routines may not be compiled — run `$system.OBJ.CompilePackage("Package","ck")` explicitly |
| `ensemble-production` | Add: Production must be running before `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles` |

### Remaining Documentation Gaps (No Existing Docs to Link To)

These items have **no documentation anywhere** — not on docs.intersystems.com, not in the EAP, not in community posts:

| Gap | What's needed | Who should write it |
|---|---|---|
| `%ConfigStore.Configuration` API | Class reference + Create/Get/Delete methods + category hierarchy | AI Hub / IRIS Platform team |
| `secret://` URI syntax | How ConfigStore resolves Wallet references | AI Hub / IRIS Platform team |
| `iris-mcp-server` WebSocket backchannel behavior | When large responses trigger binary framing vs text framing | MCP Server team |
| FHIR SQL Builder REST API | Full endpoint reference for `/csp/fhirsql/api/ui/v1/*` | FHIR SQL Builder team |
| `AutheEnabled` bitmask values for `Security.Applications` | What each integer value means (1, 4, 64, 96, etc.) and when to use which | IRIS Security docs team |
| `%Wallet.Collection` naming validation rules | The PATTERN constraint and why dots are rejected | IRIS Platform team |
