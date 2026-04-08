Class ReadyAI.Policies.AuditTable Extends %AI.Policy.Audit
{

Method %LogExecution(call As %DynamicObject, metadata As %DynamicObject, result As %DynamicObject, duration As %Integer, status As %Status) As %Status
{
    // Create a new log entry
    Set logEntry = ##class(ReadyAI.Policies.ToolLog).%New()
    Set logEntry.ToolName = call.%Get("name", "unknown")
    Set logEntry.ToolCall = call
    Set logEntry.Metadata = metadata
    Set logEntry.Result = result
    Set logEntry.Timestamp = $ZDATETIME($HOROLOG)
   Set logEntry.Duration = duration
    Set logEntry.Status = status
    set logEntry.Username = $USERNAME

    // Save the log entry to the database
    set st =  logEntry.%Save()
    if 'st {
      return $$$ERROR($$$AICoreToolAccessDenied, "Failed to save tool log: "_$SYSTEM.Status.GetErrorText(st))
    }

    Return $$$OK
}

}
