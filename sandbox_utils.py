def get_mock_census():
    """
    Simulates the get_hospital_census() response.
    Use this when the sandbox returns a 400 for broad Encounter searches.
    """
    return [
        "erXuFYUfucBZaryVksYEcMg3", # Jason Argonaut (Usually reliable)
        "eNR.A-e9uE.T6p8X06p7A.A3", # James Bond
        "e63Sjt-79659E8nMeTr9uWw3"  # Camila Lopez
    ]

def inject_test_risk(notes_list):
    """
    Injects a synthetic SDOH risk into a notes list to test the AI.
    """
    notes_list.append({
        "date": "2026-04-10",
        "text": "Patient mentions staying in a shelter and unable to afford insulin."
    })
    return notes_list