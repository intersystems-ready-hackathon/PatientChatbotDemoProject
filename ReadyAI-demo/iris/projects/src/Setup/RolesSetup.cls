Class Setup.RolesSetup Extends %RegisteredObject
{

ClassMethod Run() As %Status
{
    New $NAMESPACE
    set $NAMESPACE = "%SYS"

    do ##class(Security.Roles).Delete("Doctor")
    do ##class(Security.Users).Delete("DScully")
    do ##class(Security.Roles).Delete("Nurse")
    do ##class(Security.Users).Delete("NJoy")
    
    do ##class(Security.Users).Delete("Test")

    do ##class(Security.Resources).Create("FullMedicalAccess")
    do ##class(Security.Resources).Create("OpenAIUser")


    do ##class(Security.Roles).Create("Doctor", "Roles group for full access to a patients medical records and history", "", "",  )

    do ##class(Security.Roles).Get("Doctor", .props)
    set props("Resources")="%Native_ClassExecution:U,OpenAIUser:R,FullMedicalAccess:R"
    set sc = ##class(Security.Roles).Modify("Doctor", .props)
    do $SYSTEM.Status.DisplayError(sc)
    kill props

    set props("FullName")= "Dana Scully"
    set props("Password")="xfiles"
    set props("Roles")="Doctor,%DB_READYAI,%SQL,%HS_DB_READYAI,FSB_Analyst"

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

    kill props 

    set props("Password")="1234"
    set props("Resources")="%Native_ClassExecution:U"
    do ##class(Security.Users).Create("Test", .props)
    w "Test user created with no roles",!
}

}
