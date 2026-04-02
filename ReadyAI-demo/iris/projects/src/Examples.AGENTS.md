# AGENTS.md — ObjectScript/Examples/

Reference implementations showing how to create MCP tools and toolsets.
Included in `ReadyAI.ToolSet` as the always-available `EchoUser` tool.

## Classes

| Class | Purpose |
|-------|---------|
| `EchoUser.cls` | Minimal `%AI.Tool` — returns current `$USERNAME`; always accessible (no role requirement) |
| `GetRoles.cls` | `Utils.GetRoles` — called from Python via `iris.createIRIS(conn).classMethodValue(...)` to determine user roles |
| `CompleteExampleToolset.cls` | Full-featured example ToolSet with all XML config patterns |
| `CompleteMCPService.cls` | Full-featured example MCP service definition |

## Usage

- `EchoUser` is the simplest possible `%AI.Tool` — copy it to create new tools
- `GetRoles` is called via the IRIS Native API from Python, not via MCP
- `CompleteExampleToolset` shows all available `<Requirement>`, `<Policy>`, `<Include>` XML patterns

## Python-side Role Check

```python
irispy = iris.createIRIS(conn)
roles = irispy.classMethodValue("Utils.GetRoles", "GetRoles")
# returns comma-separated role string, e.g. "Doctor,ReadOnly"
```
