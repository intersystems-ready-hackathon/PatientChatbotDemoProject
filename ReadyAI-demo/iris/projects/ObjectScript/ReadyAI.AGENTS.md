# AGENTS.md — ObjectScript/ReadyAI/

Core MCP tool implementations. All classes in the `ReadyAI` package.

## Classes

| Class | Extends | Purpose |
|-------|---------|---------|
| `MCPService.cls` | `%AI.MCP.Service` | MCP service stub; points to `ReadyAI.ToolSet` |
| `ToolSet.cls` | `%AI.ToolSet` | XData RBAC config: which tools, which roles |
| `SQLTools.cls` | `%AI.Tool` | FHIR SQL queries (ListTables, QueryTable, GetPatientsByCondition, GetConditionsList) |
| `Agent.cls` | `%AI.Agent` | IRIS-side agent stub (openai / gpt-5-nano) |
| `AuditTable.cls` | `%AI.Policy.Audit` | Logs every tool call to `ReadyAI.ToolLog` persistent |
| `ToolLog.cls` | `%Persistent` | Audit log storage: ToolName, Call, Result, Duration, Username |

## Adding a New Tool

1. Create `ReadyAI.MyTool.cls` extending `%AI.Tool`
2. Add `<Include Class="ReadyAI.MyTool"/>` in `ToolSet.cls` XData
3. Add `<Requirement Name="Role" Value="Doctor"/>` if Doctor-only

## RBAC

```xml
<Include Class="ReadyAI.SQLTools">
    <Requirement Name="Role" Value="Doctor"/>
    <Requirement Name="ReadOnly" Value="1"/>
</Include>
```

Role value must match an actual IRIS role (set up in `roleSetup.script`).

## SQL Pattern

- All queries use `%SQL.Statement` — never string-concatenated user input without validation
- Schema: `AFHIRData` (hardcoded in `PackageName` parameter)
- Patient column auto-detected: looks for `Patient`, `PatientId`, `PatientID` variants
- Responses always return `%DynamicObject` with `Method`, `Status`, and result keys

## Anti-Patterns

- Do NOT use `%SYSTEM.SQL.Execute` for dynamic queries — use `%SQL.Statement.%Prepare`
- Do NOT return raw `%Status` to the LLM — wrap in `%DynamicObject` response
- Do NOT add new classes to this package for examples — use `Examples/` package instead
