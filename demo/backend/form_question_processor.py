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
            for question in section.get('questions', []):
                # Handle nested provider information structure
                if question.get('subsection') and question.get('fields'):
                    total += len(question.get('fields', []))
                else:
                    total += 1
                    # Add potential follow-up questions
                    if question.get('follow_up'):
                        total += 1
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
            # Calculate total questions in this section (including nested fields and follow-ups)
            section_total = 0
            for question in section.get('questions', []):
                if question.get('subsection') and question.get('fields'):
                    section_total += len(question.get('fields', []))
                else:
                    section_total += 1
                    # Add potential follow-up questions
                    if question.get('follow_up'):
                        section_total += 1
            
            section_result = {
                "section_name": section.get('section_name', ''),
                "questions": [],
                "completed": 0,
                "total": section_total
            }
            
            for question in section.get('questions', []):
                # Handle nested provider information structure
                if question.get('subsection') and question.get('fields'):
                    # Process each field in the subsection
                    for field in question.get('fields', []):
                        current_question += 1
                        
                        # Update progress
                        if progress_callback:
                            progress = int((current_question / total_questions) * 100)
                            progress_callback(progress, f"Processing field {current_question}/{total_questions}: {field.get('label', '')[:50]}...")
                        
                        # Create a question-like structure for the field
                        field_question = {
                            "id": field.get("id"),
                            "question": field.get("label"),
                            "type": field.get("type", "text"),
                            "required": field.get("required", False)
                        }
                        
                        # Process individual field
                        field_result = self._process_question(
                            field_question, patient_data, patient_mrn, auth_data
                        )
                        
                        section_result["questions"].append(field_result)
                        
                        if field_result.get("status") == "completed":
                            section_result["completed"] += 1
                            results["completed_questions"] += 1
                        
                        results["processed_questions"] += 1
                        
                        # Add citations
                        if "citation" in field_result:
                            results["citations"].append(field_result["citation"])
                        
                        # Track missing data
                        if field_result.get("status") == "missing_data":
                            results["missing_data"].append({
                                "question_id": field.get("id"),
                                "question": field.get("label"),
                                "reason": field_result.get("reason", "Data not found in EHR")
                            })
                        
                        # Small delay to simulate processing
                        time.sleep(0.1)
                else:
                    # Process regular question
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
                    
                    # Process follow-up questions if they exist and condition is met
                    if question_result.get("follow_up"):
                        current_question += 1
                        
                        # Update progress
                        if progress_callback:
                            progress = int((current_question / total_questions) * 100)
                            progress_callback(progress, f"Processing follow-up question {current_question}/{total_questions}: {question_result['follow_up'].get('question', '')[:50]}...")
                        
                        # Create follow-up question structure
                        follow_up_question = {
                            "id": f"{question.get('id')}_followup",
                            "question": question_result["follow_up"]["question"],
                            "type": question_result["follow_up"]["type"],
                            "required": False,
                            "is_follow_up": True,
                            "parent_question_id": question.get("id")
                        }
                        
                        # Process follow-up question
                        follow_up_result = self._process_question(
                            follow_up_question, patient_data, patient_mrn, auth_data
                        )
                        
                        section_result["questions"].append(follow_up_result)
                        
                        if follow_up_result.get("status") == "completed":
                            section_result["completed"] += 1
                            results["completed_questions"] += 1
                        
                        results["processed_questions"] += 1
                        
                        # Add citations
                        if "citation" in follow_up_result:
                            results["citations"].append(follow_up_result["citation"])
                        
                        # Track missing data
                        if follow_up_result.get("status") == "missing_data":
                            results["missing_data"].append({
                                "question_id": follow_up_question.get("id"),
                                "question": follow_up_question.get("question"),
                                "reason": follow_up_result.get("reason", "Data not found in EHR")
                            })
                        
                        # Small delay to simulate processing
                        time.sleep(0.1)
                    
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
            # Handle statement type questions differently
            if question_type == "statement":
                result["status"] = "completed"
                result["answer"] = "Statement displayed"
                result["source"] = "Form Information"
                result["confidence"] = 100
                result["is_statement"] = True
                return result
            
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
                if "follow_up" in question:
                    follow_up_condition = question["follow_up"].get("condition")
                    answer_value = answer_data.get("answer")
                    if follow_up_condition and answer_value == follow_up_condition:
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
        
        # Debug specific questions
        if question_id in ['h2', 'h3']:
            print(f"DEBUG: Processing question {question_id}: '{question_text}'")
        
        # Map common question patterns to data extraction methods
        # Handle provider information fields by ID
        if question_id.startswith('billing_') or question_id.startswith('ordering_'):
            return self._extract_provider_info(question_id, auth_data)
        # Handle member information fields by ID
        elif question_id.startswith('mi'):
            return self._extract_member_info(question_id, patient_data, auth_data)
        # Handle certification fields by ID
        elif question_id in ['physician_signature', 'signature_date']:
            return self._extract_certification_info(question_id, auth_data)
        # Handle follow-up questions
        elif question_id.endswith('_followup'):
            return self._extract_follow_up_answer(question, patient_data, patient_mrn, auth_data)
        elif "test name" in question_text:
            return self._extract_test_name(auth_data)
        elif "date of service" in question_text:
            return self._extract_date_of_service(auth_data)
        elif "type of test" in question_text:
            return self._extract_test_type(auth_data)
        elif "gene mutation" in question_text:
            return self._extract_gene_mutation(auth_data)
        elif "icd-10" in question_text or "diagnosis" in question_text:
            return self._extract_diagnosis_codes(auth_data)
        elif "cpt codes" in question_text:
            return self._extract_cpt_codes(auth_data)
        elif "testing being ordered by" in question_text and "physician" in question_text:
            return self._extract_provider_qualification(patient_data, auth_data)
        elif "genetic counseling" in question_text:
            return self._extract_genetic_counseling_info(patient_data, patient_mrn)
        elif "mutation" in question_text and "reliably associated" in question_text:
            return self._extract_test_reliability(auth_data)
        elif "genetic disorder" in question_text and "diagnosed" in question_text:
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
    
    def _extract_test_name(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract test name from authorization data"""
        service_type = auth_data.get('service_type', 'Comprehensive Genomic Profiling')
        return {
            "success": True,
            "answer": service_type,
            "source": "Prior Authorization Request",
            "confidence": 100,
            "citation": {
                "source": "Prior Auth Request",
                "url": f"/api/prior-auths/{auth_data.get('id')}",
                "title": "Test Name Information",
                "relevance": 100
            }
        }
    
    def _extract_date_of_service(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract date of service from authorization data"""
        from datetime import datetime
        date_of_service = auth_data.get('date_of_service', datetime.now().strftime('%Y-%m-%d'))
        return {
            "success": True,
            "answer": date_of_service,
            "source": "Prior Authorization Request",
            "confidence": 100,
            "citation": {
                "source": "Prior Auth Request",
                "url": f"/api/prior-auths/{auth_data.get('id')}",
                "title": "Date of Service",
                "relevance": 100
            }
        }
    
    def _extract_test_type(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract test type from authorization data"""
        service_type = auth_data.get('service_type', 'Comprehensive Genomic Profiling')
        if 'comprehensive' in service_type.lower():
            test_type = "Gene panel (comprehensive genomic profiling)"
        else:
            test_type = "Gene panel"
        
        return {
            "success": True,
            "answer": test_type,
            "source": "Prior Authorization Request",
            "confidence": 95,
            "citation": {
                "source": "Prior Auth Request",
                "url": f"/api/prior-auths/{auth_data.get('id')}",
                "title": "Test Type Information",
                "relevance": 95
            }
        }
    
    def _extract_gene_mutation(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract gene mutation information from authorization data"""
        diagnosis = auth_data.get('diagnosis', 'Advanced Cancer')
        if 'cancer' in diagnosis.lower():
            gene_mutation = "Multiple genes for comprehensive genomic profiling"
        else:
            gene_mutation = "Specific gene mutations based on clinical presentation"
        
        return {
            "success": True,
            "answer": gene_mutation,
            "source": "Clinical Guidelines",
            "confidence": 90,
            "citation": {
                "source": "NCCN Guidelines",
                "url": "/api/guidelines/nccn/genes",
                "title": "Gene Mutation Guidelines",
                "relevance": 90
            }
        }
    
    def _extract_diagnosis_codes(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract diagnosis codes from authorization data"""
        diagnosis = auth_data.get('diagnosis', 'Advanced Cancer')
        # Map common diagnoses to ICD-10 codes
        diagnosis_codes = {
            'advanced cancer': 'C79.9',
            'lung cancer': 'C34.90',
            'breast cancer': 'C50.919',
            'colorectal cancer': 'C18.9',
            'melanoma': 'C43.9'
        }
        
        icd_code = diagnosis_codes.get(diagnosis.lower(), 'C79.9')
        
        return {
            "success": True,
            "answer": icd_code,
            "source": "ICD-10 Database",
            "confidence": 95,
            "citation": {
                "source": "ICD-10 Database",
                "url": f"/api/icd10/{icd_code}",
                "title": "Diagnosis Code Information",
                "relevance": 95
            }
        }
    
    def _extract_follow_up_answer(self, question: Dict, patient_data: Dict, patient_mrn: str, auth_data: Dict) -> Dict[str, Any]:
        """Extract answer for follow-up questions"""
        question_text = question.get("question", "").lower()
        parent_question_id = question.get("parent_question_id", "")
        
        # Map follow-up questions to appropriate extraction methods
        if "explain" in question_text and "no" in question_text:
            if "genetic counseling" in question_text or "counseling" in question_text:
                return {
                    "success": True,
                    "answer": "Genetic counseling will be scheduled prior to testing as per clinical guidelines.",
                    "source": "Clinical Guidelines",
                    "confidence": 90,
                    "citation": {
                        "source": "NCCN Guidelines",
                        "url": "/api/guidelines/nccn/counseling",
                        "title": "Genetic Counseling Requirements",
                        "relevance": 95
                    }
                }
            elif "physician" in question_text or "provider" in question_text:
                return {
                    "success": True,
                    "answer": "Provider has appropriate training and certification for genetic testing ordering.",
                    "source": "Provider Database",
                    "confidence": 95,
                    "citation": {
                        "source": "Provider Database",
                        "url": f"/api/providers/{auth_data.get('ordering_provider', '')}",
                        "title": "Provider Qualifications",
                        "relevance": 100
                    }
                }
        elif "describe" in question_text and "yes" in question_text:
            if "diagnosed" in question_text or "diagnostic" in question_text:
                return {
                    "success": True,
                    "answer": "Clinical examination, imaging studies, and laboratory tests have been performed but genetic testing is still required for definitive diagnosis and treatment planning.",
                    "source": "EHR Review",
                    "confidence": 85,
                    "citation": {
                        "source": "EHR System",
                        "url": f"/api/ehr/patient/{patient_mrn}/studies",
                        "title": "Alternative Diagnostic Studies",
                        "relevance": 90
                    }
                }
        elif "explain why repeat testing" in question_text:
            return {
                "success": True,
                "answer": "Repeat testing is medically necessary due to new clinical findings, progression of disease, or need for updated molecular profiling for treatment selection.",
                "source": "Clinical Documentation",
                "confidence": 90,
                "citation": {
                    "source": "Clinical Guidelines",
                    "url": "/api/guidelines/nccn/repeat-testing",
                    "title": "Repeat Testing Guidelines",
                    "relevance": 95
                }
            }
        
        # Default follow-up answer
        return {
            "success": True,
            "answer": "Additional information available in patient documentation and clinical records.",
            "source": "EHR Review",
            "confidence": 80,
            "citation": {
                "source": "EHR System",
                "url": f"/api/ehr/patient/{patient_mrn}",
                "title": "Patient Documentation",
                "relevance": 85
            }
        }
    
    def _extract_certification_info(self, field_id: str, auth_data: Dict) -> Dict[str, Any]:
        """Extract certification information"""
        from datetime import datetime
        
        certification_data = {
            'physician_signature': 'Dr. Jordan Rivera',
            'signature_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        answer = certification_data.get(field_id, 'Certification pending')
        
        return {
            "success": True,
            "answer": answer,
            "source": "Provider Information",
            "confidence": 100,
            "citation": {
                "source": "Provider Database",
                "url": f"/api/providers/certification",
                "title": "Provider Certification",
                "relevance": 100
            }
        }
    
    def _extract_member_info(self, field_id: str, patient_data: Dict, auth_data: Dict) -> Dict[str, Any]:
        """Extract member information from patient data"""
        member_data = {
            'mi1': auth_data.get('patient_mrn', 'MRN123456'),
            'mi2': patient_data.get('dob', '1985-03-15'),
            'mi3': patient_data.get('name', 'Smith, John'),
            'mi4': patient_data.get('address', '789 Patient Street'),
            'mi5': patient_data.get('city_state_zip', 'Hartford, CT 06103')
        }
        
        answer = member_data.get(field_id, 'Member information available')
        
        return {
            "success": True,
            "answer": answer,
            "source": "Patient Records",
            "confidence": 100,
            "citation": {
                "source": "EHR System",
                "url": f"/api/patients/{auth_data.get('patient_mrn', '')}",
                "title": "Patient Information",
                "relevance": 100
            }
        }
    
    def _extract_provider_info(self, field_id: str, auth_data: Dict) -> Dict[str, Any]:
        """Extract provider information from authorization data"""
        # Mock provider information - in real system would come from provider database
        provider_data = {
            'billing_medicaid': '123456789',
            'billing_name': 'Advanced Genetics Testing Center',
            'billing_address': '123 Medical Drive',
            'billing_city_state_zip': 'Hartford, CT 06101',
            'billing_phone': '(860) 555-0123',
            'billing_fax': '(860) 555-0124',
            'billing_contact': 'Sarah Johnson',
            'ordering_medicaid': '987654321',
            'ordering_name': auth_data.get('ordering_provider', 'Dr. Jordan Rivera'),
            'ordering_address': '456 Healthcare Blvd',
            'ordering_city_state_zip': 'New Haven, CT 06511',
            'ordering_phone': '(203) 555-0567',
            'ordering_fax': '(203) 555-0568',
            'ordering_contact': 'Dr. Jordan Rivera'
        }
        
        answer = provider_data.get(field_id, 'Provider information available')
        
        return {
            "success": True,
            "answer": answer,
            "source": "Provider Database",
            "confidence": 95,
            "citation": {
                "source": "Provider Database",
                "url": f"/api/providers/{field_id}",
                "title": "Provider Information",
                "relevance": 95
            }
        }
    
    def _extract_cpt_codes(self, auth_data: Dict) -> Dict[str, Any]:
        """Extract CPT codes from authorization data"""
        # Get the main CPT code from auth data
        main_cpt_code = auth_data.get('cpt_code', '')
        
        if main_cpt_code:
            # Return as simple text format
            answer = f"{main_cpt_code} (1 unit)"
            
            return {
                "success": True,
                "answer": answer,
                "source": "Prior Authorization Request",
                "confidence": 95,
                "citation": {
                    "source": "Prior Auth Request",
                    "url": f"/api/prior-auths/{auth_data.get('id')}",
                    "title": "CPT Code Information",
                    "relevance": 100
                }
            }
        return {"success": False, "error": "CPT codes not found in authorization data"}
    
    def _extract_provider_qualification(self, patient_data: Dict, auth_data: Dict) -> Dict[str, Any]:
        """Extract provider qualification information"""
        provider_name = auth_data.get('ordering_provider', 'Dr. Jordan Rivera')
        
        # Check if provider is qualified (simulated logic)
        is_qualified = True  # In real system, would check provider credentials
        
        answer = "Yes" if is_qualified else "No"
        
        return {
            "success": True,
            "answer": answer,
            "source": "Provider Database",
            "confidence": 95,
            "citation": {
                "source": "Provider Database",
                "url": f"/api/providers/{provider_name}",
                "title": "Provider Qualifications",
                "relevance": 100
            }
        }
    
    def _extract_genetic_counseling_info(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract genetic counseling information from EHR"""
        # For now, return "Yes" to avoid triggering follow-up (more realistic)
        # In real system, would check for actual genetic counseling documentation
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
        print("DEBUG: _extract_personal_history called")
        # For now, return "Yes" to ensure follow-up questions appear
        return {
            "success": True,
            "answer": "Yes",
            "source": "EHR - Personal History",
            "confidence": 85,
            "citation": {
                "source": "EHR System",
                "url": f"/api/ehr/patient/{patient_mrn}/history",
                "title": "Personal Medical History",
                "relevance": 90
            }
        }
    
    def _extract_family_history(self, patient_data: Dict, patient_mrn: str) -> Dict[str, Any]:
        """Extract family history information"""
        print("DEBUG: _extract_family_history called")
        # For now, return "Yes" to ensure follow-up questions appear
        return {
            "success": True,
            "answer": "Yes",
            "source": "EHR - Family History",
            "confidence": 85,
            "citation": {
                "source": "EHR System",
                "url": f"/api/ehr/patient/{patient_mrn}/family",
                "title": "Family History",
                "relevance": 90
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
