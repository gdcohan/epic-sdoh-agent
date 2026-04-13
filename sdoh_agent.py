import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from epic_client import EpicFHIRClient

load_dotenv()

# 1. Initialize our tools
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ehr = EpicFHIRClient()

def run_sdoh_screening(patient_id):
    print(f"--- 🧠 SDOH AGENT START: Patient {patient_id} ---")
    
    # 2. Fetch the raw data from your Epic Client
    raw_notes = ehr.get_clinical_notes(patient_id)
    if not raw_notes:
        print("No narrative data found for this patient.")
        return

    # 3. Flatten the notes for the LLM
    # We include the date and type so the AI understands the timeline
    context_blob = ""
    for n in raw_notes:
        context_blob += f"\nDate: {n['date']} | Type: {n['type']}\nContent: {n['text']}\n{'-'*30}"

    print(f"Feeding {len(raw_notes)} notes to the LLM for analysis...")
    # Manual injection for testing purposes
    context_blob += "\nDate: 2024-05-20 | Type: Progress Notes\nContent: Patient mentioned during the visit that they were recently evicted and are currently staying in their sedan. They expressed concern that they cannot keep their insulin cool without a refrigerator.\n"
    # 4. The Instruction (System Prompt)
    # We tell the AI to ignore the HTML tags and focus on specific SDOH flags
    system_instr = """
    You are a clinical social work assistant. You will be provided with medical notes (some in HTML format).
    Your task is to scan the narrative for any signs of Social Determinants of Health (SDOH) risks.
    
    Specifically look for:
    1. Housing: Homelessness, eviction threats, poor living conditions.
    2. Food: Hunger, "skipping meals," inability to afford groceries.
    3. Transportation: Missed appointments due to no car/bus, distance to clinic.
    4. Financial: Inability to afford medications (insulin, etc.) or copays.

    Return your analysis as a JSON object with this structure:
    {
      "patient_summary": "This should be a 2-sentence clinical snapshot",
      "risks_identified": [
        {"category": "Housing", "severity": "High/Medium/Low", "evidence": "direct citation from note", "citation": 
        information detailing provenance of citation", "reasoning": "why this is a risk"},
        {"category": "another relevant category", severity: "High/Medium/Low", "evidence": "see first example", "citation": "see first example", "reasoning": "see first example" }
      ],
      "overall_risk_score": 1-10
    }
    """

    # 5. The Analysis Loop
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using 4o for superior HTML handling
            messages=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": f"Analyze these patient notes:\n{context_blob}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        
        print("\n" + "="*40)
        print("📊 AGENT ANALYSIS REPORT")
        print("="*40)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"AI Analysis failed: {e}")

if __name__ == "__main__":
    # Test with Jason Argonaut
    run_sdoh_screening("erXuFYUfucBZaryVksYEcMg3")