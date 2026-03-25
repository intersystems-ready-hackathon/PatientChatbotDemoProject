Class ReadyAI.SQLTools Extends %AI.Tool
{

Parameter PackageName = "FHIRData";

/// Description
Method ListTables() As %Status
{
        Set sc = $$$OK
        // do something

        set query = "SELECT JSON_ARRAYAGG(JSON_OBJECT('TABLE_SCHEMA':TABLE_SCHEMA, 'TABLE_NAME':TABLE_NAME)) AS tables FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='"_..#PackageName_"'"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            set sc = status
            do $System.Status.DisplayError(status)
            quit sc
        }
        set resultSet = statement.%Execute()

        
        set tables = resultSet.%Get("tables")
        write tables 
        Return {"Method": "ListTables", "Status":(sc), "Tables": (tables)}
}

// Query a FHIRdata Table for all entries for a given list of Patients. PatientIds should be passed as a list of patient identifiers

// in the format Patient/1, Patient/2, etc. 

Method QueryTable(tableName As %String, patientIds As %DynamicArray(ELEMENTTYPE="%String")) As %DynamicObject
{
        set response = {}
        set rows = []

        do response.%Set("Method", "QueryTable")
        do response.%Set("Table", tableName)
        do response.%Set("Rows", rows)

        if '$IsObject(patientIds) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "patientIds must be a dynamic array")
            quit response
        }
        if patientIds.%Size()=0 {
            do response.%Set("Status", "OK")
            do response.%Set("PatientColumn", "")
            quit response
        }
        set metadataQuery = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION"
        set metadataStatement = ##class(%SQL.Statement).%New()
        set status = metadataStatement.%Prepare(metadataQuery)
        if $$$ISERR(status) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", $System.Status.GetErrorText(status))
            quit response
        }
        set metadataResult = metadataStatement.%Execute(..#PackageName, tableName)
        set columnCount = 0
        set patientColumn = ""

        while metadataResult.%Next() {
            set columnCount = columnCount + 1
            set columnNames(columnCount) = metadataResult.%Get("COLUMN_NAME")

            if patientColumn="" {
                set currentColumn = columnNames(columnCount)
                if (currentColumn="Patient")!(currentColumn="patient")!(currentColumn="PatientId")!(currentColumn="patientId")!(currentColumn="PatientID")!(currentColumn="patientID") {
                    set patientColumn = currentColumn
                }
}
        }

        if columnCount=0 {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "Table not found in schema "_..#PackageName)
            quit response
        }

        if patientColumn="" {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "No supported patient ID column found on table "_tableName)
            quit response
        }

        do response.%Set("PatientColumn", patientColumn)

        set query = "SELECT * FROM "_..#PackageName_"."_tableName_" WHERE "_patientColumn_" = ?"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", $System.Status.GetErrorText(status))
            quit response
        }

        for i=0:1:patientIds.%Size()-1 {
            set patientId = patientIds.%Get(i)
            set resultSet = statement.%Execute(patientId)

            while resultSet.%Next() {
                set row = {}

                for columnIndex=1:1:columnCount {
                    set columnName = columnNames(columnIndex)
                    do row.%Set(columnName, resultSet.%Get(columnName))
                }

                do rows.%Push(row)
            }
        }

        do response.%Set("Status", "OK")
        quit response
}

Method GetPatientsByCondition(pConditionCode As %Integer) As %DynamicObject
{

        set response = {}
        set patients = []
    
        do response.%Set("Method", "GetPatientsByCondition")
        do response.%Set("ConditionCode", pConditionCode)
        do response.%Set("Patients", patients)
    
        if pConditionCode="" {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "Condition code is required")
            quit response
        }
    
        set query = "SELECT DISTINCT Patient FROM "_..#PackageName_"."_"Condition WHERE SnomedCode = ?"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", $System.Status.GetErrorText(status))
            quit response
        }
        set resultSet = statement.%Execute(pConditionCode)

        while resultSet.%Next() {
            set patientId = resultSet.%Get("Patient")
            do patients.%Push(patientId)
        }

        do response.%Set("Status", "OK")
        quit response
}

Method GetConditionsList()
{
        set response = {}
        set conditions = []
    
        do response.%Set("Method", "GetConditionsList")
        do response.%Set("Conditions", conditions)
    
        set query = "SELECT DISTINCT SnomedCode, Description FROM "_..#PackageName_"."_"Condition"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", $System.Status.GetErrorText(status))
            quit response
        }
        set resultSet = statement.%Execute()

        while resultSet.%Next() {
            set conditionCode = resultSet.%Get("SnomedCode")
            set conditionDescription = resultSet.%Get("Description")
            set condition = {"Code": (conditionCode), "Description": (conditionDescription)}
            do conditions.%Push(condition)
        }

        do response.%Set("Status", "OK")
        quit response
}

}
