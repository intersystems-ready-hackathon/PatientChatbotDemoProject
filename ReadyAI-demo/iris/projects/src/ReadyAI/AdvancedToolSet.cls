
Class ReadyAI.AdvancedToolSet Extends %AI.ToolSet [ dependsOn = (ReadyAI.Tools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.AdvancedToolSet">
            <Description>Full access toolset to query patient FHIR data</Description>
            <Include Class="ReadyAI.Tools">
                <Filter Tool="ListTables"/>
                <Filter Tool="QueryTable"/>
            </Include>
            
</ToolSet>
}

}

