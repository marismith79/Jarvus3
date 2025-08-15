import json
import os
from datetime import datetime, timedelta
import random

class MockEHRSystem:
    def __init__(self):
        self.patients = {}
        self._load_realistic_data()
    
    def _load_realistic_data(self):
        """Load realistic EHR data from JSON file"""
        json_file_path = os.path.join(os.path.dirname(__file__), 'mock_ehr_pa_oncology_genomics_with_notes_and_fhir.json')
        
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                self.patients[mrn] = patient_record
                
        except FileNotFoundError:
            print(f"Warning: Mock EHR JSON file not found at {json_file_path}")
            # Fallback to basic mock data
            self._initialize_basic_patients()
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            self._initialize_basic_patients()
    
    def _initialize_basic_patients(self):
        """Fallback basic patient data if JSON file is not available"""
        self.patients = {
            "MRN001": {
                "patient_admin": {
                    "mrn": "MRN001",
                    "name": {"given": "John", "family": "Smith"},
                    "dob": "1985-03-15",
                    "sex_at_birth": "Male"
                },
                "coverage": {"payer": "Original Medicare"},
                "diagnosis_and_stage": {"description": "Family history of breast cancer"},
                "genomic_testing": {"current_test": {"test_name": "BRCA1/BRCA2 Genetic Testing", "cpt": "81162"}},
                "clinical_notes": []
            }
        }
    
    def get_patient_data(self, mrn):
        """Get patient demographic and administrative data"""
        if mrn not in self.patients:
            return None
        
        patient = self.patients[mrn]
        admin = patient['patient_admin']
        
        return {
            'mrn': admin['mrn'],
            'name': f"{admin['name']['given']} {admin['name']['family']}",
            'dob': admin['dob'],
            'gender': admin['sex_at_birth'],
            'race': admin.get('race', 'Unknown'),
            'address': admin.get('address', ''),
            'phone': admin.get('contact', {}).get('phone', ''),
            'email': admin.get('contact', {}).get('email', ''),
            'insurance_provider': patient['coverage']['payer'],
            'insurance_plan': patient['coverage']['plan_type'],
            'member_id': patient['coverage']['member_id'],
            'diagnosis': patient['diagnosis_and_stage']['description'],
            'icd10': patient['diagnosis_and_stage']['primary_icd10'],
            'stage': patient['diagnosis_and_stage']['stage_group'],
            'ecog': patient['diagnosis_and_stage']['ecog'],
            'diagnosis_date': patient['diagnosis_and_stage']['date_of_diagnosis']
        }
    
    def get_patient_documents(self, mrn):
        """Get patient clinical documents"""
        if mrn not in self.patients:
            return []
        
        patient = self.patients[mrn]
        documents = []
        
        # Add pathology report
        if 'pathology_synoptic' in patient:
            path = patient['pathology_synoptic']
            documents.append({
                'type': 'Pathology Report',
                'date': path['specimen']['collection_date'],
                'content': f"Specimen: {path['specimen']['type']} from {path['specimen']['site']}. Histology: {path['histology']}, Grade: {path['grade']}, Size: {path['tumor_size_mm']}mm. Margins: {path['margins']}, LVI: {path['lvi']}.",
                'doc_id': f"DOC_{mrn}_PATH"
            })
        
        # Add genomic testing report
        if 'genomic_testing' in patient and 'current_test' in patient['genomic_testing']:
            test = patient['genomic_testing']['current_test']
            documents.append({
                'type': 'Genomic Testing Report',
                'date': test['report_date'],
                'content': f"Test: {test['test_name']} (CPT {test['cpt']}). Methodology: {test['methodology']}. Genes analyzed: {test['genes_analyzed']}.",
                'doc_id': f"DOC_{mrn}_GEN"
            })
        
        # Add clinical notes
        for note in patient.get('clinical_notes', []):
            documents.append({
                'type': note['type'],
                'date': note['date'],
                'author': note['author'],
                'content': note['text'],
                'doc_id': note['note_id']
            })
        
        return documents
    
    def get_family_history(self, mrn):
        """Get patient family history"""
        if mrn not in self.patients:
            return []
        
        return self.patients[mrn].get('family_history', [])
    
    def get_lab_results(self, mrn):
        """Get patient lab results"""
        if mrn not in self.patients:
            return []
        
        return self.patients[mrn].get('labs', [])
    
    def get_imaging(self, mrn):
        """Get patient imaging reports"""
        if mrn not in self.patients:
            return []
        
        return self.patients[mrn].get('imaging', [])
    
    def get_treatment_history(self, mrn):
        """Get patient treatment history"""
        if mrn not in self.patients:
            return []
        
        patient = self.patients[mrn]
        treatments = []
        
        # Add systemic therapies
        for therapy in patient.get('treatment_history', {}).get('systemic_therapies', []):
            treatments.append({
                'type': 'Systemic Therapy',
                'drug': therapy['drug'],
                'start_date': therapy['start'],
                'end_date': therapy.get('stop'),
                'line': therapy['line_of_therapy']
            })
        
        return treatments
    
    def search_documents(self, mrn, query):
        """Search patient documents for specific terms"""
        documents = self.get_patient_documents(mrn)
        results = []
        
        query_lower = query.lower()
        for doc in documents:
            if query_lower in doc['content'].lower():
                results.append(doc)
        
        return results
    
    def get_clinical_summary(self, mrn):
        """Get comprehensive clinical summary"""
        if mrn not in self.patients:
            return None
        
        patient = self.patients[mrn]
        admin = patient['patient_admin']
        diagnosis = patient['diagnosis_and_stage']
        
        summary = {
            'patient_name': f"{admin['name']['given']} {admin['name']['family']}",
            'mrn': admin['mrn'],
            'dob': admin['dob'],
            'diagnosis': diagnosis['description'],
            'stage': diagnosis['stage_group'],
            'ecog': diagnosis['ecog'],
            'diagnosis_date': diagnosis['date_of_diagnosis'],
            'insurance': patient['coverage']['payer'],
            'ordering_provider': patient['ordering_provider']['name'],
            'facility': patient['rendering_facility']['org_name'],
            'current_test': patient['genomic_testing']['current_test']['test_name'],
            'cpt_code': patient['genomic_testing']['current_test']['cpt'],
            'family_history': len(patient.get('family_history', [])),
            'lab_results': len(patient.get('labs', [])),
            'imaging_reports': len(patient.get('imaging', [])),
            'clinical_notes': len(patient.get('clinical_notes', [])),
            'pa_status': patient.get('pa_metadata', {}).get('status', 'Unknown')
        }
        
        return summary
    
    def get_genomic_variants(self, mrn):
        """Get genomic variants from testing"""
        if mrn not in self.patients:
            return []
        
        patient = self.patients[mrn]
        if 'genomic_testing' in patient and 'current_test' in patient['genomic_testing']:
            return patient['genomic_testing']['current_test']['results']['variants']
        
        return []
    
    def get_pa_metadata(self, mrn):
        """Get prior authorization metadata"""
        if mrn not in self.patients:
            return None
        
        return self.patients[mrn].get('pa_metadata', {})
