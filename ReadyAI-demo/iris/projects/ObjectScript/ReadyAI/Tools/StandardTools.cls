Class ReadyAI.Tools.StandardTools Extends %AI.Tool
{

/// Search for a patient based on their surname
/// Use this to find the patient ID which can be used for other queries
Method SearchForPatient(PatientSurname As %String) As %DynamicObject
{
        set query = "SELECT ID, GivenName, FamilyName, BirthDate FROM AFHIRData.Patient WHERE FamilyName = ?"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error preparing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set resultSet = statement.%Execute(PatientSurname)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error executing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set results = []
        while resultSet.%Next() {
            set patientId = resultSet.%Get("ID")
            set givenName = resultSet.%Get("GivenName")
            set familyName = resultSet.%Get("FamilyName")
            set birthDate = resultSet.%Get("BirthDate")
            set patientInfo = {"ID": (patientId), "GivenName": (givenName), "FamilyName": (familyName), "BirthDate": (birthDate)}
            do results.%Push(patientInfo)
        }
        quit results
}

/// Search for allergy information for a patient based on their patient ID. 
Method QueryPatientAllergies(PatientID As %Integer) As %DynamicObject
{

        set patientReference = "Patient/"_PatientID
        set l1 = "SELECT TOP 50 AllergyDescription, Category, Code, Criticality, "
        set l2 = "StatusVerificationStatus FROM AFHIRData.AllergyIntolerance WHERE Patient=?"
        set query = l1_l2
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error preparing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set resultSet = statement.%Execute(patientReference)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error executing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set results = []
        while resultSet.%Next() {
            set allergyDescription = resultSet.%Get("AllergyDescription")
            set category = resultSet.%Get("Category")
            set code = ##class(ReadyAI.Tools.Utils).SafeString(resultSet.%Get("Code"))
            set criticality = ##class(ReadyAI.Tools.Utils).SafeString(resultSet.%Get("Criticality"))
            set statusVerificationStatus = ##class(ReadyAI.Tools.Utils).SafeString(resultSet.%Get("StatusVerificationStatus"))
            set allergyInfo = {"AllergyDescription": (allergyDescription), "Category": (category), "Code": (code), "Criticality": (criticality), "StatusVerificationStatus": (statusVerificationStatus)}
            do results.%Push(allergyInfo)
        }
        quit results
}

/// Search for medication information for a patient based on their patient ID.
Method QueryMedications(PatientId As %Integer) As %DynamicObject
{
        set patientReference = "Patient/"_PatientId
        set l1 = "SELECT TOP 50 MedicationRequestAuthoredOn, MedicationDescription, "
        set l2 = " FROM AFHIRData.MedicationRequest WHERE Patient=?"
        set l3 = "ORDER BY MedicationRequestAuthoredOn DESC" 
        set query = l1_l2
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error preparing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set query = l1_l2_l3
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do $System.Status.DisplayError(status)
            quit {"status":"Error executing SQL statement", "Details": ($System.Status.GetErrorText(status))}
        }
        set results = []
        set resultSet = statement.%Execute(patientReference)
        while resultSet.%Next() {
            set medicationRequestAuthoredOn = resultSet.%Get("MedicationRequestAuthoredOn")
            set medicationDescription = ##class(ReadyAI.Tools.Utils).SafeString(resultSet.%Get("MedicationDescription"))
            set medicationInfo = {"MedicationRequestAuthoredOn": (medicationRequestAuthoredOn), "MedicationDescription": (medicationDescription)}
            do results.%Push(medicationInfo)
        }
        quit results
}

}
