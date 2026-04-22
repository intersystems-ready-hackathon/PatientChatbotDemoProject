# READYAI 

This repository contains the code for the READYAI hackathon demo project.

The `./iris/projects` directory is mounted at `/home/irisowner/dev`. The ObjectScript tools, toolsets, classes and MCP servers are defined in the ReadyAI package. This should be automatically installed upon building (via IPM), as will an MCP Web Application. 

## Building AI-HUB 


To build the IRIS for Health AI Hub container you will need:
- An IRIS for Health community AI Hub docker image - can be downloaded from [the Early Access Program Portal](https://evaluation.intersystems.com/Eval/early-access/AIHub)
    - Download the image, then run `docker load -i /path/to/irishealth-community-2026.2.0AI.156.0-docker.tar.gz`
    - If you are using a mac (arm64) version, or have downloaded a more recent image, update the image name in `Dockerfile` in ./ReadyAI-demo/iris
- A `langchain_intersystems-0.0.1-py3-none-any.whl` . Download from the same EAP portal. Save this wheel in ./langchain/dist 

- An OPENAI_API_KEY - this is used for the langchain side of the demo. It is currently set to use gpt-5-nano and the cost of running the demo is minimal. Add this to .env as as follows: 
        - Note, if you'd like to use a different AI API provider, the set-us is in `ReadyAI-demo\iris\projects\src\Setup\ConfigStore.cls`, which is automatically called by the iris.script file from the Dockerfile. 

```dotenv
OPENAI_API_KEY="sk-....."
```

After performing these three setup step, you can run: 

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

The full FHIR Server and FHIR SQL Build can be done with:

```bash
docker exec -it iris iris session iris
```
```objectscript
ZN "READYAI"
Do ##class(Setup.FSBRestRequest).RunAll()
zpm "load /home/irisowner/dev -v" 
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

There is a second container running  with Python. This is our "Client" container which is connecting to the mcp server as a remote client via HTTP. 

The demo app can be found at http://localhost:8501 . 

Try logging in and running the app with: 

- DScully / xfiles 
- NJoy / pokemon 

To show two different access layers. 

