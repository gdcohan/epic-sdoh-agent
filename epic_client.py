import os, jwt, time, uuid, requests, base64
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

    def _authenticate(self):
        """Standard OAuth2 Client Credentials Handshake."""
        if self.access_token and time.time() < self.token_expiry:
            return 
        
        # JWT Generation Logic
        with open(self.private_key_path, 'r') as k:
            private_key = k.read()
        
        now = int(time.time()) - 60
        claims = {
            "iss": self.client_id, "sub": self.client_id,
            "aud": self.token_url, "jti": str(uuid.uuid4()),
            "iat": now, "exp": now + 300
        }
        signed_jwt = jwt.encode(claims, private_key, algorithm="RS384", headers={"alg": "RS384", "typ": "JWT", "kid": "my-agent-v1"})

        # Token Request
        payload = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": signed_jwt,
            "scope": "system/Patient.read system/DocumentReference.read system/Binary.read system/Encounter.read"
        }
        
        res = requests.post(self.token_url, data=payload)
        res.raise_for_status()
        data = res.json()
        self.access_token = data["access_token"]
        self.token_expiry = time.time() + data.get("expires_in", 300) - 10

    def get_hospital_census(self):
        """
        PRODUCTION IDEAL: Fetches patients currently in the building.
        Filters: In-Progress (active) + IMP (Inpatient).
        """
        self._authenticate()
        params = {
            "status": "in-progress",
            "class": "http://terminology.hl7.org/CodeSystem/v3-ActCode|imp"
        }
        res = requests.get(f"{self.base_url}/Encounter", 
                           headers={"Authorization": f"Bearer {self.access_token}"}, 
                           params=params)
        res.raise_for_status()
        
        # Return unique patient IDs from the census
        return list(set([e['resource']['subject']['reference'].split('/')[-1] 
                         for e in res.json().get('entry', [])]))

    def get_clinical_notes(self, patient_id):
        """PRODUCTION IDEAL: Fetches clinical notes via DocumentReference -> Binary."""
        self._authenticate()
        headers = {"Authorization": f"Bearer {self.access_token}", "Accept": "application/fhir+json"}
        
        res = requests.get(f"{self.base_url}/DocumentReference?patient={patient_id}", headers=headers)
        res.raise_for_status()
        
        notes = []
        for entry in res.json().get('entry', []):
            resource = entry.get('resource', {})
            # Filter for Progress Notes or Consults
            if resource.get('type', {}).get('text') in ["Progress Notes", "Consults"]:
                for content in resource.get('content', []):
                    url = content.get('attachment', {}).get('url')
                    if url:
                        # Follow the binary link
                        full_url = url if url.startswith("http") else f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
                        bin_res = requests.get(full_url, headers=headers)
                        if bin_res.status_code == 200:
                            # Handle both JSON-wrapped and raw text responses
                            text = bin_res.json().get('data') if 'json' in bin_res.headers.get('Content-Type', '') else bin_res.text
                            notes.append({"date": resource.get('date'), "text": text})
        return notes