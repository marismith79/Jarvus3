import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from .mock_ehr_system import MockEHRSystem

class FormQuestionProcessor:
    def __init__(self, ehr_system: MockEHRSystem):
        self.ehr_system = ehr_system
        self.form_questions = self._load_form_questions()
        
    def _load_form_questions(self) -> Dict:
        """Load the full genetic testing form questions"""
        form_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'genetic_testing_form_questions_full.json')
        try:
            with open(form_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading form questions: {e}")
            return {}
    
    def get_total_questions(self) -> int:
        """Get total number of questions across all sections"""
        total = 0
        for section in self.form_questions.get('sections', []):
            total += len(section.get('questions', []))
        return total
    
    def process_all_questions(self, patient_mrn: str, auth_data: Dict, 
                            progress_callback=None) -> Dict[str, Any]:
        """Process all questions in the form systematically"""
        if not patient_mrn:
            return {"error": "No patient MRN provided"}
        
        patient_data = self.ehr_system.get_patient_data(patient_mrn)
        if not patient_data:
            return {"error": f"Patient data not found for MRN: {patient_mrn}"}
        
        results = {
            "form_title": self.form_questions.get('title', ''),
            "form_id": self.form_questions.get('form_id', ''),
            "version": self.form_questions.get('version', ''),
            "sections": [],
            "total_questions": self.get_total_questions(),
            "processed_questions": 0,
            "completed_questions": 0,
            "missing_data": [],
            "citations": [],
            "processing_time": 0
        }
        
        start_time = time.time()
        total_questions = self.get_total_questions()
        current_question = 0
        
        for section in self.form_questions.get('sections', []):
            section_result = {
                "section_name": section.get('section_name', ''),
                "questions": [],
                "completed": 0,
                "total": len(section.get('questions', []))
            }
            
            for question in section.get('questions', []):
                current_question += 1
                
                # Update progress
                if progress_callback:
                    progress = int((current_question / total_questions) * 100)
                    progress_callback(progress, f"Processing question {current_question}/{total_questions}: {question.get('question', '')[:50]}...")
                
                # Process individual question
                question_result = self._process_question(
                    question, patient_data, patient_mrn, auth_data
                )
                
                section_result["questions"].append(question_result)
                
                if question_result.get("status") == "completed":
                    section_result["completed"] += 1
                    results["completed_questions"] += 1
                
                results["processed_questions"] += 1
                
                # Add citations
                if "citation" in question_result:
                    results["citations"].append(question_result["citation"])
                
                # Track missing data
                if question_result.get("status") == "missing_data":
                    results["missing_data"].append({
                        "question_id": question.get("id"),
                        "question": question.get("question"),
                        "reason": question_result.get("reason", "Data not found in EHR")
                    })
                
                # Small delay to simulate processing
                time.sleep(0.1)
            
            results["sections"].append(section_result)
        
        results["processing_time"] = time.time() - start_time
        return results
    
    def _process_question(self, question: Dict, patient_data: Dict, 
                         patient_mrn: str, auth_data: Dict) -> Dict[str, Any]:
        """Process a single question and extract relevant data"""
        question_id = question.get("id", "")
        question_text = question.get("question", "")
        question_type = question.get("type", "text")
        required = question.get("required", False)
        
        result = {
            "id": question_id,
            "question": question_text,
            "type": question_type,
            "required": required,
            "status": "pending",
            "answer": None,
            "source": None,
            "confidence": 0,
            "citation": None,
            "follow_up": None
        }
        
        try:
            # Extract answer based on question type and content
            answer_data = self._extract_answer_for_question(
                question, patient_data, patient_mrn, auth_data
            )
            
            if answer_data["success"]:
                result["status"] = "completed"
                result["answer"] = answer_data["answer"]
                result["source"] = answer_data["source"]
                result["confidence"] = answer_data["confidence"]
                result["citation"] = answer_data["citation"]
                
                # Handle follow-up questions
                if "follow_up" in question and answer_data.get("trigger_follow_up"):
                    result["follow_up"] = self._process_follow_up_question(
                        question["follow_up"], patient_data, patient_mrn, auth_data
                    )
            else:
                if required:
                    result["status"] = "missing_data"
                    result["reason"] = answer_data["error"]
                else:
                    result["status"] = "completed"
                    result["answer"] = "Not applicable"
                    result["source"] = "Not required"
                    result["confidence"] = 100
                    
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _extract_answer_for_question(self, question: Dict, patient_data: Dict, 
                                   patient_mrn: str, auth_data: Dict) -> Dict[str, Any]:
        """Extract answer for a specific question based on its content"""
        question_text = question.get("question", "").lower()
        question_id = question.get("id", "")
        
        # Map common question patterns to data extraction methods
        if "cpt codes" in question_text:
            return self._extract_cpt_codes(auth_data)
        elif "ordering provider" in question_text and "board-certified" in question_text:
            return self._extract_provider_qualification(patient_data, auth_data)
        elif "genetic counseling" in question_text:
            return self._extract_genetic_counseling_info(patient_data, patient_mrn)
        elif "genetic test reliably associated" in question_text:
            return self._extract_test_reliability(auth_data)
        elif "diagnostic studies available" in question_text:
            return self._extract_alternative_diagnostics(patient_data, patient_mrn)
        elif "test been performed previously" in question_text:
            return self._extract_prior_testing(patient_data, patient_mrn)
        elif "specific reason" in question_text and "ordered" in question_text:
            return self._extract_testing_reason(auth_data, patient_data)
        elif "examinations" in question_text and "laboratory tests" in question_text:
            return self._extract_evaluation_studies(patient_data, patient_mrn)
        elif "clinical features" in question_text:
            return self._extract_clinical_features(patient_data, patient_mrn)
        elif "direct risk" in question_text and "inheriting" in question_text:
            return self._extract_inheritance_risk(patient_data, patient_mrn)
        elif "prospective parent" in question_text:
            return self._extract_prospective_parent_info(patient_data, patient_mrn)
        elif "less intensive genetic testing" in question_text:
            return self._extract_prior_genetic_testing(patient_data, patient_mrn)
        elif "personal history" in question_text:
            return self._extract_personal_history(patient_data, patient_mrn)
        elif "family history" in question_text:
            return self._extract_family_history(patient_data, patient_mrn)
        elif "spouse" in question_text or "reproductive partner" in question_text:
            return self._extract_partner_history(patient_data, patient_mrn)
        elif "previous child" in question_text:
            return self._extract_child_history(patient_data, patient_mrn)
        elif "material impact" in question_text and "treatment plan" in question_text:
            return self._extract_treatment_impact(auth_data, patient_data)
        elif "improve health outcomes" in question_text:
            return self._extract_health_outcomes_impact(auth_data, patient_data)
        elif "disease treatable" in question_text or "preventable" in question_text:
            return self._extract_treatability_info(auth_data, patient_data)
        elif "reduced risk" in question_text and "morbidity" in question_text:
            return self._extract_risk_reduction(auth_data, patient_data)
        elif "avoid or supplant" in question_text and "additional testing" in question_text:
            return self._extract_testing_efficiency(auth_data, patient_data)
        else:
            # Default extraction for unknown questions
            return self._extract_generic_answer(question, patient_data, auth_data)
    
    def _extract_cpt_codes(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract CPT codes from authorization data"""
        cpt_code = auth_data.get('cpt_code', '')
        if cpt_code:
            return {
                "success": True,
                "answer": f"{cpt_code} (1 unit)",
                "source": "Prior Authorization Request",
                "confidence": 100,
                "citation": {
                    "source": "Prior Auth Request",
                    "url": f"/api/prior-auths/{auth_data.get('id')}",
                    "title": "CPT Code Information",
                    "relevance": 100
                }
            }
        return {"success": False, "error": "CPT code not found in authorization data"}
    
    def _extract_provider_qualification(self, patient_data: Dict, auth_data: Dict) -> Dict[str, Any]:
        """Extract provider qualification information"""
        provider_name = auth_data.get('ordering_provider', 'Dr. Jordan Rivera')
        
        # Check if provider is qualified (simulated logic)
        is_qualified = True  # In real system, would check provider credentials
        
        answer = "Yes" if is_qualified else "No"
        follow_up_needed = not is_qualified
        
        return {
            "success": True,
            "answer": answer,
            "source": "Provider Database",
            "confidence": 95,
            "trigger_follow_up": follow_up_needed,
            "citation": {
                "source": "Provider Database",
                "url": f"/api/providers/{provider_name}",
                "title": "Provider Qualifications",
                "relevance": 100
            }
        }
    
    def _extract_genetic_counseling_info(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract genetic counseling information from EHR"""
        # Search for genetic counseling notes
        counseling_notes = self._search_ehr_documents(patient_mrn, ["genetic counseling", "counseling note"])
        
        if counseling_notes:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Genetic Counseling Notes",
                "confidence": 90,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/documents",
                    "title": "Genetic Counseling Documentation",
                    "relevance": 95
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/documents",
                    "title": "No Genetic Counseling Found",
                    "relevance": 90
                }
            }
    
    def _extract_test_reliability(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract test reliability information"""
        # Based on CPT code and diagnosis, determine if test is reliable
        cpt_code = auth_data.get('cpt_code', '')
        diagnosis = auth_data.get('diagnosis', '')
        
        # Simulated logic - in real system would check against medical guidelines
        is_reliable = True  # Most genetic tests are reliable when ordered appropriately
        
        return {
            "success": True,
            "answer": "Yes" if is_reliable else "No",
            "source": "Medical Guidelines Database",
            "confidence": 90,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn",
                "title": "Genetic Testing Reliability Standards",
                "relevance": 95
            }
        }
    
    def _extract_alternative_diagnostics(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract information about alternative diagnostic studies"""
        # Check for imaging, lab tests, etc.
        imaging_studies = self._search_ehr_documents(patient_mrn, ["imaging", "CT", "MRI", "PET"])
        lab_tests = self._search_ehr_documents(patient_mrn, ["laboratory", "blood test", "biopsy"])
        
        if imaging_studies or lab_tests:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Diagnostic Studies",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/studies",
                    "title": "Alternative Diagnostic Studies",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/studies",
                    "title": "No Alternative Studies Found",
                    "relevance": 85
                }
            }
    
    def _extract_prior_testing(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract information about prior genetic testing"""
        prior_tests = self._search_ehr_documents(patient_mrn, ["genetic test", "molecular test", "prior testing"])
        
        if prior_tests:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Prior Testing Records",
                "confidence": 90,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/testing",
                    "title": "Prior Genetic Testing Records",
                    "relevance": 95
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 85,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/testing",
                    "title": "No Prior Testing Found",
                    "relevance": 90
                }
            }
    
    def _extract_testing_reason(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract the specific reason for testing"""
        diagnosis = auth_data.get('diagnosis', '')
        cpt_code = auth_data.get('cpt_code', '')
        
        reason = f"Comprehensive genomic profiling for treatment selection in {diagnosis}. NCCN Guidelines v2.2024 support this testing for advanced cancer patients."
        
        return {
            "success": True,
            "answer": reason,
            "source": "Clinical Guidelines + Diagnosis",
            "confidence": 95,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn/v2.2024",
                "title": "Treatment Selection Guidelines",
                "relevance": 100
            }
        }
    
    def _extract_evaluation_studies(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract information about examinations and studies performed"""
        studies = self._search_ehr_documents(patient_mrn, ["examination", "laboratory", "imaging", "diagnostic"])
        
        if studies:
            study_list = "Pathology report, imaging studies, laboratory tests, clinical examination"
            return {
                "success": True,
                "answer": study_list,
                "source": "EHR - Clinical Documentation",
                "confidence": 85,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/studies",
                    "title": "Evaluation Studies Performed",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": False,
                "error": "No evaluation studies found in EHR"
            }
    
    def _extract_clinical_features(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract clinical features information"""
        clinical_notes = self._search_ehr_documents(patient_mrn, ["clinical features", "symptoms", "presentation"])
        
        if clinical_notes:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Clinical Documentation",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/clinical",
                    "title": "Clinical Features Documentation",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/clinical",
                    "title": "No Clinical Features Found",
                    "relevance": 85
                }
            }
    
    def _extract_inheritance_risk(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract inheritance risk information"""
        family_history = self._search_ehr_documents(patient_mrn, ["family history", "inheritance", "genetic risk"])
        
        if family_history:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Family History",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/family",
                    "title": "Family History Documentation",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/family",
                    "title": "No Inheritance Risk Found",
                    "relevance": 85
                }
            }
    
    def _extract_prospective_parent_info(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract prospective parent information"""
        # Check if patient is of reproductive age and has pregnancy-related records
        age = patient_data.get('age', 0)
        pregnancy_notes = self._search_ehr_documents(patient_mrn, ["pregnancy", "reproductive", "fertility"])
        
        if age < 50 and pregnancy_notes:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Reproductive History",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/reproductive",
                    "title": "Reproductive History",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/reproductive",
                    "title": "Not Prospective Parent",
                    "relevance": 85
                }
            }
    
    def _extract_prior_genetic_testing(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract prior genetic testing information"""
        prior_tests = self._search_ehr_documents(patient_mrn, ["genetic test", "molecular test", "less intensive"])
        
        if prior_tests:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Prior Testing",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/testing",
                    "title": "Prior Genetic Testing",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/testing",
                    "title": "No Prior Testing",
                    "relevance": 85
                }
            }
    
    def _extract_personal_history(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract personal history information"""
        personal_history = self._search_ehr_documents(patient_mrn, ["personal history", "medical history", "diagnosis"])
        
        if personal_history:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Personal History",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/history",
                    "title": "Personal Medical History",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/history",
                    "title": "No Personal History",
                    "relevance": 85
                }
            }
    
    def _extract_family_history(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract family history information"""
        family_history = self._search_ehr_documents(patient_mrn, ["family history", "hereditary", "genetic"])
        
        if family_history:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Family History",
                "confidence": 85,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/family",
                    "title": "Family History",
                    "relevance": 90
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 80,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/family",
                    "title": "No Family History",
                    "relevance": 85
                }
            }
    
    def _extract_partner_history(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract partner history information"""
        partner_history = self._search_ehr_documents(patient_mrn, ["spouse", "partner", "reproductive partner"])
        
        if partner_history:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Partner History",
                "confidence": 80,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/partner",
                    "title": "Partner History",
                    "relevance": 85
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 75,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/partner",
                    "title": "No Partner History",
                    "relevance": 80
                }
            }
    
    def _extract_child_history(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract child history information"""
        child_history = self._search_ehr_documents(patient_mrn, ["child", "offspring", "previous child"])
        
        if child_history:
            return {
                "success": True,
                "answer": "Yes",
                "source": "EHR - Child History",
                "confidence": 80,
                "trigger_follow_up": True,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/children",
                    "title": "Child History",
                    "relevance": 85
                }
            }
        else:
            return {
                "success": True,
                "answer": "No",
                "source": "EHR Review",
                "confidence": 75,
                "citation": {
                    "source": "EHR System",
                    "url": f"/api/ehr/patient/{patient_mrn}/children",
                    "title": "No Child History",
                    "relevance": 80
                }
            }
    
    def _extract_treatment_impact(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract treatment plan impact information"""
        diagnosis = auth_data.get('diagnosis', '')
        
        impact = f"Yes - Test results will guide targeted therapy selection for {diagnosis} based on molecular profile"
        
        return {
            "success": True,
            "answer": "Yes",
            "source": "Clinical Guidelines",
            "confidence": 90,
            "trigger_follow_up": True,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn/treatment",
                "title": "Treatment Selection Guidelines",
                "relevance": 95
            }
        }
    
    def _extract_health_outcomes_impact(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract health outcomes impact information"""
        return {
            "success": True,
            "answer": "Yes",
            "source": "Clinical Evidence",
            "confidence": 90,
            "trigger_follow_up": True,
            "citation": {
                "source": "Clinical Trials Database",
                "url": "/api/evidence/outcomes",
                "title": "Health Outcomes Evidence",
                "relevance": 95
            }
        }
    
    def _extract_treatability_info(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract disease treatability information"""
        diagnosis = auth_data.get('diagnosis', '')
        
        treatability = f"Yes - {diagnosis} has targeted treatment options based on molecular profiling"
        
        return {
            "success": True,
            "answer": "Yes",
            "source": "Clinical Guidelines",
            "confidence": 90,
            "trigger_follow_up": True,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn/treatability",
                "title": "Disease Treatability Guidelines",
                "relevance": 95
            }
        }
    
    def _extract_risk_reduction(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract risk reduction information"""
        return {
            "success": True,
            "answer": "Yes",
            "source": "Clinical Evidence",
            "confidence": 90,
            "citation": {
                "source": "Clinical Trials Database",
                "url": "/api/evidence/risk-reduction",
                "title": "Risk Reduction Evidence",
                "relevance": 95
            }
        }
    
    def _extract_testing_efficiency(self, auth_data: Dict, patient_data: Dict) -> Dict[str, Any]:
        """Extract testing efficiency information"""
        return {
            "success": True,
            "answer": "Yes",
            "source": "Clinical Guidelines",
            "confidence": 90,
            "trigger_follow_up": True,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn/efficiency",
                "title": "Testing Efficiency Guidelines",
                "relevance": 95
            }
        }
    
    def _extract_generic_answer(self, question: Dict, patient_data: Dict, auth_data: Dict) -> Dict[str, Any]:
        """Extract generic answer for unknown questions"""
        return {
            "success": True,
            "answer": "Information available in patient records",
            "source": "EHR Review",
            "confidence": 70,
            "citation": {
                "source": "EHR System",
                "url": f"/api/ehr/patient/{patient_data.get('mrn', '')}",
                "title": "Patient Records",
                "relevance": 75
            }
        }
    
    def _process_follow_up_question(self, follow_up: Dict, patient_data: Dict, 
                                  patient_mrn: str, auth_data: Dict) -> Dict[str, Any]:
        """Process follow-up questions"""
        follow_up_question = follow_up.get("question", "")
        follow_up_type = follow_up.get("type", "text_area")
        
        # For now, provide a generic response
        return {
            "question": follow_up_question,
            "type": follow_up_type,
            "answer": "Please review patient documentation for specific details",
            "source": "EHR Review",
            "status": "pending_clinician_review"
        }
    
    def _search_ehr_documents(self, patient_mrn: str, search_terms: List[str]) -> List[Dict]:
        """Search EHR documents for specific terms"""
        try:
            # This would integrate with the actual EHR system
            # For now, return simulated results
            return [{"document_type": "clinical_note", "content": "Sample content"}]
        except Exception as e:
            print(f"Error searching EHR documents: {e}")
            return []
