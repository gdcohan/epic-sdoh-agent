# EPIC SDOH Analysis Agent

An automated clinical intelligence pipeline that identifies Social Determinants of Health (SDOH) risks by analyzing narrative clinical notes within an Epic FHIR environment.

## Overview
This project provides a robust framework for scanning a hospital census and leveraging Large Language Models (LLMs) to detect housing, food, transportation, and financial instabilities that are often buried in unstructured clinical text. It is designed with a clear separation between production-grade FHIR integration and sandbox-specific simulation layers.

## Core Features
* **FHIR Narrative Ingestion:** Navigates the Epic `DocumentReference` and `Binary` resources to extract raw clinical text (Progress Notes, Consults, and Nursing Notes).
* **Automated Risk Triage:** Uses OpenAI’s GPT-4o to analyze clinical narratives, providing a structured JSON report with evidence-based reasoning and an overall risk score (1–10).
* **Referral Deduplication:** Includes logic to check for existing `ServiceRequest` (Social Work) entries to prevent clinician alert fatigue.

## Project Structure
* **`epic_client.py`**: The production-ready FHIR client handling OAuth2 handshakes (SMART v2), Patient Search, Encounter Census, and Binary resource fetching.
* **`sdoh_agent.py`**: The "Brain" of the project. Contains the AI logic and prompts required to transform narrative fragments into clinical insights.
* **`main.py`**: The orchestrator that manages the census loop, triggers the analysis, and saves timestamped reports for clinical review.
* **`sandbox_utils.py`**: A dedicated utility layer for simulating census data and injecting test risks to verify agent performance within limited sandbox environments.

## Tech Stack
* **Language:** Python 3.x
* **EHR Integration:** Epic FHIR API (R4)
* **Intelligence:** OpenAI API (GPT-4o)
* **Security:** JWT-based OAuth2 with RS384 signing

## Setup
1. Clone the repository and create a virtual environment.
2. Install dependencies: `pip install requests PyJWT openai python-dotenv`.
3. Configure your `.env` file with your Epic Client ID, Private Key path, and OpenAI API Key.
4. Run the orchestrator: `python main.py`.
