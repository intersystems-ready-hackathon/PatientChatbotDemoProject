Class ReadyAI.ToolSet Extends %AI.ToolSet
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.ToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <!-- <Audit Class="ReadyAI.AuditTable" /> -->
                    <!-- <Audit Class="%AI.Policy.ConsoleAudit" /> -->
                <!-- <Authorization Class="%AI.Policy.ConsoleAuth"/> -->
                
            </Policies>
            <Include Class="ReadyAI.SQLTools">
                <Requirement Name="Role" Value="Doctor"/>
                <Requirement Name="ReadOnly" Value="1"/>
            </Include>
</ToolSet>
}

}
