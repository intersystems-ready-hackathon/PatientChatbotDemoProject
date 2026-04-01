Class ReadyAI.Audit.AuditTable Extends %AI.Policy.Audit
{

Method %LogExecution(call As %DynamicObject, metadata As %DynamicObject, result As %DynamicObject, duration As %Integer, status As %Status) As %Status
{
    // Create a new log entry
    set ^toolLog(1) = "True"
    
    Set logEntry = ##class(ReadyAI.Audit.ToolLog).%New()
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
        set ^toolLog(2) = $SYSTEM.Status.GetErrorText(st)
        return $$$ERROR($$$AICoreToolAccessDenied, "Failed to save tool log: "_$SYSTEM.Status.GetErrorText(st))
    }

    Return $$$OK
}

}
