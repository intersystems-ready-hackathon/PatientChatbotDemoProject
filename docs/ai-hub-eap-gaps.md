# AI Hub EAP Documentation Gaps

**Context:** Gaps specific to the AI Hub SDK, `iris-mcp-server`, `langchain-intersystems`, and ConfigStore discovered while building the READY 2026 hackathon demo.

**See also:** [Gabriel's suggested improvements](ai-hub-suggested-improvements.md) on the `GI` branch — covers MCP ConfigStore per-user auth, VectorStore/%AI.RAG incompatibility, %AI.RAG flexibility, and %AI.QueryTool. This document does not duplicate those items.

**Date:** 2026-04-01

---

## What the EAP Docs Got Right

Credit where due — these sections saved us significant time:

- **`MCP_Server_Guide.md`** — The full TOML reference is excellent. We could copy-paste and adjust.
- **`MCP_Server_Examples.md`** — The `Security.Applications.Create` with `AutheEnabled=64, Type=18` was the key to making discovery work.
- **`ObjectScript_SDK_Guide.md`** — The `%AI.ToolSet` XData pattern with `<Requirement>` and `<Include>` was clear and worked first try.
- **`langchain_SDK.md`** — The 4-step demo (init_chat_model → init_mcp_client → create_agent → ainvoke) was exactly right. Short, complete, and it works.

---

## P1: Blocking (Participants Will Fail Without These)

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

**Note:** Gabriel's item #1 (MCP ConfigStore per-user auth) is a related but separate issue — he's requesting dynamic user injection into MCP configs; we're asking for the basic Wallet integration to be documented.

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

---

## P2: Significant Time Savings

### 4. `iris-mcp-server` Large Response Corruption

**Current state:** Not documented.

**What happens:** Tool responses larger than ~15KB are corrupted by the `iris-mcp-server 2.0.0` WebSocket backchannel. The error message is misleading: `"Corrupt UTF-8 in IRIS response at byte 1"`. This is NOT a UTF-8 encoding issue — it's a binary WebSocket frame being parsed as text.

**Workaround:** Add `TOP N` to SQL queries in tools to limit response size. We use `TOP 50`.

**Recommendation:** Add to `MCP_Server_Guide.md` → Troubleshooting:
> **Problem:** `Corrupt UTF-8 in IRIS response` when calling tools that return large results. Limit query results (e.g., `SELECT TOP 50 ...`) or paginate large responses.

### 5. Agent Streaming Output Pattern

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

### 6. Connection Pool Sizing for Limited Licenses

**Current state:** `MCP_Server_Guide.md` has a Connection Pool Sizing section but doesn't mention license constraints.

**What we discovered:** `pool = { min = 5, max = 10 }` (the example default) immediately exhausts a development license (5 slots). We had to use `pool = { min = 1, max = 3 }`.

**Recommendation:** Add a note:
> **Development licenses:** Set `min = 1` to avoid exhausting limited license slots. Each pool connection consumes one IRIS license slot.

---

## P3: Nice to Have

### 7. `%AI.Tools.SQL` vs Custom SQL Tools

We wrote custom `SQLTools.cls` because we needed FHIR-specific patient ID resolution. In hindsight, `%AI.Tools.SQL` with `<Requirement Name="ReadOnly" Value="1"/>` may have been sufficient.

**Note:** Gabriel's item #4 (%AI.QueryTool) proposes a related enhancement — auto-serialising class queries into tools. Both suggest the built-in SQL tool story needs more examples.

---

## Undocumented APIs (No Documentation Anywhere)

| Gap | What's needed | Owner |
|---|---|---|
| `%ConfigStore.Configuration` API | Class reference + Create/Get/Delete methods + category hierarchy | AI Hub team |
| `secret://` URI syntax | How ConfigStore resolves Wallet references | AI Hub team |
| `iris-mcp-server` WebSocket backchannel | When large responses trigger binary framing vs text | MCP Server team |
| `AutheEnabled` bitmask values for `Security.Applications` | What 1, 4, 64, 96 mean and when to use each | AI Hub or IRIS Security team |
| `%Wallet.Collection` naming validation rules | The PATTERN constraint and why dots are rejected | IRIS Platform team |

---

## Action Items

| # | Action | Suggested Owner | Priority |
|---|---|---|---|
| 1 | Add ConfigStore + Wallet API key pattern to `langchain_SDK.md` | Benjamin/Dave | P1 |
| 2 | Add `AutheEnabled=64` explanation to MCP Server Guide | Benjamin/Dave | P1 |
| 3 | Add explicit whl download instructions to `langchain_SDK.md` | Aohan | P1 |
| 4 | Add large response workaround to MCP Server troubleshooting | MCP team | P2 |
| 5 | Add agent streaming pattern to `langchain_SDK.md` | Aohan | P2 |
| 6 | Add pool sizing note for dev licenses | Benjamin/Dave | P2 |
| 7 | Add `%AI.Tools.SQL` + FHIR example | Gabriel/Tom | P3 |
