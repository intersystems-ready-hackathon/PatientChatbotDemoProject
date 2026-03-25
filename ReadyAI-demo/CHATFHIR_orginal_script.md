- Created by [Sylwester Boldt](https://usconfluence.iscinternal.com/display/~sboldt), last updated by [Henning Sievert](https://usconfluence.iscinternal.com/display/~hsievert) on [Feb 24, 2026](https://usconfluence.iscinternal.com/pages/diffpagesbyversion.action?pageId=1083872180&selectedPageVersions=61&selectedPageVersions=62 "Show changes")  8 minute read

This demo was presented by [Sylwester Boldt](https://usconfluence.iscinternal.com/display/~sboldt) and [Henning Sievert](https://usconfluence.iscinternal.com/display/~hsievert) at the DACH Symposium 2025 in German. Hence, most of the information below is in German. With minor efforts, it can easily be converted to an English demo. I you wish to do so, feel free to reach out if you need help.

- [Title](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Titel)
- [Abstract](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Abstract)
- [Presentation](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Presentation)
- [Github Repository](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-GithubRepository)
- [Useful Background Information](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-UsefulBackgroundInformation)
- [Demo](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Demo)
    - [Necessary preparation](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-NotwendigeVorbereitung)
    - [Important URLs](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-WichtigeURLs)
    - [Command to create a container snapshot](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-KommandozumErzeugeneinesContainerSnapshots)
    - [Script](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Skript)
        - [Scenario 1 - LLM with connection to iris-mcp (still without transformation for drugs)](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Szenario1-LLMmitVerbindungzuiris-mcp\(nochohneTransformationf%C3%BCrMedikamente\))
        - [Scenario 2 - Complement medication mapping in SQL Builder and MCP Server](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Szenario2-Erg%C3%A4nzendesMappingsvonMedikamentenimSQLBuilderundMCPServer)
        - [Scenario 3 - Deleting the SQL Builder Configuration and Basic Building from Scratch](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Szenario3-L%C3%B6schenderKonfigurationdesSQLBuildersundgrundlegenderAufbauvonGrundauf)
        - [Scenario 4 - (Optional if there is still time) - Various queries that demonstrate different capabilities](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1083872180/READYAI+-+GenAI+MCP+FHIR#READYAIGenAI,MCP,FHIR-Szenario4-\(Optional,wennnochZeitist\)-VerschiedeneAbfragen,dieverschiedeneF%C3%A4higkeitendemonstieren)

# Title

READYAI: GenAI meets FHIR, agent-based data access with MCP

# Abstract

Using FHIR data in a structured way is a thing of the past - today we are talking to you. This session introduces the MCP server as a bridge between AI and FHIR. An MCP server opens up access to external sources for AI models via standardized interfaces. With the InterSystems FHIR SQL Builder, existing FHIR repositories are made available as tools. Participants will learn how to create an agent that retrieves FHIR data via MCP, makes it usable in a structured and understandable way - and how to build your own agents with little effort. A hands-on introduction to agent-based GenAI applications in healthcare.


[https://github.com/intersystems-dach/chat-fhir](https://github.com/intersystems-dach/chat-fhir)

# Useful Background Information

- MCP: [https://modelcontextprotocol.io/docs/getting-started/intro](https://modelcontextprotocol.io/docs/getting-started/intro)
- FHIR Basics: [https://training.iscfhir.com/](https://training.iscfhir.com/ "https://training.iscfhir.com/")
- FHIR SQL Builder and Data Set with 115 patients: [FHIR SQL Builder](https://usconfluence.iscinternal.com/spaces/ISCDACH/pages/1085834974/FHIR+SQL+Builder)

# Demo



## Important URLs

- IRIS Management Portal: [http://localhost:8080/csp/sys/Utilhome.csp](http://localhost:8080/csp/sys/Utilhome.csp)
- Open WebUI: [http://localhost:3000/](http://localhost:3000/)

## Command to create a container snapshot

`docker commit iris4h iris4h:scratch`

## Script

**(Introduction) Sylwester: Sylwester (is an endocrinologist, technically affine, no IT knowledge), Henning (Innovative IT employee)**

**Sylwester gets a taste of the IT department, which always provides him with innovative tools that make his work easier and are based on ISC products. Now he inquires about the latest status, he had recently picked up the keyword "FHIR SQL Builder and AI".**

### Scenario 1 - LLM with connection to iris-mcp (still without transformation for drugs)

- **Sylwester: I've heard you're experimenting with a FHIR SQL Builder and AI. What are you doing there?**
- Open SQL Portal: [http://localhost:8080/csp/sys/exp/%25CSP.UI.Portal.SQL.Home.zen?$NAMESPACE=READYAI](http://localhost:8080/csp/sys/exp/%25CSP.UI.Portal.SQL.Home.zen?$NAMESPACE=READYAI)
- Schema: Select "READYAI"
- Expand tables
- Briefly explain that we currently see 3 relevant tables here with patient master data, observations and conditions.
- Drag the READYAI.Patient table to the "Run Query" tab
- Click Run
- Show that there are 114 patients in the database.
- **Sylwester: Throwing in SQL, if there is a direct FHIR interface?**
- Open Open WebUI: [http://localhost:3000/](http://localhost:3000/)
- "New chat"
- Question: "How many patients are in the database?"
- Model cannot answer it because it does not yet have a tool available to access the database.
- Integrations → tools
    - Enable IRIS MCP
- Question: "How many patients are in the database?"
- Model answers correctly 114.
- Call "tool_get_patient_count_post" and show the JSON response.
- **Sylwester: Hey, that's cool. Can I now use it to find out, for example, which of my patients have diabetes?**
- Question: "Which patients have diabetes?"
- Model responds with list of 5 patients
- Expand and explain the tool calls. Show how the relevant Snomed Codes and Patient IDs are passed to the next tool. (Snomed code for diabetes is on line 201 of the response)
- **At this point, it should also be mentioned that diabetes not only has a snomed code, but there are many types of it and that in real life you would connect an MCP server for a medical knowledge base**.
- There may be more patients in the response. Then show that the other patients have diagnoses that have something with diabetes in their name (e.g. prediabetes) and explain that the LLM has now filtered out only those patients who have a real diabetes diagnosis.
- **Sylwester: I'm impressed. And is it really live?**
- Switch to VS Code
- Open file iris\projects\READYAI\SampleMessages\StefanKoch.rest
- Click on the "Send Request" link
- Open Production in the Management Portal: [http://localhost:8080/csp/healthshare/readyai/EnsPortal.ProductionConfig.zen?PRODUCTION=Demo.READYAI.Interop.Production&$NAMESPACE=READYAI](http://localhost:8080/csp/healthshare/readyai/EnsPortal.ProductionConfig.zen?PRODUCTION=Demo.READYAI.Interop.Production&$NAMESPACE=READYAI)
- Open the "Messages" tab on the right side of the UI
- Click on the top message
- Briefly explain the tracing and click the "Content" tab for the message to the trace operation
- Explain that this is the content of the message we sent from VS Code via REST API
- Switch back to the Open WebUI
- Question: "How many patients are in the database?"
- Model now answers 115, so one more.
- Question: "Which patients have diabetes?"
- Stefan Koch is now also included in the list.
- **Sylwester: As the treating physician, it is important to me to pay special attention to patients with risk factors. One of these factors is overweight, can I have this displayed here?**
- Question: "Are you overweight?"
- Explain that this is where the strengths of an LLM and the FHIR connection come together. The model has the definition of overweight based on BMI and therefore asks for and compares the BMIs of the patients.

### Scenario 2 - Complement medication mapping in SQL Builder and MCP Server

- **Sylwester: With my patients, it is important to me that they are treated accordingly with medication. Can I also see if they have already prescribed appropriate medication?**
- Question: "Do you receive diabetes medication?"
- Model replies that it can't answer the question because it doesn't have access to medication.
- Click on the tool and expand iris-mcp
- Show that there is no tool for medications.
- Open SQL Portal: [http://localhost:8080/csp/sys/exp/%25CSP.UI.Portal.SQL.Home.zen?$NAMESPACE=READYAI](http://localhost:8080/csp/sys/exp/%25CSP.UI.Portal.SQL.Home.zen?$NAMESPACE=READYAI)

- Schema: Select "READYAI"
- Expand tables
- Show that there are only tables for condition, observation and patient, but none for medication
- Click on "Home" in the menu bar at the top
- Health → READYAI → FHIR Server Management → Go 
- Links Select FHIR SQL Builder (2nd from bottom)
- Under "Transformation Specifications" click the edit icon of the "READYAITransform" transformation
- Change "Items per page" to 100 at the bottom right
- Scroll through the list and show that there are only transformations for Patient, Condition and Observation
- Map the following fields under "MedicationRequest":
    - subject→reference
        - Click on "Show Histogram" and show that you will then get a preview of the content. In this case, the reference to the patient key
        - Column name: Patient
        - Index: on
        - Click on "Add to projection"
    - medicationCodeableConcept→coding→code
        - Column name: Code
        - Index: on
        - Click on "Add to projection"
    - medicationCodeableConcept→coding→display
        - Column name: Description
        - Index: on
        - Click on "Add to projection"
- Scroll through the list again and show the three new mappings at the bottom of the list
- Scroll to the top and click "Done" in the top right corner
- Click the round arrow on the right of "Projections" to update the projection
- Click on "Home" at the top
- System Explorer → SQL → Go
- Change namespace to READYAI
- Schema: Select "READYAI"
- Expand tables
- Show that there is now a new MedicationRequest table
- Drag and drop the table into the "Run Query" tab
- Click "Run"
- Show that the 3 mapped columns have been created accordingly plus 3 more standard columns (ID, Key, RowNum)
- **Sylwester: Great, it was really easy with the table. But if I understand correctly, we always lack the tool for the LLM, right?**
- Switch to VS Code
- Open mcp-servers\medications-mcp\server.py file
- Explain how it is structured and show that the MCP tool for the medications is only a short method with a simple SQL statement.
- Open Swagger for MCP Server: [http://localhost:8003/docs](http://localhost:8003/docs)
- Expand POST
- Click on "Try it out"
- Replace "string" with "patient/9" in the request body
- Click "Execute"
- Scroll down to Response Body and Show Answer
- **Sylwester: Nice, so we've now built the MCP server. How can the LLM access it now?**
- Switch back to Open WebUI
- User → Settings → External Tools
- Click Plus
- Enter the following values:
    - URL: [http://localhost:8003](http://localhost:8003/) 
    - **It should be mentioned here that access control to the data can also be configured here (also via SSO to the backend), which we did not do for the demo.**
- Click on the round double arrow to test the connection
- Save
- Save again in the parent window
- Back to chat
- Click on the integrations
- Tell me that you can now see the new MCP server for medications there
- Activate it
- Click on the tool and expand medications-mcp
- To show that a new tool for medications is now available.
- **Sylwester: That happened quickly. Was that really all there is to the LLM now being able to answer my question?**
- Question: "Do you receive diabetes medication?"
- Modell now answers the question.
- Question: "What medication does Terrence take?"
- Model answers.

**(Moderation transition) Sylwester: We have now seen what we can achieve with the combination of LLM and MCP. Now we want to show you, who are technically interested IRIS4H users, how we can create configuration in the FHIR SQL Builder from scratch.**

### Scenario 3 - Deleting the SQL Builder Configuration and Basic Building from Scratch

- **Sylwester: Henning, you showed us how to expand an existing transformation. If I wanted to set it all up from scratch, surely it would be a lot more complex?**
- Open Management Portal:
- IRIS Management Portal: [http://localhost:8080/csp/sys/Utilhome.csp](http://localhost:8080/csp/sys/Utilhome.csp)
- Health → READYAI → FHIR Server Management → Go
- Links Select FHIR SQL Builder (2nd from bottom)
- Delete Projection
- Delete Transform
- Delete Analysis
- Select Repository Configuration on the left (2nd from above)
    - Delete repository
    - Delete credentials for READYAIUser
- Click on "Home" in the top right corner
- System Explorer → SQL → Go
- Change namespace to READYAI
- Expand schema dropdown
- Tell that there is no READYAI schema and therefore no tables
- Expand tables
- No more READYAI tables
- **Sylwester: Aha, but how does the chatbot react if I were to ask it?**
- Switch to Open WebUI
- New chat
- Activate tools
- Question: "How many patients are in the database?"
- The model can't answer the question because it can't find the table.
- Expand the return of the tool and show an error message.
- **Sylwester: Crass. Then I'm curious how you can rebuild it now.**
- Go back to the Management Portal
- Click on "Home" in the top center
- Health → READYAI → FHIR Server Management → Go
- Links Select FHIR SQL Builder (2nd from bottom)
- Create Analysis:
    - FHIR Repository:  
        - Click "New"
        - Name: READYAIRepo
        - Host: localhost
        - Port: 52773
        - Credentials:
            - Click "New"
            - Name: READYAIUser
            - Username: superuser
            - Password: SYS123
            - Click "Save"
        - FHIR Repository URL: /readyai/r4 
        - Click "Save"
    - Selectivity Percentage: 100
    - Click "Launch Analysis Task"
- Wait for it to reach 100% Percent Complete
- Create a transformation:
    - Name: READYAITransform
    - Analysis: READYAIRepo
    - Click "Create Transformation Specification"
    - **Sylwester: But that would be quite time-consuming to configure all the transformations again...**
    - Tell us that now, as already shown in the medication example, you can configure the transformation, but we won't do that due to time constraints, but import a finished one.
    - Click "Done"
- Delete Transformation.
- Import Transformation
    - Select the chat-fhir\iris\projects\READYAI\SetupRequestBodies\transformspec_with_med.body file.
    - Analysis: READYAIRepo
    - Click "Import"
    - Click Edit icon and show that the transform is now import.
    - Click "Done"
- Create projection:
    - FHIR Repository: READYAIRepo
    - Transformation Specification: READYAITRansform
    - Package Name: READYAI
    - Click "Launch Projection"
- Click on "Home" in the top right corner
- System Explorer → SQL → Go
- Change namespace to READYAI
- Schema: Select "READYAI"
- Expand tables
- Drag patient table into "Run query" tab
- Click "Run"
- Patient data is shown
- Switch to Open WebUI
- Question: "How many patients are in the database?"
- The model answers correctly.

### Scenario 4 - (Optional if there is still time) - Various queries that demonstrate different capabilities

- **Sylwester: Cool. I had Wilbo Waters there the other day and needed a clinical summary for him. Can the agent create something like that?**
- Open a new chat so that old context is deleted.
- Enable MCP Tools
- Question: "Get me a clinical summary for Wilbo Waters."
- Modell says that the patient does not exist.
- **Sylwester: Hmm, I don't remember his name exactly. Perhaps his name was something else.**
- Question: "Is someone with a similar name?"
- Model shows list.
- **Sylwester: Oh, exactly. His name was Wilbur, not Wilbo.**
- Question: "I mean the <second>" (Adjust to position in the list)
- Model creates summary.
- **Sylwester: Do you have another interesting example?**
- Open a new chat so that old context is deleted.
- Question: "What are the diagnoses of broken bones?"
- Question: "Who has the broken ribs?"
- Question: "What clinical data are available for Thanh?"
- Question: "How has your weight developed over time? Give me a table with time and reading."
- Open a new chat so that old context is deleted.
- Question: "Who has acute Corona?"

--- END ---