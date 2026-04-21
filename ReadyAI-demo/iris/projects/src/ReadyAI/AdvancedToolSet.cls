Class ReadyAI.AdvancedToolSet Extends %AI.ToolSet [ dependsOn = (ReadyAI.Tools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.AdvancedToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Include Class="ReadyAI.Tools">
                <Filter Tool="ListTables"/>
                <Filter Tool="QueryTable"/>
            </Include>
            
</ToolSet>
}

}

