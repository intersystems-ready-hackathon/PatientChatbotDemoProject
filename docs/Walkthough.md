# Build walkthrough 

This project is built to demonstrate components from the soon-to-be released AI Hub. While the premise and implementation is basic, the demo covers the build of agent tools, the exposure of the tools via a remote MCP server and the creation of policies to govern these tools. 

Pre-requisities: 
    - Understanding of AI Tools
    - Understanding of MCP
    - A version of AI Hub 


This quickstart walkthrough aims to document the full build process for a demo application using the AI Hub. For full details, see the documentation. 

## Step 1: Setup 

This project uses FHIR data via the FHIR SQL builder to allow querying against SQL tables rather than directly through FHIR data. The set-up behind this has been automated during the docker build process as it is not the focus on the demo. To view how this works, see the `Setup.FSBSetup` and `Setup.FSBRestRequest` classes. 

The demo also uses two users with different roles, again, these are set up in the build process using the class `Setup.Roles`. 

Finally, an LLM configuration is created in the new Configuration Store, the set-up is a GPT model created with an OpenAI API Key. We'll discuss this more in the server side walkthrough later. 


## Step 2: Defining Tools


**Disclaimer: thisn demo project is a simplistic representation of a complex system.**

We want to create tools to perform custom queries on the database using SQL. We are going to define 6 tools, with two different access levels. 

### General Access

These are tools that can be used by any user with a valid login (tools may be important fo medical emergency or general practice, without giving full medical access). 

1. **SearchForPatientBySurname** - This is used as a basic patient identifier. The FHIR data refers to the patient by ID (e.g. SubjectReference = Patient/25), so in order to do querying on the rest of the patient data, the ID is needed. Hence we search for the patient by surname first. 

2. **QueryMedications** - Query the medication table for a patient to identify the current medications the patient can be on.

3. **QueryAllergies** - Check the patient allergies. 

### Restricted Access

These are tools which require a specialist role (Doctor) to see an in-depth medical record.

4. ListMedicalTables - list all available medical tables in the FHIR-SQL dataset

5. QueryTable - Query any of the medical tables listed above (using a patient ID) 

### Utility

6. EchoUser - Echo's the user's username and role to the Agent, so they can be self aware. 

 
## Step 3: Building tools

The `%AI` ObjectScript package has two methods of defining tools: `%AI.Tool` and `%AI.ToolSet`. 

### %AI.Tool 

Tools are simple - they are ObjectScript classes where each method of the class is serialised into a AI callable tool.

Below, we can see the ListTables tool. This is a normal objectscript method, which in this case doesn't accept any parameters (but if it did they would be defined as normal), and returns a dynamic object (JSON) with the result.  

```objectscript
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
}
```

Note, if you want to use a Dynamic Array as an input, you may need to define the type of the values in the array by using: `pArray as %DynamicArray(ELEMENTTYPE="%Integer")` - this is required by certain LLMs (OpenAI) and means that when a tool is discovered it serialises to:

```json
"pArray": {
    "type": "array",
    "items": {
        "type": "integer"
    }
}
 
```

### %AI.ToolSet

A toolset is a collection of tools, and policies. Policies are explained in more detail in the section below, but can be either Authorization policies (deciding whether a tool can be used), or Audit policies (logging a tools use and response). 

Toolsets are defined by XML blocks in the objectscript class. 

We are defining two toolsets for the two different access levels defined in Step 2.

#### Toolset 1: Full Access

Lets start with the full access toolset, as this is the simpler of the two as the tools have been defined elsewhere.

```objectscript
Class ReadyAI.FullAccessToolSet Extends %AI.ToolSet [ DependsOn = (ReadyAI.Tools.StandardTools, ReadyAI.Tools.FHIRSQLQueryTools) ]
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.FullAccessToolSet">
            <Description>ToolSet for READYAI demo</Description>
            <Policies>
                <Audit Class="ReadyAI.Policies.AuditTable" />
                <Authorization Class="ReadyAI.Policies.RoleAuth" />
            </Policies>
            <Include Class="ReadyAI.Tools.FHIRSQLQueryTools"/>
</ToolSet>
}

}
```

The `XData Definition`  has the full defintion of the toolset. The toolset name and description are simply defined. 

The `<Policies>` tag holds the two types of policies = `Audit` and `Authorizaion`, both of these reference classes which we will go through below. Note, here we have 

Finally The `<Include>` tag adds our existing `%AI.Tool` class. 


#### Toolset 2: General Access 

For the general access toolset, we are going to define the tools directly in the `%AI.ToolSet` extended class. 

We can start this toolset in the same way:

```objectscript
Class ReadyAI.StandardToolSet Extends %AI.ToolSet
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="ReadyAI.StandardToolSet">
        <Description>Standard ToolSet for READYAI demo</Description>
        <Policies>
            <Audit Class="ReadyAI.Policies.AuditTable" />
        </Policies>
```

To define a tool in the toolset class, we can use the `<Tool>` tag

```xml
        <Tool Name="EchoUser" Method="EchoUser" >
            <Description>Echo the current user's username and roles back to them.</Description>
        </Tool>
```

The method is refers to a class method defined in the same class: 

```objectscript
ClassMethod EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}
```

We can also define SQL queries directly in the toolset with a `<Query>` tag: 

```xml
        <Query
        Name="QueryAllergies"
            Type="SQL"
            Description="Find allergies for a patient based on their patient ID"
            Arguments="patientId As %Integer"
            MaxRows="50">
        SELECT TOP 50 AllergyDescription, Category, Code, Criticality, Status, VerificationStatus
        FROM AFHIRData.AllergyIntolerance WHERE Patient=CONCAT('Patient/', :patientId)
        </Query>
```

Here we pass in the arguments as an objectscript input (`patientId As %Integer`) and use it within the query with `:patientId`. 

## Step 4: Building Policies

In the toolsets above, we have used two policies: 

- `ReadyAI.Policies.AuditTable`
- `ReadyAI.Policies.RoleAuth`

These policies are based on ObjectScript methods, so can be as complicated in logic as you can write code for. 

### Audit Policy 

The audit policy is activated when a tool is called through a method called `%LogExecution`: 

```objectscript
Class ReadyAI.Policies.AuditTable Extends %AI.Policy.Audit
{

Method %LogExecution(call As %DynamicObject, metadata As %DynamicObject, result As %DynamicObject, duration As %Integer, status As %Status) As %Status
{
    // Create a new log entry
    Set logEntry = ##class(ReadyAI.Policies.ToolLog).%New()
    Set logEntry.ToolName = call.%Get("name", "unknown")
    Set logEntry.ToolCall = call
    Set logEntry.Metadata = metadata
    Set logEntry.Result = result
    Set logEntry.Timestamp = $ZDATETIME($HOROLOG)
    Set logEntry.Duration = duration
    Set logEntry.Status = status
    set logEntry.Username = $USERNAME

    // Save the log entry to the database
    set st =  logEntry.%Save()
    if 'st {
      return $$$ERROR($$$AICoreToolAccessDenied, "Failed to save tool log: "_$SYSTEM.Status.GetErrorText(st))
    }

    Return $$$OK
}

}
```

This simple method logs the tool call, results and related metadata via a peristent class (ReadyAI.Policies.ToolLog). `%LogExecution` is activated upon tool execution completion. 

### Authorization policy

Unlike the Audit policy, the Authorization policies are activated in advance of using either looking up the tools ("can this tool be seen at?") using the `%CanList` method or before using the tool call is executed("can this tool call be executed?") using the `%CanExecute` method.

In this case, we want to implement a very simple roles based access policy. We can do this with the following:

```
Class ReadyAI.Policies.RoleAuth Extends %AI.Policy.Authorization
{

Method %CanList(tool As %String) As %Boolean
{
        set roles = $ROLES
        if $FIND(roles, "Doctor") {
            return 1
        }elseif $FIND(roles, "%All") {
            return 1
        }
        else {
            return 0
        }
}

Method %CanExecute(tool As %String) As %Status
{
        set roles = $ROLES
        if $FIND(roles, "Doctor") {
            return $$$OK
        }
        elseif $FIND(roles, "%All") {
                return $$$OK
            }
        else {
            return $$$ERROR($$$AICoreToolAccessDenied, "Access denied: User does not have the 'Doctor' role required to execute this tool.")
        }
}

}

```

The `%CanList` method returns a boolean (1 if it can be listed, 0 if it cannot). The `%CanExecute` method returns a status, being `$$$OK` if it can be executed, or `$$$ERROR` with a defined error - this allows the tool caller to see why the call was rejected - e.g. *user did not have the correct role*. 

The tool call is inputted into the method, so the authorization can be based on the parameter contents rather than user details. In the existing examples, there is an example of a `PathSanitizer` auth policy which controls whether a FilePath is a allowed in a file system tool. 

## Step 5: Deploying MCP Web Applciation

The MCP Service is a CSP application with a simple dispatch class extending the `%AI.MCPService` class. This class simply needs to have a comma separated list of tool or toolset classes in the SPECIFICATION parameter. 

```objectscript
Class ReadyAI.MCPService Extends %AI.MCP.Service
{

Parameter SPECIFICATION = "ReadyAI.RestrictedAccessToolSet,ReadyAI.StandardToolSet";

}
```

We can create a web-application from the management portal. There is a special menu under `System Administration --> Security --> Applications --> MCP Server` menu. To create a class, you simply need to set an endpoint name (e.g. `/mcp/readyai`) and the dispatch class (`ReadyAI.MCPService`).

This can also be done from ObjectScript: 

```objectscript
zn "%SYS"
kill props
set props("DispatchClass") = "ReadyAI.MCPService" 
set props("AutheEnabled") = 32 // Password authentication
set props("Type") = 18 // Type 18 corresponds to MCP service, ensuring it lives in the MCP Service menu. 
set props("namespace") = "READYAI"
set sc =  ##class(Security.Applications).Create("/mcp/readyai", .props)
```

We have already set this up from the `module.xml` file which installs the demo via IPM. 

```xml
      <WebApplication
        Url="/mcp/readyAI"
        Recurse="1"
        DispatchClass="ReadyAI.MCPService"
        AutheEnabled="#{$$$AutheCache}"
        Type="18" 
       /> 
```

At this point, the tools should be visible at the `/<endpoint>/v1/services` endpoint:

http://localhost:32783/mcp/readyai/v1/services

As we have password login, this will require a login. 

## Step 6: Start MCP Transport 

The MCP service has two parts, the web application, and the transport method. The transport uses the web-gateway protocol and can be used for remote HTTP/HTTPS service i.e. connecting to the IRIS server from a client, or using stdio for local usage i.e. connecting from a different applciation on the same server. 

We can set the configuration in a `config.toml` file: 

```toml
[[iris]]
name = "local"
server = { host = "localhost", port = 1972, username = "SuperUser", password = "SYS" }
endpoints = [
    {path = "/mcp/readyai" }
]

[pool]
min_connections = 1
max_connections = 3
connection_timeout = 30

[discovery]
auto_discover = true
interval_seconds = 60
cache_ttl = 300

[mcp]
transport = "http"
port=8888
host="0.0.0.0"

[logging]
level="debug"
```

The endpoints are added to this. The server login requires CSPSystem privaleges to use the wgprotocol to connect to iris, whilst login for individual endpoints can be added to this configuration or authentication can happen from an HTTP client via `Basic` (Username:Password in Base64) or `Bearer` token for OAuth. There is more information on this config in the documentation. 

To start the configuration, use the `iris-mcp-server` binary with: 

```bash
iris-mcp-server -c config.toml run
```

After this, you can connect to the MCP server from an MCP client. 

## Step 7: Connect From MCP Client 

In the demo, we have a basic Python application created with Streamlit. We connect to the MCP server via langchain's `MultiServerMCPClient`:

```python
from langchain.mcp_adapters import MultiServerMCPClient
import base64
import asyncio

async def main():
    auth_header = base64.b64encode(b"SuperUser:SYS").decode("utf-8")

    client = MultiServerMCPClient(
                {
                    "readyai": {
                        "transport": "http",
                        "url": "/mcp/readyai",
                        "headers": {"Authorization": f"Basic {auth_header}"},
                    }
                }
            )

    tools = await client.get_tools()
    for tool in tools: 
        print("- ", tool, "\n")

asyncio.run(main)
```

## Step 8: Build an AI Agent

We can create 