import json
import requests
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any
import sqlite3
import os

class EpicAPISimulation:
    """
    Simulates EPIC FHIR API endpoints for pulling patient data.
    In production, this would make actual HTTP requests to EPIC's API.
    """
    
    def __init__(self, base_url: str = "https://fhir.epic.com/api/FHIR/R4"):
        self.base_url = base_url
        self.api_key = os.getenv('EPIC_API_KEY', 'demo_key_12345')
        self.client_id = os.getenv('EPIC_CLIENT_ID', 'demo_client_id')
        self.db_path = 'demo.db'
        
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _make_epic_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Simulate making a request to EPIC's FHIR API.
        In production, this would make actual HTTP requests.
        """
        # Simulate API latency
        import time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simulate potential API errors
        if random.random() < 0.05:  # 5% chance of error
            raise requests.exceptions.RequestException("EPIC API temporarily unavailable")
        
        # In production, this would be:
        # headers = {
        #     'Authorization': f'Bearer {self._get_access_token()}',
        #     'Epic-Client-ID': self.client_id,
        #     'Content-Type': 'application/fhir+json'
        # }
        # response = requests.get(f"{self.base_url}/{endpoint}", headers=headers, params=params)
        # response.raise_for_status()
        # return response.json()
        
        # For demo, we'll return mock responses based on the endpoint
        return self._get_mock_response(endpoint, params)
    
    def _get_mock_response(self, endpoint: str, params: Dict = None) -> Dict:
        """Get mock response based on EPIC FHIR endpoint"""
        if 'Patient' in endpoint:
            return self._get_patient_fhir_response(params)
        elif 'Observation' in endpoint:
            return self._get_observation_fhir_response(params)
        elif 'DocumentReference' in endpoint:
            return self._get_document_fhir_response(params)
        elif 'Condition' in endpoint:
            return self._get_condition_fhir_response(params)
        elif 'Procedure' in endpoint:
            return self._get_procedure_fhir_response(params)
        else:
            return {"resourceType": "Bundle", "entry": []}
    
    def get_patient_by_mrn(self, mrn: str) -> Optional[Dict]:
        """
        Get patient data from EPIC using MRN.
        Simulates: GET /Patient?identifier={mrn}
        """
        try:
            # Simulate EPIC API call
            epic_response = self._make_epic_request("Patient", {"identifier": mrn})
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM patients WHERE mrn = ?
            ''', (mrn,))
            
            patient_row = cursor.fetchone()
            if not patient_row:
                return None
            
            # Convert database row to FHIR Patient resource
            patient_data = self._row_to_patient_fhir(patient_row)
            
            # Merge with EPIC response format
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 1,
                "entry": [{
                    "resource": patient_data
                }]
            }
            
        except Exception as e:
            print(f"Error getting patient from EPIC: {e}")
            return None
    
    def get_patient_observations(self, patient_id: str, category: str = None) -> Dict:
        """
        Get patient observations (labs, vitals, etc.) from EPIC.
        Simulates: GET /Observation?patient={patient_id}&category={category}
        """
        try:
            # Simulate EPIC API call
            params = {"patient": patient_id}
            if category:
                params["category"] = category
            
            epic_response = self._make_epic_request("Observation", params)
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM lab_results WHERE patient_mrn = ?
            ''', (patient_id,))
            
            lab_rows = cursor.fetchall()
            
            # Convert to FHIR Observation resources
            observations = []
            for row in lab_rows:
                observation = self._row_to_observation_fhir(row)
                observations.append(observation)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(observations),
                "entry": [{"resource": obs} for obs in observations]
            }
            
        except Exception as e:
            print(f"Error getting observations from EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    def get_patient_documents(self, patient_id: str, type: str = None) -> Dict:
        """
        Get patient documents from EPIC.
        Simulates: GET /DocumentReference?patient={patient_id}&type={type}
        """
        try:
            # Simulate EPIC API call
            params = {"patient": patient_id}
            if type:
                params["type"] = type
            
            epic_response = self._make_epic_request("DocumentReference", params)
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM clinical_documents WHERE patient_mrn = ?
            '''
            if type:
                query += ' AND document_type = ?'
                cursor.execute(query, (patient_id, type))
            else:
                cursor.execute(query, (patient_id,))
            
            doc_rows = cursor.fetchall()
            
            # Convert to FHIR DocumentReference resources
            documents = []
            for row in doc_rows:
                document = self._row_to_document_fhir(row)
                documents.append(document)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(documents),
                "entry": [{"resource": doc} for doc in documents]
            }
            
        except Exception as e:
            print(f"Error getting documents from EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    def get_patient_conditions(self, patient_id: str) -> Dict:
        """
        Get patient conditions (diagnoses) from EPIC.
        Simulates: GET /Condition?patient={patient_id}
        """
        try:
            # Simulate EPIC API call
            epic_response = self._make_epic_request("Condition", {"patient": patient_id})
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM patient_conditions WHERE patient_mrn = ?
            ''', (patient_id,))
            
            condition_rows = cursor.fetchall()
            
            # Convert to FHIR Condition resources
            conditions = []
            for row in condition_rows:
                condition = self._row_to_condition_fhir(row)
                conditions.append(condition)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(conditions),
                "entry": [{"resource": cond} for cond in conditions]
            }
            
        except Exception as e:
            print(f"Error getting conditions from EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    def get_patient_procedures(self, patient_id: str) -> Dict:
        """
        Get patient procedures from EPIC.
        Simulates: GET /Procedure?patient={patient_id}
        """
        try:
            # Simulate EPIC API call
            epic_response = self._make_epic_request("Procedure", {"patient": patient_id})
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM patient_procedures WHERE patient_mrn = ?
            ''', (patient_id,))
            
            procedure_rows = cursor.fetchall()
            
            # Convert to FHIR Procedure resources
            procedures = []
            for row in procedure_rows:
                procedure = self._row_to_procedure_fhir(row)
                procedures.append(procedure)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(procedures),
                "entry": [{"resource": proc} for proc in procedures]
            }
            
        except Exception as e:
            print(f"Error getting procedures from EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    def get_family_history(self, patient_id: str) -> Dict:
        """
        Get patient family history from EPIC.
        Simulates: GET /FamilyMemberHistory?patient={patient_id}
        """
        try:
            # Simulate EPIC API call
            epic_response = self._make_epic_request("FamilyMemberHistory", {"patient": patient_id})
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM family_history WHERE patient_mrn = ?
            ''', (patient_id,))
            
            family_rows = cursor.fetchall()
            
            # Convert to FHIR FamilyMemberHistory resources
            family_history = []
            for row in family_rows:
                family_member = self._row_to_family_history_fhir(row)
                family_history.append(family_member)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(family_history),
                "entry": [{"resource": member} for member in family_history]
            }
            
        except Exception as e:
            print(f"Error getting family history from EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    def search_patients(self, query: str) -> Dict:
        """
        Search for patients in EPIC.
        Simulates: GET /Patient?name={query}
        """
        try:
            # Simulate EPIC API call
            epic_response = self._make_epic_request("Patient", {"name": query})
            
            # Get actual data from our database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM patients WHERE 
                name LIKE ? OR mrn LIKE ?
            ''', (f'%{query}%', f'%{query}%'))
            
            patient_rows = cursor.fetchall()
            
            # Convert to FHIR Patient resources
            patients = []
            for row in patient_rows:
                patient = self._row_to_patient_fhir(row)
                patients.append(patient)
            
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(patients),
                "entry": [{"resource": patient} for patient in patients]
            }
            
        except Exception as e:
            print(f"Error searching patients in EPIC: {e}")
            return {"resourceType": "Bundle", "entry": []}
    
    # Helper methods to convert database rows to FHIR resources
    def _row_to_patient_fhir(self, row) -> Dict:
        """Convert database patient row to FHIR Patient resource"""
        if not row:
            return None
            
        return {
            "resourceType": "Patient",
            "id": f"patient-{row[0]}",
            "identifier": [{"value": row[1]}],  # MRN
            "name": [{"text": row[2]}],  # Name
            "birthDate": row[3],  # DOB
            "gender": row[4],  # Gender
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-race",
                    "valueString": row[5] if row[5] else "Unknown"
                }
            ],
            "telecom": [
                {"system": "phone", "value": row[7]} if row[7] else None,
                {"system": "email", "value": row[8]} if row[8] else None
            ],
            "address": [{"text": row[6]}] if row[6] else []
        }
    
    def _row_to_observation_fhir(self, row) -> Dict:
        """Convert database lab row to FHIR Observation resource"""
        if not row:
            return None
            
        return {
            "resourceType": "Observation",
            "id": f"obs-{row[0]}",
            "status": row[7] if row[7] else "final",
            "category": [{"coding": [{"code": "laboratory"}]}],
            "code": {"text": row[2]},
            "subject": {"reference": f"Patient/{row[1]}"},
            "effectiveDateTime": row[3],
            "valueQuantity": {
                "value": row[4] if row[4] is not None else None,
                "unit": row[5] if row[5] else None
            },
            "referenceRange": [{"text": row[6]}] if row[6] else [],
            "performer": [{"display": row[9]}] if row[9] else []
        }
    
    def _row_to_document_fhir(self, row) -> Dict:
        """Convert database document row to FHIR DocumentReference resource"""
        if not row:
            return None
            
        return {
            "resourceType": "DocumentReference",
            "id": f"doc-{row[0]}",
            "status": "current",
            "type": {"text": row[2]},
            "subject": {"reference": f"Patient/{row[1]}"},
            "date": row[3],
            "content": [{"attachment": {"title": row[4]}}],
            "author": [{"display": row[6]}] if row[6] else [],
            "description": row[5] if row[5] else None
        }
    
    def _row_to_condition_fhir(self, row) -> Dict:
        """Convert database condition row to FHIR Condition resource"""
        if not row:
            return None
            
        return {
            "resourceType": "Condition",
            "id": f"cond-{row[0]}",
            "clinicalStatus": {"coding": [{"code": row[4] if row[4] else "active"}]},
            "code": {"text": row[2]},
            "subject": {"reference": f"Patient/{row[1]}"},
            "onsetDateTime": row[3],
            "severity": {"text": row[6]} if row[6] else None
        }
    
    def _row_to_procedure_fhir(self, row) -> Dict:
        """Convert database procedure row to FHIR Procedure resource"""
        if not row:
            return None
            
        return {
            "resourceType": "Procedure",
            "id": f"proc-{row[0]}",
            "status": row[5] if row[5] else "completed",
            "code": {"text": row[2]},
            "subject": {"reference": f"Patient/{row[1]}"},
            "performedDateTime": row[3],
            "performer": [{"display": row[6]}] if row[6] else [],
            "location": {"display": row[7]} if row[7] else None
        }
    
    def _row_to_family_history_fhir(self, row) -> Dict:
        """Convert database family history row to FHIR FamilyMemberHistory resource"""
        if not row:
            return None
            
        return {
            "resourceType": "FamilyMemberHistory",
            "id": f"family-{row[0]}",
            "status": "completed",
            "patient": {"reference": f"Patient/{row[1]}"},
            "relationship": {"text": row[2]},
            "condition": [{"code": {"text": row[3]}}],
            "ageAge": {"value": row[4]} if row[4] else None,
            "deceasedBoolean": row[5] == "deceased" if row[5] else False
        }
    
    def _get_patient_fhir_response(self, params: Dict) -> Dict:
        """Mock EPIC response for Patient endpoint"""
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 1,
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "id": "demo-patient-1",
                    "identifier": [{"value": params.get("identifier", "unknown")}]
                }
            }]
        }
    
    def _get_observation_fhir_response(self, params: Dict) -> Dict:
        """Mock EPIC response for Observation endpoint"""
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 5,
            "entry": []
        }
    
    def _get_document_fhir_response(self, params: Dict) -> Dict:
        """Mock EPIC response for DocumentReference endpoint"""
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 3,
            "entry": []
        }
    
    def _get_condition_fhir_response(self, params: Dict) -> Dict:
        """Mock EPIC response for Condition endpoint"""
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 2,
            "entry": []
        }
    
    def _get_procedure_fhir_response(self, params: Dict) -> Dict:
        """Mock EPIC response for Procedure endpoint"""
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 4,
            "entry": []
        }
