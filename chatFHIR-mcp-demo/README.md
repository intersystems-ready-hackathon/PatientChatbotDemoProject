# ChatFHIR x AIHub

This repository contains the code for the ChatFHIR x AIHub hackathon project. The original ChatFHIR project was developed by InterSystems Dach. Much of the build process has been simplified or changed based on my preferences.

I've created tools using AI Core - mostly using embedded python, but also a singular tool using ObjectScript. This tools mirror the original MCP tools and fit with the scripted demo which is available on confluence. At the moment, the MCP server hasn't been created (as this part hasn't been included in the docker build)

The original MCP-servers are in mcp-servers folder. I've left them in the docker-compose so its easy to switch back and forth between the original MCP tools and the new AI tools.

I've included the Dockerfile I used to build the IRIS for Health AI Core image in iris4h-aicore-build. you will need to edit for your build kit and license key (its based on one I found in the AI hub gitlab repo...)

Theres then a separate 'customization' build step in the docker-compose and `iris/Dockerfile`.

## Set secrets

The docker-compose references:
- iris.secret - a file which just contains a password for web gateway. I use the default SYS (this is hard coded elsewhere in the build, so I reommend just using it too)
- VLLM_API_KEY - the OpenWebUI is set up to use Plaza via a base URL and VLLM_API_KEY set in .env. You can add plaza key to .env, use a different openai key or just remove this and set up another provider in the WebUI once its running. 

## Setting up the demo

Start the containers:

```bash
docker-compose up -d --build
```

## Create FHIR SQL projection

FHIR SQL Builder is not documented for programatic use, but the Germans worked out how to can create the Builder Spec from POST requests and created a helper class to do this, which is compiled upon the customization build step, unfortunately the requests don't work as part of the build, (maybe because of a web-gateway dependancy?) so I've resorted to using this class manually once the containers are running:

```bash
docker exec -it iris iris session iris
```

```objectscript
Do ##class(Demo.CHATFHIR.Setup.RestRequest).LocalPOSTRequest("credentials", "/tmp/SetupRequestBodies/credentials.body")
Do ##class(Demo.CHATFHIR.Setup.RestRequest).LocalPOSTRequest("fhirrepository", "/tmp//SetupRequestBodies/fhirrepository.body")
Do ##class(Demo.CHATFHIR.Setup.RestRequest).LocalPOSTRequest("analysis", "/tmp/SetupRequestBodies/analysis.body")
Do ##class(Demo.CHATFHIR.Setup.RestRequest).WaitForAnalysisComplete(1)
Do ##class(Demo.CHATFHIR.Setup.RestRequest).LocalPOSTRequest("transformspec", "/tmp//SetupRequestBodies/transformspec.body")
Do ##class(Demo.CHATFHIR.Setup.RestRequest).LocalPOSTRequest("projection", "/tmp/SetupRequestBodies/projection.body")
```

The SetupRequestBodies folder contains the request bodies, which are copied to /tmp/SetupRequestBodies as part of the customization build step.

## New tools

The newly build MCP tools are available in `iris/projects/mcp_tools`, mostly build with Embedded Python, but also one build with objectscript. 

## Extra preparation

- Building containers
- Launch container
- In WebUI ([http://localhost:3000/](http://localhost:3000/))
    - Add system prompt (to be found in the repo under mcp-servers\system_prompt.txt
        - User → Settings → General → System Prompt
        - Save
    - Configuring the link to OpenAI API models
        - User → settings → administration → connections
            - Enable OpenAI API
            - Click on the plus next to "Manage OpenAI API connections"
            - Fill in the following fields:
                - URL: [https://api.openai.com/v1](https://api.openai.com/v1)
            - Save
            - Save again in the parent window
    - Configuring the Link to MCP Server
        - User → Settings → External Tools
        - Click on the plus next to "Manage Tool Server"
        - Fill in the following fields:
            - URL: [http://localhost:8002](http://localhost:8002/)
        - Click on the round double arrow to test the connection
        - Save
        - Save again in the parent window
    - Disable follow-up question generation
        - User → settings → interface
        - In the "Conversation" section
            - Disable the following entries:
                - "Automatically generate chat titles"
                - "Auto-generation for follow-up questions"
                - "Automatic generation of chat tags"
            - Save
    - Enable better support for tool chaining
        - User → Settings → General
        - Expand the Advanced Parameters section
            - Change the function call parameter to native.
            - Save
    - Open a new chat window
        - Select gpt-5.2 as model
        - Under the model name, select Set as Default


