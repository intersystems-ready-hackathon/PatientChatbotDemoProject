Class ReadyAI.Tools.FHIRSQLQueryTools Extends %AI.Tool
{

Parameter PackageName = "AFHIRData";

/// List the Availble tables in the FHIRData Schema
Method ListTables() As %DynamicObject
{
        Set sc = $$$OK

        set l1 = "SELECT JSON_ARRAYAGG(JSON_OBJECT"
        set l2 = "('TABLE_SCHEMA':TABLE_SCHEMA, 'TABLE_NAME':TABLE_NAME)) "
        set l3 = "AS tables FROM INFORMATION_SCHEMA.TABLES "
        set l4 = "WHERE TABLE_SCHEMA='"_..#PackageName_"'"
        set query = l1_l2_l3_l4
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)

        if $$$ISERR(status) {
            set sc = status
            do $System.Status.DisplayError(status)
            quit sc
        }
        set resultSet = statement.%Execute()

        do resultSet.%Next()
        set tables = resultSet.%Get("tables")

        Return {"Method": "ListTables", "Status":(sc), "Tables": (tables)}
}

/// Query a FHIRdata Table for all entries for a given Patient.
///  PatientId should be a single integer identifier
Method QueryTable(tableName As %String, patientId As %Integer) As %DynamicObject
{
        set response = {}
        set rows = []

        do response.%Set("Method", "QueryTable")
        do response.%Set("Table", tableName)
        do response.%Set("Rows", rows)

        if patientId="" {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "patientId must not be empty")
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
            set ^QueryTableLog($INCREMENT(^QueryTableLog)) = response.%ToJSON()
            quit response
        }

        if patientColumn="" {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", "No supported patient ID column found on table "_tableName)
            set ^QueryTableLog($INCREMENT(^QueryTableLog)) = response.%ToJSON()
            quit response
        }

        do response.%Set("PatientColumn", patientColumn)

        set query = "SELECT TOP 50 *  FROM "_..#PackageName_"."_tableName_" WHERE "_patientColumn_" = ?"
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            do response.%Set("Status", "ERROR")
            do response.%Set("Error", $System.Status.GetErrorText(status))
            set ^QueryTableLog($INCREMENT(^QueryTableLog)) = response.%ToJSON()
            quit response
        }

        set resultSet = statement.%Execute("Patient/"_patientId)

            while resultSet.%Next() {
                set row = {}

                for columnIndex=1:1:columnCount {
                    set columnName = columnNames(columnIndex)
                    do row.%Set(columnName, ##class(Utils.SafeString).SafeString(resultSet.%Get(columnName)))
                }

                do rows.%Push(row)
            }

        do response.%Set("Status", "OK")
        set ^QueryTableLog($INCREMENT(^QueryTableLog)) = response.%ToJSON()
        quit response
}

}
