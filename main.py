import os
import json
import time
from epic_client import EpicFHIRClient
from sdoh_agent import SDOHAgent
import sandbox_utils

# Initializing
client = EpicFHIRClient()
agent = SDOHAgent()

def run_pipeline(use_sandbox_workaround=True):
    # STEP 1: Get the Census
    if use_sandbox_workaround:
        census = sandbox_utils.get_mock_census()
    else:
        census = client.get_hospital_census()

    print(f"--- 🚀 Starting Pipeline for {len(census)} patients ---\n")

    # STEP 2: Process the Census
    for patient_id in census:
        print(f"👉 Processing Patient: {patient_id}")
        
        try:
            # Fetch Notes
            notes = client.get_clinical_notes(patient_id)
            
            if use_sandbox_workaround:
                notes = sandbox_utils.inject_test_risk(notes)

            # Run AI Analysis
            analysis = agent.analyze_notes(notes)
            
            # Print a clean summary instead of raw JSON
            if analysis:
                print(f"   ✅ Analysis Complete. Risk Score: {analysis.get('overall_risk_score', 'N/A')}/10")
                print(json.dumps(analysis, indent=2))
            else:
                print("   ⚠️ No notes available for analysis.")

        except Exception as e:
            # This is the 'Circuit Breaker' - it catches the 400 and keeps the loop alive
            print(f"   ❌ ERROR for patient {patient_id}: {e}")
            continue # Move to the next patient in the census

        print("-" * 40)

if __name__ == "__main__":
    run_pipeline(use_sandbox_workaround=True)