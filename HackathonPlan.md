# READY Hackathon: AI Hub Integration Demo Plan

## Objectives

This project aims to build a comprehensive demonstration highlighting the core capabilities of the internal AI Hub. The codebase is deliberately designed to be accessible and easy to follow, while explicitly showcasing the key integration patterns available through the platform.

Specifically, we intend to demonstrate:
* The creation and deployment of an IRIS Model Context Protocol (MCP) server utilizing custom Python and ObjectScript methods.
* The implementation of custom workflows using the Langchain connector, emphasizing IRIS LLM management and Role-Based Access Control (RBAC).

## Solution Overview

The proposed solution is a **Patient Encounter Briefing Tool**. This web-based application assists clinicians by rapidly summarizing a patient's recent clinical history and current status using standard FHIR data. 

The architecture involves exposing FHIR data via the FHIR SQL Builder through the AI Hub using MCP. The front-end user experience will be delivered via an application built with Streamlit, Langchain, and LangGraph.

## Tech Stack

**IRIS Data & Hub Layer:**
* InterSystems FHIR SQL Builder
* Tool definitions authored in Python and ObjectScript
* IRIS MCP server hosting the LLM tools

**Application Layer:**
* Streamlit (User Interface)
* Langchain / LangGraph (AI Workflow Orchestration)
* IRIS-Langchain integration components

## Dependencies & Required Access

To successfully deliver this demonstration and provide a seamless capability showcase, we require clarification and access regarding the following component ownership:

* **AI Core deliverables**: Our current understanding is that the Tool Definitions and the IRIS MCP Server infrastructure will be provided by the "AI Core" project team.
* **Langchain integration**: We understand the Langchain integration components are managed by a separate team. 

**Ask for Product Managers:** We require explicit confirmation of these component responsibilities and immediate access to the Langchain integrations and work repositories to proceed without blocking development.

## Demo Features in Detail

The application will guide users through four core functional workflows, effectively transforming raw clinical records into actionable insights. This multi-layered approach showcases standard data querying alongside AI-driven summarization.

### 1. Patient Snapshot
* **Description**: Delivers a concise, high-level overview of a selected patient.
* **Data Sources**: Demographics, latest encounters, recent observations, and active medications.
* **FHIR Mapping**: Maps directly to standard FHIR resources (`Patient`, `Encounter`, `Observation`, `MedicationRequest`).
* **Value**: Allows users to instantly grasp the patient's baseline clinical context upon opening the record.

### 2. Recent Timeline View
* **Description**: Assembles the patient’s recent clinical activity into an intuitive, date-ordered timeline (e.g., covering the last 90 days).
* **Data Sources**: Encounters, observations, medication activity, and relevant clinical documents.
* **Value**: Provides a simple, chronological understanding of the sequence of care and recent health events.

### 3. Relevant Notes Search & View
* **Description**: Surfaces critical narrative context that structured FHIR data alone cannot capture. 
* **Data Sources**: Unstructured note text linked to the patient via `DocumentReference` data.
* **Technical Approach**: Leverages the InterSystems FHIR SQL Builder to project `DocumentReference` content into a schema optimized for search and review.
* **Value**: Ensures clinicians have rapid access to the qualitative insights, observations, and detailed notes recorded by other healthcare providers.

### 4. Draft Handover Summary
* **Description**: An automated, AI-generated clinical briefing.
* **Workflow**: Synthesizes the structured data gathered from the Patient Snapshot and Timeline View, alongside the unstructured data from Relevant Notes, into a cohesive, highly readable handover document.
* **Value**: Demonstrates the true power of the AI Hub by combining a robust FHIR data layer, SQL-projected analytics/search, and document retrieval with LLM summarization to significantly reduce clinician cognitive load.

## Addendum & Hackathon Scope

To maximize the broader applicability of the AI Hub across different use cases, our hackathon strategy also includes:

* **Cross-Industry Demonstration**: Building a non-healthcare equivalent of the primary demo, focusing on the same technical patterns and features but applied to a different industry dataset.
* **Synthetic Datasets**: Providing large, synthetically generated datasets spanning multiple sectors to ensure participants have high-quality data for their specific projects.
* **Hackathon Tracks**: Participants will be organized into three distinct execution tracks to encourage a wide variety of AI Hub applications:
    1. Healthcare
    2. Non-Healthcare 
    3. Just for Fun / Experimental 