# READYAI 

This repository contains the code for the READYAI x AIHub hackathon project. The original CHATFHIR project was developed by InterSystems Dach. Much of the build process has been simplified or changed based on my preferences.

The `./iris/projects` directory is mounted at `/home/irisowner/dev`. The ObjectScript tools, toolsets, classes and MCP servers are defined in the ReadyAI package. This should be automatically installed upon building (via IPM), as will an MCP Web Application. 

## Setting up the demo

Start the containers:

```bash
cd ReadyAI-demo
docker-compose up -d --build
```

## Create FHIR SQL projection

FHIR SQL Builder is not documented for programatic use, but the Germans worked out how to can create the Builder Spec from POST requests and created a helper class to do this, which is compiled upon the customization build step, unfortunately the requests don't work as part of the build, (maybe because of a web-gateway dependancy?) so I've resorted to using this class manually once the containers are running:

```bash
docker exec -it iris iris session iris
```

```objectscript
ZN "READYAI"
Do ##class(Demo.READYAI.Setup.RestRequest).LocalPOSTRequest("credentials", "/home/irisowner/dev/FHIR/SetupRequestBodies/credentials.body")
Do ##class(Demo.READYAI.Setup.RestRequest).LocalPOSTRequest("fhirrepository", "/home/irisowner/dev/FHIR//SetupRequestBodies/fhirrepository.body")
Do ##class(Demo.READYAI.Setup.RestRequest).LocalPOSTRequest("analysis", "/home/irisowner/dev/FHIR/SetupRequestBodies/analysis.body")
Do ##class(Demo.READYAI.Setup.RestRequest).WaitForAnalysisComplete(1)
Do ##class(Demo.READYAI.Setup.RestRequest).LocalPOSTRequest("transformspec", "/home/irisowner/dev/FHIR/SetupRequestBodies/transformspec.body")
Do ##class(Demo.READYAI.Setup.RestRequest).LocalPOSTRequest("projection", "/home/irisowner/dev/FHIR/SetupRequestBodies/projection.body")
```

The SetupRequestBodies folder contains the request bodies, which are copied to /tmp/SetupRequestBodies as part of the customization build step.

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

To test with Stdio transport, you can use: 

```bash
docker-compose exec -it iris bash 

cd mcp_test_stdio

pip install --break-system-packages fastmcp
```

## Vector store from DocumentReference Resources

The document reference resources (Synthetic clinical notes made for the original FHIR AI Hackathon Kit) have been added to the FHIR SQL builder transform. This can be loaded into a vector store with: 

```objectscript
zn "READYAI"
do ##class(RAG.DocRefVectorSetup).EmbedText()
```

The vector store will have the name `AFHIRData.DocRefVectorStore`.