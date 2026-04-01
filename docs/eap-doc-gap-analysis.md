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

## Priority 1: Blocking Gaps (Participants Will Fail Without These)

### 1. ConfigStore + Wallet: Storing API Keys Securely

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

### 2. `AutheEnabled=64` for MCP Web Applications

**Current state:** `MCP_Server_Examples.md` shows `AutheEnabled=64` on line 48 but doesn't explain WHY this specific value is required.

**What happens without it:** If you use `AutheEnabled=4` (Password/Basic auth), `iris-mcp-server` tool discovery fails with HTTP 401 because the server uses wgproto delegated auth (not Basic auth) for its internal discovery calls to `/v1/services`.

**What the doc needs:** In `MCP_Server_Guide.md` → "Configure Web Application", add:

> **Important:** Set `AutheEnabled=64` (delegated authentication) on the CSP web application. The `iris-mcp-server` uses the Web Gateway protocol (wgproto) for tool discovery, which authenticates via delegated session tokens — not HTTP Basic auth. Using `AutheEnabled=4` (Password only) will cause tool discovery to fail with 401.

### 3. `langchain_intersystems` Whl Distribution

**Current state:** The README says "download from the EAP portal" but `langchain_SDK.md` doesn't have a direct link or version-specific instructions.

**What the doc needs:** Explicit instructions:
```
1. Download langchain_intersystems-0.0.1-py3-none-any.whl from the EAP portal
2. pip install ./langchain_intersystems-0.0.1-py3-none-any.whl
3. Also install: pip install mcp langchain-openai
```

And note: the whl has no upper bound on `mcp`, so pip will install the latest. This is fine for Python 3.11 but causes issues on Python 3.14.

### 4. Docker Image: IRIS vs IRISHealth

**Current state:** The EAP README shows `iris-2026.2.0AI.141.0` (plain IRIS). No mention of IRISHealth.

**What we discovered:** For FHIR SQL Builder, you MUST use an `IRISHealth` kit (e.g., `IRISHealth-2026.2.0AI.142.0`). The plain IRIS kit doesn't include `HS.FHIRServer.*`, `HS.HC.FHIRSQL.*`, or the FHIR SQL Builder UI.

**What the doc needs:** In the README "Accessing the software" section:
> If your use case involves FHIR data, download the **IRISHealth** variant of the kit. The plain IRIS kit does not include HealthShare classes (FHIR Server, FHIR SQL Builder). Both variants include the full AI Hub functionality.

---

## Priority 2: Significant Time Savings

### 5. FHIR SQL Builder Programmatic Setup

**Current state:** Not documented in EAP docs at all. The FHIR SQL Builder has a REST API at `/csp/fhirsql/api/ui/v1/...` but there's no documentation for driving it programmatically.

**What we had to build:** `FSBSetup.cls` which:
1. Calls `HS.FHIRServer.Installer.InstallNamespace("READYAI")`
2. Calls `HS.FHIRServer.Installer.InstallInstance(appKey, strategyClass, metadataPackages)`
3. Starts the Ensemble production (`Ens.Director.StartProduction`)
4. Loads FHIR data via `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles`
5. Enables `/csp/fhirsql/api/ui` and `/csp/fhirsql/api/repository` CSP apps with `AutheEnabled` matching `/api/mgmnt`
6. Grants `FSB_Admin`, `FSB_Analyst`, `FSB_Data_Steward` roles to users
7. Drives the REST API: POST credentials → POST fhirrepository → POST analysis (wait for completion) → POST transformspec → POST projection

**Recommendation:** Either document the FHIR SQL Builder REST API, or provide a reusable setup class like our `FSBSetup.cls`.

### 6. `iris-mcp-server` Large Response Bug

**Current state:** Not documented.

**What happens:** Tool responses larger than ~15KB are corrupted by the `iris-mcp-server 2.0.0` WebSocket backchannel. The error message is misleading: `"Corrupt UTF-8 in IRIS response at byte 1: invalid utf-8 sequence of 1 bytes from index 1"`. This is NOT a UTF-8 encoding issue — it's a binary WebSocket frame being parsed as text.

**Workaround:** Add `TOP N` to SQL queries in tools to limit response size. We use `TOP 50`.

**Recommendation:** Add to `MCP_Server_Guide.md` → Troubleshooting:
> **Problem:** `Corrupt UTF-8 in IRIS response` when calling tools that return large results
>
> This occurs when a tool response exceeds the WebSocket frame buffer. Limit query results (e.g., `SELECT TOP 50 ...`) or paginate large responses. A fix is planned for a future iris-mcp-server release.

### 7. Agent Streaming Output Pattern

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

### 8. Connection Pool Sizing for Limited Licenses

**Current state:** `MCP_Server_Guide.md` has a Connection Pool Sizing section but doesn't mention license constraints.

**What we discovered:** `pool = { min = 5, max = 10 }` (the example default) immediately exhausts a development license (5 slots). We had to use `pool = { min = 1, max = 3 }`.

**Recommendation:** Add a note:
> **Development licenses:** Set `min = 1` to avoid exhausting limited license slots. Each pool connection consumes one IRIS license slot.

---

## Priority 3: Nice to Have

### 9. IPM Package with `WebApplication` Element

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

### 10. `%AI.Tools.SQL` vs Custom SQL Tools

The EAP docs show `%AI.Tools.SQL` as a built-in. We wrote custom `SQLTools.cls` instead because we needed FHIR-specific patient ID resolution and the `AFHIRData` schema prefix. In hindsight, we could have used `%AI.Tools.SQL` with `<Requirement Name="ReadOnly" Value="1"/>` and let the LLM figure out the schema.

**Recommendation:** Add an example of `%AI.Tools.SQL` with a FHIR SQL Builder schema, showing that the built-in tool is often sufficient.

---

## Things the EAP Docs Got Right

Credit where due — these sections saved us significant time:

- **`MCP_Server_Guide.md`** — The full TOML reference is excellent. We could copy-paste and adjust.
- **`MCP_Server_Examples.md`** — The `Security.Applications.Create` with `AutheEnabled=64, Type=18` was the key to making discovery work.
- **`ObjectScript_SDK_Guide.md`** — The `%AI.ToolSet` XData pattern with `<Requirement>` and `<Include>` was clear and worked first try.
- **`langchain_SDK.md`** — The 4-step demo (init_chat_model → init_mcp_client → create_agent → ainvoke) was exactly right. Short, complete, and it works.

---

## Action Items

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add ConfigStore + Wallet API key pattern to `langchain_SDK.md` | Benjamin/Dave | P1 |
| 2 | Add `AutheEnabled=64` explanation to MCP Server Guide | Benjamin/Dave | P1 |
| 3 | Add explicit whl download instructions to `langchain_SDK.md` | Aohan | P1 |
| 4 | Document IRIS vs IRISHealth distinction for FHIR | Benjamin/Dave | P1 |
| 5 | Document FHIR SQL Builder programmatic setup | Gabriel/Tom | P2 |
| 6 | Add large response workaround to MCP Server troubleshooting | MCP team | P2 |
| 7 | Add agent streaming pattern to `langchain_SDK.md` | Aohan | P2 |
| 8 | Add pool sizing note for dev licenses | Benjamin/Dave | P2 |
| 9 | Document IPM WebApplication pattern | Gabriel | P3 |
| 10 | Add `%AI.Tools.SQL` + FHIR example | Gabriel/Tom | P3 |
