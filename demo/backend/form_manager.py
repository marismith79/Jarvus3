import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from .mock_ehr_system import MockEHRSystem

class FormManager:
    def __init__(self, ehr_system: MockEHRSystem):
        self.ehr_system = ehr_system
        self.form_templates = self._load_form_templates()
        self.field_mappings = self._load_field_mappings()
        
    def _load_form_templates(self) -> Dict[str, Dict]:
        """Load form templates for different insurance companies and CPT codes"""
        return {
            "HUSKY": {
                "name": "HUSKY Health Genetic Testing Prior Authorization",
                "sections": [
                    {
                        "id": "member_info",
                        "title": "Member Information",
                        "fields": [
                            {"id": "member_id", "label": "Member ID", "type": "text", "required": True},
                            {"id": "dob", "label": "Date of Birth", "type": "date", "required": True},
                            {"id": "member_name", "label": "Member Name", "type": "text", "required": True},
                            {"id": "address", "label": "Address", "type": "text", "required": True}
                        ]
                    },
                    {
                        "id": "testing_info",
                        "title": "Requested Testing Information",
                        "fields": [
                            {"id": "test_name", "label": "Test Name", "type": "text", "required": True},
                            {"id": "date_of_service", "label": "Date of Service", "type": "date", "required": True},
                            {"id": "test_type", "label": "Type of Test", "type": "text", "required": True},
                            {"id": "genes_tested", "label": "Gene Mutation Tested For", "type": "text", "required": True},
                            {"id": "icd10_codes", "label": "ICD-10 Codes", "type": "text", "required": True},
                            {"id": "cpt_requests", "label": "CPT Requests", "type": "text", "required": True}
                        ]
                    },
                    {
                        "id": "clinical_docs",
                        "title": "Clinical Documentation",
                        "fields": [
                            {"id": "ordering_provider", "label": "Ordering Provider", "type": "text", "required": True},
                            {"id": "genetic_counseling", "label": "Genetic Counseling", "type": "text", "required": False},
                            {"id": "clinical_indication", "label": "Clinical Indication", "type": "text", "required": True},
                            {"id": "treatment_history", "label": "Treatment History", "type": "text", "required": False}
                        ]
                    },
                    {
                        "id": "history",
                        "title": "Personal & Family History",
                        "fields": [
                            {"id": "personal_history", "label": "Personal History", "type": "text", "required": False},
                            {"id": "family_history", "label": "Family History", "type": "text", "required": False},
                            {"id": "prior_genetic_testing", "label": "Prior Genetic Testing", "type": "text", "required": False}
                        ]
                    },
                    {
                        "id": "provider_info",
                        "title": "Provider Information",
                        "fields": [
                            {"id": "billing_provider", "label": "Billing Provider", "type": "text", "required": True},
                            {"id": "provider_address", "label": "Provider Address", "type": "text", "required": True}
                        ]
                    }
                ]
            },
            "MEDICARE": {
                "name": "Medicare NCD 90.2 Prior Authorization",
                "sections": [
                    {
                        "id": "patient_info",
                        "title": "Patient Information",
                        "fields": [
                            {"id": "patient_name", "label": "Patient Name", "type": "text", "required": True},
                            {"id": "mrn", "label": "Medical Record Number", "type": "text", "required": True},
                            {"id": "dob", "label": "Date of Birth", "type": "date", "required": True},
                            {"id": "diagnosis", "label": "Primary Diagnosis", "type": "text", "required": True}
                        ]
                    },
                    {
                        "id": "ncd_criteria",
                        "title": "NCD 90.2 Criteria",
                        "fields": [
                            {"id": "advanced_cancer", "label": "Advanced Cancer Diagnosis", "type": "boolean", "required": True},
                            {"id": "no_prior_comprehensive_ngs", "label": "No Prior Comprehensive NGS", "type": "boolean", "required": True},
                            {"id": "clinical_indication", "label": "Clinical Indication for Testing", "type": "text", "required": True},
                            {"id": "specimen_adequacy", "label": "Specimen Adequacy", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }
    
    def _load_field_mappings(self) -> Dict[str, Dict]:
        """Load field mappings from EHR to form fields"""
        return {
            "patient_name": {
                "ehr_field": "name",
                "extraction_method": "direct",
                "validation": "required"
            },
            "mrn": {
                "ehr_field": "mrn",
                "extraction_method": "direct",
                "validation": "required"
            },
            "dob": {
                "ehr_field": "dob",
                "extraction_method": "direct",
                "validation": "required"
            },
            "diagnosis": {
                "ehr_field": "diagnosis",
                "extraction_method": "direct",
                "validation": "required"
            },
            "stage": {
                "ehr_field": "stage",
                "extraction_method": "direct",
                "validation": "optional"
            },
            "ordering_provider": {
                "ehr_field": "ordering_provider",
                "extraction_method": "direct",
                "validation": "required"
            },
            "family_history": {
                "ehr_field": "family_history",
                "extraction_method": "document_search",
                "search_terms": ["family history", "genetic", "inherited"],
                "validation": "optional"
            },
            "genetic_counseling": {
                "ehr_field": "genetic_counseling",
                "extraction_method": "document_search",
                "search_terms": ["genetic counseling", "counseling note"],
                "validation": "conditional"
            }
        }
    
    def get_form_template(self, insurance_provider: str, cpt_code: str) -> Dict:
        """Get the appropriate form template based on insurance provider and CPT code"""
        # Map CPT codes to insurance-specific forms
        cpt_to_form = {
            "81445": "HUSKY",  # Comprehensive genomic profiling
            "81450": "HUSKY",  # Gene panel testing
            "81162": "MEDICARE",  # BRCA testing
            "81211": "MEDICARE"   # Other genetic testing
        }
        
        form_type = cpt_to_form.get(cpt_code, "HUSKY")
        return self.form_templates.get(form_type, self.form_templates["HUSKY"])
    
    def extract_ehr_data_for_form(self, patient_mrn: str, form_template: Dict, 
                                 expert_knowledge: Dict = None) -> Dict[str, Any]:
        """Extract EHR data for form completion with citations"""
        if not patient_mrn:
            return {"error": "No patient MRN provided"}
        
        patient_data = self.ehr_system.get_patient_data(patient_mrn)
        if not patient_data:
            return {"error": f"Patient data not found for MRN: {patient_mrn}"}
        
        extracted_data = {
            "patient_info": {},
            "ehr_citations": [],
            "missing_fields": [],
            "validation_errors": []
        }
        
        # Extract data for each section
        for section in form_template["sections"]:
            section_data = {}
            
            for field in section["fields"]:
                field_id = field["id"]
                field_result = self._extract_field_data(
                    field_id, field, patient_data, patient_mrn, expert_knowledge
                )
                
                if field_result["success"]:
                    section_data[field_id] = field_result["data"]
                    extracted_data["ehr_citations"].append(field_result["citation"])
                else:
                    if field["required"]:
                        extracted_data["missing_fields"].append({
                            "field_id": field_id,
                            "label": field["label"],
                            "reason": field_result["error"]
                        })
                    else:
                        section_data[field_id] = {"value": "", "source": "Not available"}
            
            extracted_data["patient_info"][section["id"]] = section_data
        
        return extracted_data
    
    def _extract_field_data(self, field_id: str, field_config: Dict, 
                           patient_data: Dict, patient_mrn: str, 
                           expert_knowledge: Dict = None) -> Dict:
        """Extract data for a specific field"""
        mapping = self.field_mappings.get(field_id, {})
        extraction_method = mapping.get("extraction_method", "direct")
        
        try:
            if extraction_method == "direct":
                return self._extract_direct_field(field_id, mapping, patient_data, patient_mrn)
            elif extraction_method == "document_search":
                return self._extract_from_documents(field_id, mapping, patient_mrn, expert_knowledge)
            elif extraction_method == "computed":
                return self._extract_computed_field(field_id, mapping, patient_data, patient_mrn)
            else:
                return {"success": False, "error": f"Unknown extraction method: {extraction_method}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_direct_field(self, field_id: str, mapping: Dict, 
                             patient_data: Dict, patient_mrn: str) -> Dict:
        """Extract field data directly from patient data"""
        ehr_field = mapping.get("ehr_field", field_id)
        value = patient_data.get(ehr_field, "")
        
        if not value and mapping.get("validation") == "required":
            return {"success": False, "error": f"Required field {field_id} not found in EHR"}
        
        citation = {
            "field": field_id,
            "value": value,
            "source": "EHR System",
            "url": f"/ehr/patient/{patient_mrn}/field/{ehr_field}",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": {"value": value, "source": "EHR"},
            "citation": citation
        }
    
    def _extract_from_documents(self, field_id: str, mapping: Dict, 
                               patient_mrn: str, expert_knowledge: Dict = None) -> Dict:
        """Extract field data by searching patient documents"""
        search_terms = mapping.get("search_terms", [field_id])
        
        # Search documents using expert knowledge if available
        if expert_knowledge and "document_search_strategies" in expert_knowledge:
            search_strategy = expert_knowledge["document_search_strategies"].get(field_id)
            if search_strategy:
                search_terms.extend(search_strategy.get("additional_terms", []))
        
        documents = self.ehr_system.get_patient_documents(patient_mrn)
        relevant_docs = []
        
        for doc in documents:
            doc_content = doc.get("content", "").lower()
            for term in search_terms:
                if term.lower() in doc_content:
                    relevant_docs.append(doc)
                    break
        
        if not relevant_docs:
            return {"success": False, "error": f"No relevant documents found for {field_id}"}
        
        # Extract value from most relevant document
        best_doc = relevant_docs[0]
        value = self._extract_value_from_document(field_id, best_doc, expert_knowledge)
        
        citation = {
            "field": field_id,
            "value": value,
            "source": best_doc.get("type", "Clinical Document"),
            "url": f"/ehr/document/{best_doc.get('doc_id', 'unknown')}",
            "timestamp": datetime.now().isoformat(),
            "document_date": best_doc.get("date", "")
        }
        
        return {
            "success": True,
            "data": {"value": value, "source": best_doc.get("type", "Clinical Document")},
            "citation": citation
        }
    
    def _extract_value_from_document(self, field_id: str, document: Dict, 
                                    expert_knowledge: Dict = None) -> str:
        """Extract specific value from document content"""
        content = document.get("content", "")
        
        # Use expert knowledge for extraction patterns if available
        if expert_knowledge and "extraction_patterns" in expert_knowledge:
            patterns = expert_knowledge["extraction_patterns"].get(field_id, [])
            for pattern in patterns:
                # Simple pattern matching - in real implementation, use regex or NLP
                if pattern["keyword"] in content.lower():
                    return pattern["extraction_method"]
        
        # Default extraction based on field type
        if field_id == "genetic_counseling":
            if "genetic counseling" in content.lower():
                return "Completed"
            elif "counseling" in content.lower():
                return "Completed"
            else:
                return "Not documented"
        
        elif field_id == "family_history":
            if "family history" in content.lower():
                return "Documented"
            else:
                return "No family history documented"
        
        # Return a summary of the document content
        return content[:100] + "..." if len(content) > 100 else content
    
    def _extract_computed_field(self, field_id: str, mapping: Dict, 
                               patient_data: Dict, patient_mrn: str) -> Dict:
        """Extract computed field based on multiple data sources"""
        if field_id == "clinical_indication":
            diagnosis = patient_data.get("diagnosis", "")
            stage = patient_data.get("stage", "")
            
            if diagnosis and stage:
                value = f"{diagnosis} - Stage {stage}"
            elif diagnosis:
                value = diagnosis
            else:
                value = "Clinical indication not documented"
            
            citation = {
                "field": field_id,
                "value": value,
                "source": "Computed from EHR data",
                "url": f"/ehr/patient/{patient_mrn}/computed/{field_id}",
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "data": {"value": value, "source": "Computed"},
                "citation": citation
            }
        
        return {"success": False, "error": f"Unknown computed field: {field_id}"}
    
    def validate_form_data(self, form_data: Dict, form_template: Dict) -> Dict:
        """Validate completed form data"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": []
        }
        
        for section in form_template["sections"]:
            section_data = form_data.get("patient_info", {}).get(section["id"], {})
            
            for field in section["fields"]:
                field_id = field["id"]
                field_value = section_data.get(field_id, {}).get("value", "")
                
                if field["required"] and not field_value:
                    validation_result["missing_required"].append({
                        "field_id": field_id,
                        "label": field["label"],
                        "section": section["title"]
                    })
                    validation_result["is_valid"] = False
        
        return validation_result
    
    def generate_form_preview(self, form_data: Dict, form_template: Dict) -> Dict:
        """Generate a preview of the completed form"""
        preview = {
            "form_name": form_template["name"],
            "sections": [],
            "summary": {
                "total_fields": 0,
                "completed_fields": 0,
                "required_fields": 0,
                "missing_required": 0
            }
        }
        
        for section in form_template["sections"]:
            section_preview = {
                "id": section["id"],
                "title": section["title"],
                "fields": []
            }
            
            section_data = form_data.get("patient_info", {}).get(section["id"], {})
            
            for field in section["fields"]:
                field_id = field["id"]
                field_data = section_data.get(field_id, {})
                
                field_preview = {
                    "id": field_id,
                    "label": field["label"],
                    "value": field_data.get("value", ""),
                    "source": field_data.get("source", ""),
                    "required": field["required"],
                    "is_completed": bool(field_data.get("value", ""))
                }
                
                section_preview["fields"].append(field_preview)
                
                preview["summary"]["total_fields"] += 1
                if field_preview["is_completed"]:
                    preview["summary"]["completed_fields"] += 1
                if field["required"]:
                    preview["summary"]["required_fields"] += 1
                    if not field_preview["is_completed"]:
                        preview["summary"]["missing_required"] += 1
            
            preview["sections"].append(section_preview)
        
        return preview
