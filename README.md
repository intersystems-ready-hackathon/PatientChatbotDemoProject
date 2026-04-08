# READYAI 

This repository contains the code for the READYAI hackathon demo project.

The `./iris/projects` directory is mounted at `/home/irisowner/dev`. The ObjectScript tools, toolsets, classes and MCP servers are defined in the ReadyAI package. This should be automatically installed upon building (via IPM), as will an MCP Web Application. 

## Building AI-HUB 


---
Update! I changed the build to use version 144 and the community edition - the main change this causes is WebGateway is no longer required and the http port is back to the standard 52773 rather than 80. 

To use a licensed version a couple of changes are required: 
    - Change the PORT parameter in FSBRestRequests to 80 
    - Change the port in the fhirrespository.body to 80
    
I also found that the REST requests didn't work during the container build for some reason. The StandardToolSet class depends on the tables being built and if this doesn't compile none of the IPM package will be installed, so you may need to manually run everything in the iris.script file.  

---


To build the IRIS for Health AI Hub container you will need:
    - A License Key 
    - An IRIS for Health AI Hub build kit  (downloaded internally [here](https://kits-web.iscinternal.com/kits/unreleased/IRISHealth/2026.2.0AI/)) Build 142 is confirmed to work. Use the dockerubuntu single-file kit appropriate for your operating system (arm for Mx Mac)

The container build step is available ReadyAI-demo/iris4h-aihub-build. Note you will need to change the version argument to match your kit, and if you are using an arm version, there might be other small mismatches that need changing in the dockerfile. 

```bash 
docker build -t i4h-aihub-142
```

I've separated out the i4h-aihub container build to the actual demo container build to make things neater. It does lead to double building so you can always combine these if its inconvenient.


## Setting up the demo

After you have built the base i4h-aihub container, you can build the demo container compose project. 

First create a .env file with 

```dotenv
OPENAI_API_KEY="sk-....."
```

Then

```bash
cd ReadyAI-demo
docker-compose up -d --build
```

### Build Details

The IRIS build is handled by the `iris/Dockerfile` (general bash commands, nothing too interesting) and the `iris/iris.script` script. This script does a few notable things:

- Installs the READYAI namespace
- Sets up FHIR Server and FHIRSQL builer with `do ##class(Setup.FSB).RunAll()`
- Installs IPM and loads all the `iris/projects/src` Objectscript Classes 
- Creates an MCP service Web application using the IPM Install (the following lines from `iris/projects/module.xml`):

```xml
      <WebApplication
        Url="/mcp/readyAI"
        Recurse="1"
        DispatchClass="ReadyAI.MCPService"
        AutheEnabled="#{$$$AutheCache}"
        Type="18" 
       />  
```

Type 18 defines its an MCP Server (and will appear in that applications portal) and $$$AutheCache is for Password Authentication

- Sets up the config store with

```objectscript
do ##class(Setup.ConfigStore).SetupWithAPIKey(__APIKEY__)
```
The \__API__ key is being replaced at build time in the dockerfile. 

- Sets up Roles for two users with 

```objectscript
do ##class(Setup.Roles).Run()
```

## FHIR Server Build 


FHIR SQL Builder is not documented for programatic use, but InterSystems Dach SEs worked out how to can create the Builder Spec from POST requests and created a helper class to do this, which is compiled with IPM during the build.

The full FHIR Server and FHIR SQL Build can be done with:

```bash
docker exec -it iris iris session iris
```
```objectscript
ZN "READYAI"
Do ##class(Setup.FSB).RunAll()
```

The SetupRequestBodies folder contains the FHIR-SQL Specification bodies, which are copied to /tmp/SetupRequestBodies as part of the customization build step.

## Start the MCP server

On start-up, you can check the health and tools available on the MCP server at 

- http://localhost:32783/mcp/readyAI/v1/health
- http://localhost:32783/mcp/readyAI/v1/services

To actually use the MCP server, the wgprotocol transport needs to be started using the `iris-mcp-server` binary: 

```bash
docker-compose exec -it iris bash 
iris-mcp-server -c config.toml run
```

## Test MCP server

You can run `langchain_discovery.py` locally (i.e. not in the container) to check the remote http server. This will print the available tools and invoke EchoUser to print the current user. 

```bash
pip install langchain langchain-mcp-adapters
python3 langchain_discovery.py
```

If you would like to try the MCP server with Stdio transport (i.e. connect to the MCP from the same system):
```bash
docker-compose exec -it iris bash 

cd mcp_test_stdio

pip install --break-system-packages fastmcp
python mcp_stdio_client_test.py
```

## Streamlit Side

There is a second container running (technically third because we have web-gateway as well) with Python. This is our "Client" container which is connecting to the mcp server as a remote client via HTTP. 

The demo app can be found at http://localhost:8501 . 

Try logging in and running the app with: 

- DScully / xfiles 
- NJoy / pokemon 

To show two different access layers. 


## Tool Audits

The MCP Server (or technically the toolset (ReadyAI.Toolset) it is serving) has an audit policy defined by: 

```xml
<Policies>
    <Audit Class="ReadyAI.Audit.AuditTable" />
</Policies>
```