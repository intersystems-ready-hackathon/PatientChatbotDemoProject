Class ReadyAI.StandardToolSet Extends %AI.ToolSet
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.StandardToolSet">
        <Description>Standard ToolSet for READYAI demo</Description>
        <Policies>
            <Audit Class="ReadyAI.Policies.AuditTable" />
        </Policies>

        <Tool Name="EchoUser" Method="EchoUser" >
            <Description>Echo the current user's username and roles back to them.</Description>
        </Tool>

        <Query
        Name="FindPatientsBySurname"
            Type="SQL"
            Description="Find patients by their surname"
            Arguments="patientSurname As %String"
            MaxRows="50"
        >
        SELECT ID, GivenName, FamilyName, BirthDate 
        FROM AFHIRData.Patient WHERE FamilyName = :patientSurname
        </Query>

        <Query
        Name="QueryAllergies"
            Type="SQL"
            Description="Find allergies for a patient based on their patient ID"
            Arguments="patientId As %Integer"
            MaxRows="50">
        SELECT TOP 50 AllergyDescription, Category, Code, Criticality, Status, VerificationStatus
        FROM AFHIRData.AllergyIntolerance WHERE Patient=CONCAT('Patient/', :patientId)
        </Query>

        <Query
        Name="QueryMedications"
            Type="SQL"
            Description="Find medications for a patient based on their patient ID"
            Arguments="patientId As %Integer"
            MaxRows="50">
        SELECT TOP 50 Description, Code, AuthoredOn
        FROM AFHIRData.MedicationRequest WHERE Patient=CONCAT('Patient/', :patientId)
        </Query>
    </ToolSet>
}

ClassMethod EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}

}
