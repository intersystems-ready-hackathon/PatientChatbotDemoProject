Class Demo.READYAI.Setup.RestRequest Extends %RegisteredObject
{

ClassMethod LocalPOSTRequest(resource As %String, filePath As %String) As %Status
{
    // Create an HTTP request object
    Set httpRequest = ##class(%Net.HttpRequest).%New()

    // Set the target URL
    Set httpRequest.Server = "localhost"
    Set httpRequest.Https = 0 
    Set httpRequest.Port = 80

    // Set the request headers (optional)
    Do httpRequest.SetHeader("Content-Type", "application/json")
    Do httpRequest.SetHeader("Accept", "application/json")
    Do httpRequest.SetHeader("Authorization", "Basic U3VwZXJVc2VyOlNZUw==")

    Set fileStream = ##class(%Stream.FileCharacter).%New()
    Do fileStream.LinkToFile(filePath)
    Do httpRequest.EntityBody.CopyFrom(fileStream)

    Set endpoint = "/csp/fhirsql/api/ui/v2/"_resource

    // Send the request
    Set status = httpRequest.Post(endpoint)

    // Check for errors
    If $$$ISERR(status) {
        Write "Error sending request: ", $SYSTEM.Status.GetErrorText(status), !
        Quit status
    }

    // Read the response
    Write "Response Code: ", httpRequest.HttpResponse.StatusCode, !
    Write "Response Data: ", httpRequest.HttpResponse.Data.Read(), !

    Quit $$$OK
}

ClassMethod WaitForAnalysisComplete(id As %String)
{
    for {
        quit:..GetAnalysisStatus(id)="completed"
        write "Waiting...", !
        hang 2
    }

    write "Finished waiting", !
}

ClassMethod GetAnalysisStatus(id As %String) As %String
{
    // Create an HTTP request object
    Set httpRequest = ##class(%Net.HttpRequest).%New()

    // Set the target URL
    Set httpRequest.Server = "localhost"
    Set httpRequest.Https = 0 
    Set httpRequest.Port = 80

    // Set the request headers (optional)
    Do httpRequest.SetHeader("Content-Type", "application/json")
    Do httpRequest.SetHeader("Accept", "application/json")
    Do httpRequest.SetHeader("Authorization", "Basic U3VwZXJVc2VyOlNZUw==")

    Set endpoint = "/csp/fhirsql/api/ui/v2/analysis?ID="_id

    // Send the request
    Set status = httpRequest.Get(endpoint)

    // Check for errors
    If $$$ISERR(status) {
        Write "Error sending request: ", $SYSTEM.Status.GetErrorText(status), !
        Quit status
    }

    set responseText = httpRequest.HttpResponse.Data.Read()

    // Read the response
    Write "Response Code: ", httpRequest.HttpResponse.StatusCode, !
    Write "Response Data: ", responseText, !

    set responseJson = {}.%FromJSON(responseText)
    set completionStatus = responseJson.status
    write "Completion Status: ", completionStatus, !

    Quit completionStatus
}

}
