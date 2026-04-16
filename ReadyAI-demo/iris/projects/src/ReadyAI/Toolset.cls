Class ReadyAI.ToolSet Extends %AI.ToolSet [ DependsOn = (ReadyAI.Tools.StandardTools, ReadyAI.Tools.AdvancedQueryTools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.ToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <Audit Class="ReadyAI.Policies.AuditTable" />
                <Authorization Class="ReadyAI.Policies.RoleAuth" />
                <Discovery Class="ReadyAI.Policies.Discovery" />
            </Policies>

            <Include Class="ReadyAI.Tools.StandardTools"/>

            <Include Class="ReadyAI.Tools.AdvancedQueryTools">
                <Requirement Name="Role" Value="Doctor"/>
            </Include>

</ToolSet>
}

}
