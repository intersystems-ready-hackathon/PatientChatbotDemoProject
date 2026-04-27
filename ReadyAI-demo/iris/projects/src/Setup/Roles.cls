Class Setup.Roles Extends %RegisteredObject
{

ClassMethod GrantExecute() As %Status
{
    new $NAMESPACE
    set $NAMESPACE = "READYAI"
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListPatientsBySurname TO Nurse")
    quit:$$$ISERR(sc) sc
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListMedications TO Nurse")
    quit:$$$ISERR(sc) sc
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListAllergies TO Nurse")
    quit:$$$ISERR(sc) sc
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListAllergies TO Doctor")
    quit:$$$ISERR(sc) sc
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListMedications TO Doctor")
    quit:$$$ISERR(sc) sc
    set sc = ..ExecuteGrant("GRANT EXECUTE ON ReadyAI.Tools_ListPatientsBySurname TO Doctor")
    quit:$$$ISERR(sc) sc
    q $$$OK
}


ClassMethod ExecuteGrant(sql As %String) As %Status
{
    set statement = ##class(%SQL.Statement).%New()
    set sc = statement.%Prepare(sql)
    if $$$ISERR(sc) {
        write "ERROR preparing SQL grant: ", sql, !
        do $SYSTEM.Status.DisplayError(sc)
        quit sc
    }

    set sc = $$$OK
    try {
        set result = statement.%Execute()
    } catch ex {
        set sc = ex.AsStatus()
    }

    if $$$ISERR(sc) {
        write "ERROR executing SQL grant: ", sql, !
        do $SYSTEM.Status.DisplayError(sc)
        quit sc
    }

    q $$$OK
}


ClassMethod Run() As %Status
{
    New $NAMESPACE
    set $NAMESPACE = "%SYS"

    do ##class(Security.Roles).Delete("Doctor")
    do ##class(Security.Users).Delete("DScully")
    do ##class(Security.Roles).Delete("Nurse")
    do ##class(Security.Users).Delete("NJoy")
    
    do ##class(Security.Users).Delete("Test")

    do ##class(Security.Resources).Create("MedicalAccess")
    
    do ##class(Security.Resources).Create("OpenAIUser")


    do ##class(Security.Roles).Create("Doctor", "Roles group for full access to a patients medical records and history", "", "",  )

    do ##class(Security.Roles).Get("Doctor", .props)
    set props("Resources")="%Native_ClassExecution:U,OpenAIUser:R,MedicalAccess:U"
    set sc = ##class(Security.Roles).Modify("Doctor", .props)
    do $SYSTEM.Status.DisplayError(sc)
    kill props

    set props("FullName")= "Dana Scully"
    set props("Password")="xfiles"
    set props("Roles")="Doctor,%DB_READYAI,%SQL,%HS_DB_READYAI,FSB_Analyst,%DB_HSPATIENT,%DB_HSLIB,%DB_HSREGISTRY,%DB_HSDATA"

    do ##class(Security.Users).Create("DScully", .props)

    w "Doctor user DScully created with access to patient records and OpenAI API",!


    kill props
    do ##class(Security.Roles).Create("Nurse", "Roles group for partial access to a patients medical history", "", "",  )
    do ##class(Security.Roles).Get("Nurse", .props)
    set props("Resources")="%Native_ClassExecution:U,OpenAIUser:R"
    set sc = ##class(Security.Roles).Modify("Nurse", .props)

    kill props
    set props("FullName")= "Nurse Joy"
    set props("Password")="pokemon"
    set props("Roles")="Nurse,%HS_DB_READYAI,FSB_Analyst"

    do ##class(Security.Users).Create("NJoy", .props)
    w "Nurse user NJoy created with partial access to patient records",!


    do ##class(Security.Roles).Create("TestRole", "Role with only class execution for testing", "", "",  )
    do ##class(Security.Roles).Get("TestRole", .props)
    set props("Resources")="%Native_ClassExecution:U"
    set sc = ##class(Security.Roles).Modify("TestRole", .props)
    do $SYSTEM.Status.DisplayError(sc)
    kill props

    set props("Password")="1234"
    
    do ##class(Security.Users).Create("Test", .props)
    w "Test user created with Class Execution Only",!

    #; do ..GrantExecute()
}

}
