Class ReadyAI.FSBSetup Extends %RegisteredObject
{

ClassMethod EnableApps() As %Status
{
    New $NAMESPACE
    Set $NAMESPACE = "%SYS"
    Kill ap
    Set ap("AutheEnabled") = 4
    Set ap("Enabled") = 1
    Do ##class(Security.Applications).Modify("/csp/fhirsql/api/ui", .ap)
    Kill ap
    Set ap("AutheEnabled") = 4
    Set ap("Enabled") = 1
    Do ##class(Security.Applications).Modify("/csp/fhirsql/api/repository", .ap)
    Write "Apps enabled",!
    Quit $$$OK
}

ClassMethod InstallFoundation() As %Status
{
    New $NAMESPACE
    Set $NAMESPACE = "HSLIB"
    Set sc = ##class(HS.Util.Installer.Foundation).Install("READYAI")
    If $$$ISERR(sc) { Write "Foundation ERR: ",$System.Status.GetErrorText(sc),! }
    If $$$ISOK(sc) { Write "Foundation OK",! }
    Quit sc
}

ClassMethod GrantFSBRoles() As %Status
{
    New $NAMESPACE
    Set $NAMESPACE = "%SYS"
    For user = "SuperUser","DScully","NJoy" {
        Set sc = ##class(Security.Users).Get(user, .up)
        If sc {
            Set up("Roles") = up("Roles") _ ",FSB_Admin,FSB_Analyst,FSB_Data_Steward"
            Do ##class(Security.Users).Modify(user, .up)
            Write user, " FSB roles granted",!
        }
    }
    Quit $$$OK
}

ClassMethod RunAll() As %Status
{
    Do ..EnableApps()
    Do ..InstallFoundation()
    Do ..GrantFSBRoles()
    Quit $$$OK
}

}
