Class ReadyAI.FullAccessToolSet Extends %AI.ToolSet [ DependsOn = (ReadyAI.Tools.StandardTools, ReadyAI.Tools.FHIRSQLQueryTools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.FullAccessToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <Audit Class="ReadyAI.Policies.AuditTable" />
                <Authorization Class="ReadyAI.Policies.RoleAuth" />
                
            </Policies>

            <Include Class="ReadyAI.Tools.FHIRSQLQueryTools"/>

</ToolSet>
}

}
