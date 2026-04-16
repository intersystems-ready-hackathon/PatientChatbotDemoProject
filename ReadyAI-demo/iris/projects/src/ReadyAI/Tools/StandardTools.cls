Class ReadyAI.Tools.StandardTools Extends %AI.Tool
{
    
Parameter STATEFUL = 0;

/// Lists patients by their surname
Query ListPatientsBySurname(surname As %String) As %SQLQuery(ROWSPEC="ID:%Integer, GivenName:%String, FamilyName:%String, BirthDate:%Date") [SqlProc]
{
        SELECT TOP 50 ID, GivenName, FamilyName, BirthDate 
        FROM AFHIRData.Patient WHERE FamilyName = :surname
}
/// Lists the current allergies for a patient based on their patient ID
Query ListAllergies(patientId As %Integer) As %SQLQuery(ROWSPEC="AllergyDescription:%String, Category:%String, Code:%String, Criticality:%String, Status:%String, VerificationStatus:%String") [SqlProc]
{
        SELECT TOP 50 AllergyDescription, Category, Code, Criticality, Status, VerificationStatus
        FROM AFHIRData.AllergyIntolerance WHERE Patient=CONCAT('Patient/', :patientId)
}

/// Lists the current medications for a patient based on their patient ID
Query ListMedications(patientId As %Integer) As %SQLQuery(ROWSPEC="Description:%String, Code:%String, AuthoredOn:%DateTime") [SqlProc]
{
        SELECT TOP 50 Description, Code, AuthoredOn
        FROM AFHIRData.MedicationRequest WHERE Patient=CONCAT('Patient/', :patientId)
}
}
