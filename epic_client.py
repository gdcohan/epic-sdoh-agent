import os
import jwt
import time
import uuid
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

class EpicFHIRClient:
    def __init__(self):
        self.client_id = os.getenv("EPIC_CLIENT_ID")
        self.private_key_path = os.getenv("EPIC_PRIVATE_KEY_PATH")
        self.base_url = os.getenv("EPIC_FHIR_BASE_URL")
        self.token_url = os.getenv("EPIC_TOKEN_URL")
        self.access_token = None
        self.token_expiry = 0

    def _generate_jwt(self):
        with open(self.private_key_path, 'r') as key_file:
            private_key = key_file.read()
        
        now = int(time.time()) - 60 
        
        headers = {
            "alg": "RS384",
            "typ": "JWT",
            "kid": "my-agent-v1"
        }
        
        claims = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_url,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 300 
        }
        return jwt.encode(claims, private_key, algorithm="RS384", headers=headers)

    def _authenticate(self):
        signed_jwt = self._generate_jwt()
        # Explicitly asking for the scopes we need
        requested_scopes = "system/Patient.read system/DocumentReference.read system/Binary.read"

        payload = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": signed_jwt,
            "scope": requested_scopes
        }
        
        response = requests.post(self.token_url, data=payload)
        response.raise_for_status()
        data = response.json()
        
        self.access_token = data["access_token"]
        self.token_expiry = time.time() + data.get("expires_in", 300) - 10
        
        granted_scopes = data.get("scope", "No scopes listed")
        print(f"DEBUG: Scopes granted by Epic: {granted_scopes}")

    def get_hospital_census(self, limit=5):
        self._authenticate()
        headers = {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}
        
        # 1. The "Strict" Census Search: Active Inpatients
        # status=in-progress means they are currently in the building
        # class=IMP means Inpatient
        print("DEBUG: Searching for active 'in-progress' inpatients...")
        endpoint = f"{self.base_url}/Encounter?status=in-progress&class=IMP&_count={limit}"
        
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 2. The Creative Workaround: If the hospital is "empty," look for recent discharges
        if not data.get("entry"):
            print("  --> Census empty. Broadening search to any recent Inpatient/Emergency encounters...")
            endpoint = f"{self.base_url}/Encounter?class=IMP,EMR&_sort=-date&_count={limit}"
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()

        patient_ids = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            patient_ref = resource.get("subject", {}).get("reference", "")
            
            if "Patient/" in patient_ref:
                p_id = patient_ref.split("/")[-1]
                # We also want to capture the 'reason' for the visit if available
                reason = resource.get("reasonCode", [{}])[0].get("text", "Unknown Reason")
                if p_id not in [p['id'] for p in patient_ids]:
                    patient_ids.append({"id": p_id, "reason": reason})
                    
        return patient_ids
    
    def get_clinical_notes(self, patient_id):
        self._authenticate()
        headers = {
            "Authorization": f"Bearer {self.access_token}", 
            "Accept": "application/fhir+json"
        }
        
        endpoint = f"{self.base_url}/DocumentReference?patient={patient_id}"
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        extracted = []
        TARGET_TYPES = ["Progress Notes", "Consults", "Nursing Note", "Patient Instructions"]

        for entry in data.get("entry", []):
            res = entry.get("resource", {})
            doc_type = res.get("type", {}).get("text", "Unknown")
            
            if doc_type in TARGET_TYPES:
                print(f"DEBUG: Processing {doc_type}...")
                
                for content in res.get("content", []):
                    attachment = content.get("attachment", {})
                    
                    if "data" in attachment:
                        encoded_data = attachment["data"]
                        self._process_encoded_text(encoded_data, doc_type, res.get("date"), extracted)
                    
                    elif "url" in attachment:
                        binary_url = attachment["url"]
                        if not binary_url.startswith("http"):
                            binary_url = f"{self.base_url.rstrip('/')}/{binary_url.lstrip('/')}"
                        
                        print(f"  --> Fetching Binary: {binary_url}")
                        bin_res = requests.get(binary_url, headers=headers)
                        
                        if bin_res.status_code == 200:
                            content_type = bin_res.headers.get('Content-Type', '')
                            if 'json' in content_type:
                                try:
                                    bin_json = bin_res.json()
                                    self._process_encoded_text(bin_json.get("data"), doc_type, res.get("date"), extracted)
                                except Exception:
                                    print("  --> Error parsing Binary JSON wrapper.")
                            else:
                                print(f"  --> SUCCESS: Extracted {len(bin_res.text)} raw characters.")
                                extracted.append({
                                    "date": res.get("date"),
                                    "type": doc_type,
                                    "text": bin_res.text
                                })
                        else:
                            print(f"  --> Binary Fetch Failed: {bin_res.status_code}")
        return extracted

    def _process_encoded_text(self, encoded_data, doc_type, date, extracted_list):
        if not encoded_data:
            return
        try:
            decoded_text = base64.b64decode(encoded_data).decode('utf-8')
            extracted_list.append({
                "date": date,
                "type": doc_type,
                "text": decoded_text
            })
            print(f"  --> SUCCESS: Decoded {len(decoded_text)} characters.")
        except Exception as e:
            print(f"  --> Decoding error: {e}")