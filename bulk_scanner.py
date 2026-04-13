import time
from epic_client import EpicFHIRClient
from sdoh_agent import run_sdoh_screening

ehr = EpicFHIRClient()

def run_census_scan():
    print("--- 🏥 HOSPITAL CENSUS AGENT ---")
    
    # 1. Fetch the census
    census = ehr.get_hospital_census(limit=5)
    
    # 2. Creative Workaround: The Mock Census
    if not census:
        print("\n⚠️  No encounters found in Sandbox. Falling back to Mock Census for testing...")
        census = [
            {"id": "erXuFYUfucBZaryVksYEcMg3", "reason": "Jason Argonaut (Mock)"},
            {"id": "e63Sjt-79659E8nMeTr9uWw3", "reason": "Camila Lopez (Mock)"}
        ]
    
    print(f"Found {len(census)} patients to screen.\n")

    for patient in census:
        p_id = patient['id']
        reason = patient['reason']
        
        print(f"👉 Now Screening: {p_id} (Admitted for: {reason})")
        try:
            run_sdoh_screening(p_id)
            print("-" * 50)
            time.sleep(1) # Polite pause for API rate limits
        except Exception as e:
            print(f"   ❌ Error screening {p_id}: {e}")

if __name__ == "__main__":
    run_census_scan()