Class ReadyAI.ToolSet Extends %AI.ToolSet [ DependsOn=(ReadyAI.Tools.StandardTools,ReadyAI.Tools.FHIRSQLQueryTools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.ToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <Audit Class="ReadyAI.Audit.AuditTable" />
            </Policies>
            <Tool Name="EchoUser" Method="EchoUser" >
                <Description>Echo the current user's username and roles back to them.</Description>
            </Tool>

            <Include Class="ReadyAI.Tools.StandardTools"/>
            
            <Include Class="ReadyAI.Tools.FHIRSQLQueryTools">
                <Requirement Name="Role" Value="Doctor"/>
            </Include>
</ToolSet>
}

ClassMethod EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}

}
