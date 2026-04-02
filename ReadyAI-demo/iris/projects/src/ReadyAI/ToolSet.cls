Class ReadyAI.ToolSet Extends %AI.ToolSet [compileafter=Utils.EchoUser]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.ToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <Audit Class="ReadyAI.Audit.AuditTable" />
            </Policies>
            <Include Class="Utils.EchoUser"/>

            <Include Class="ReadyAI.Tools.StandardTools"/>
            
            <Include Class="ReadyAI.Tools.FHIRSQLQueryTools">
                <Requirement Name="Role" Value="Doctor"/>
            </Include>
</ToolSet>
}

}
