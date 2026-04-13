# test_it.py
from epic_client import EpicFHIRClient

client = EpicFHIRClient()

try:
    print("Initiating handshake with Epic...")
    # Using the standard Sandbox Test Patient: Jason Argonaut
    notes = client.get_clinical_notes("erXuFYUfucBZaryVksYEcMg3")
    
    print(f"\n✅ SUCCESS! Connection established.")
    print(f"Retrieved {len(notes)} clinical notes for Jason Argonaut.")
    
    if notes:
        print("\n--- Latest Note Excerpt ---")
        print(notes[0]['text'][:500] + "...")
        
except Exception as e:
    print(f"\n❌ CONNECTION FAILED")
    print(f"Error details: {e}")