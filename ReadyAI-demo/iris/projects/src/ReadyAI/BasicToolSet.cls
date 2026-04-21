Class ReadyAI.BasicToolSet Extends %AI.ToolSet [ dependsOn = (ReadyAI.Tools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.BasicToolSet">
            <Description>ToolSet for READYAI demo</Description>

            <Include Class="ReadyAI.Tools">
                <Filter Tool="ListAllergies"/>
                <Filter Tool="ListMedications"/>
                <Filter Tool="ListPatientsBySurname"/>
            </Include>
            
</ToolSet>
}

}
