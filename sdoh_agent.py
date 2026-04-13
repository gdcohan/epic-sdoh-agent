from openai import OpenAI
import os, json

class SDOHAgent:
    def __init__(self):
        self.ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze_notes(self, notes):
        if not notes: return None
        
        context = "\n".join([f"Date: {n['date']}\nNote: {n['text']}\n---" for n in notes])
        
        prompt = """
        Analyze the provided medical notes to create a SINGLE consolidated SDOH profile for this patient.
        Do not list every date. Instead, summarize their current situation based on the most recent evidence.

        Focus on: Housing, Food, Transport, Financial insecurity, though you can use your discretion to identify other relevant challenges.
        Return a JSON object: 
        {
        "summary": "Brief clinical overview",
        "risks": [{"category": "...", "severity": "...", "evidence": "...", "citation": "provide the source of the evidence cited, along with the relevant provider, author, etc."}],
        "overall_risk_score": 1-10
        }
        """
        response = self.ai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": context}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)