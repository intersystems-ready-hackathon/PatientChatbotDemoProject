Class Tools.ChatFHIRMedicationTool Extends %AI.Tool
{

Property Name As %String [ InitialExpression = "ChatFHIRMedicationTool" ];

// This method retrieves medication information for a list of patient IDs, e.g. ['Patient/1', 'Patient/2', 'Patient/3'] and returns it as a JSON string.
ClassMethod GetMedicationInfo(patientIds As %DynamicArray) As %String
{
    set output = []


        set l1 = "SELECT JSON_ARRAYAGG(JSON_OBJECT("
        set l2 = "'Patient':Patient, 'Code':Code, 'Description':Description, 'Status':Status, 'AuthoredOn':AuthoredOn))"
        set l3 = " AS MedicationInfo FROM ChatFHIR.MedicationRequest WHERE Patient=?"

        set query = l1_l2_l3

        w query,!

        set stmt = ##class(%SQL.Statement).%New()
        set qStatus =  stmt.%Prepare(query)

         if qStatus'=1 {
            do $System.Status.DisplayError(qStatus) 
            quit -1
        }

        for i=0:1:patientIds.%Size()-1 {

            set patient = patientIds.%Get(i)
            w patient,!
            set rs = stmt.%Execute(patient)
            w rs.%SQLCODE,!
            while rs.%Next() {
                
                set row = rs.%Get("MedicationInfo")
                do output.%Push(row)
            }
        }
    return output.%ToJSON()
}

}
