import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from .form_manager import FormManager
from .mock_ehr_system import MockEHRSystem

class InteractiveFormEditor:
    def __init__(self, form_manager: FormManager, ehr_system: MockEHRSystem):
        self.form_manager = form_manager
        self.ehr_system = ehr_system
        self.active_sessions = {}  # Store active form editing sessions
        self.expert_feedback = {}  # Store expert feedback and guidance
        
    def create_form_session(self, auth_id: int, patient_mrn: str, 
                           insurance_provider: str, cpt_code: str,
                           coverage_analysis: Dict = None) -> Dict:
        """Create a new interactive form editing session"""
        session_id = str(uuid.uuid4())
        
        # Get form template
        form_template = self.form_manager.get_form_template(insurance_provider, cpt_code)
        
        # Extract initial EHR data
        expert_knowledge = self._get_expert_knowledge_for_case(auth_id, cpt_code, insurance_provider)
        extracted_data = self.form_manager.extract_ehr_data_for_form(
            patient_mrn, form_template, expert_knowledge
        )
        
        # Create session
        session = {
            "session_id": session_id,
            "auth_id": auth_id,
            "patient_mrn": patient_mrn,
            "insurance_provider": insurance_provider,
            "cpt_code": cpt_code,
            "form_template": form_template,
            "form_data": extracted_data,
            "coverage_analysis": coverage_analysis,
            "expert_knowledge": expert_knowledge,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "status": "active",
            "validation_errors": [],
            "human_edits": [],
            "expert_requests": [],
            "auto_suggestions": []
        }
        
        # Generate auto-suggestions based on coverage analysis
        if coverage_analysis:
            session["auto_suggestions"] = self._generate_auto_suggestions(
                session, coverage_analysis
            )
        
        self.active_sessions[session_id] = session
        return session
    
    def _get_expert_knowledge_for_case(self, auth_id: int, cpt_code: str, 
                                      insurance_provider: str) -> Dict:
        """Get expert knowledge relevant to this specific case"""
        # In a real implementation, this would query the agent setup database
        # For now, return mock expert knowledge
        return {
            "document_search_strategies": {
                "genetic_counseling": {
                    "additional_terms": ["genetic counselor", "counseling session", "pre-test counseling"],
                    "priority_documents": ["Genetic Counseling Note", "Oncology Consultation"]
                },
                "family_history": {
                    "additional_terms": ["family cancer", "inherited", "hereditary"],
                    "priority_documents": ["Family History Assessment", "Genetic Risk Assessment"]
                }
            },
            "extraction_patterns": {
                "genetic_counseling": [
                    {
                        "keyword": "genetic counseling completed",
                        "extraction_method": "Completed"
                    },
                    {
                        "keyword": "counseling session",
                        "extraction_method": "Completed"
                    }
                ],
                "family_history": [
                    {
                        "keyword": "family history positive",
                        "extraction_method": "Positive family history documented"
                    }
                ]
            },
            "field_validation_rules": {
                "clinical_indication": {
                    "required_for_cpt": ["81445", "81450"],
                    "validation_pattern": ".*cancer.*stage.*"
                }
            }
        }
    
    def _generate_auto_suggestions(self, session: Dict, coverage_analysis: Dict) -> List[Dict]:
        """Generate auto-suggestions based on coverage analysis"""
        suggestions = []
        
        # Check for missing required fields
        missing_fields = session["form_data"].get("missing_fields", [])
        for field in missing_fields:
            suggestions.append({
                "type": "missing_field",
                "field_id": field["field_id"],
                "label": field["label"],
                "message": f"Required field '{field['label']}' is missing: {field['reason']}",
                "action": "request_clinician_input",
                "priority": "high"
            })
        
        # Check coverage requirements
        if coverage_analysis and "requirements" in coverage_analysis:
            for req in coverage_analysis["requirements"]:
                req_type = req.get("requirement_type", "").lower()
                if "genetic counseling" in req_type:
                    suggestions.append({
                        "type": "coverage_requirement",
                        "field_id": "genetic_counseling",
                        "message": f"Coverage requires: {req.get('description', '')}",
                        "action": "ensure_documentation",
                        "priority": "medium"
                    })
        
        return suggestions
    
    def update_form_field(self, session_id: str, section_id: str, field_id: str, 
                         value: str, source: str = "human_edit") -> Dict:
        """Update a specific form field"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Update the field value
        if "patient_info" not in session["form_data"]:
            session["form_data"]["patient_info"] = {}
        if section_id not in session["form_data"]["patient_info"]:
            session["form_data"]["patient_info"][section_id] = {}
        
        session["form_data"]["patient_info"][section_id][field_id] = {
            "value": value,
            "source": source,
            "last_modified": datetime.now().isoformat()
        }
        
        # Record human edit
        session["human_edits"].append({
            "field_id": field_id,
            "section_id": section_id,
            "old_value": "",  # Would track previous value in real implementation
            "new_value": value,
            "timestamp": datetime.now().isoformat(),
            "source": source
        })
        
        session["last_modified"] = datetime.now().isoformat()
        
        # Re-validate form
        validation_result = self.form_manager.validate_form_data(
            session["form_data"], session["form_template"]
        )
        session["validation_errors"] = validation_result.get("errors", [])
        
        return {
            "success": True,
            "field_updated": True,
            "validation_result": validation_result,
            "session_status": self._get_session_status(session)
        }
    
    def request_expert_help(self, session_id: str, field_id: str, 
                           question: str, context: Dict = None) -> Dict:
        """Request help from human expert for a specific field"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        request_id = str(uuid.uuid4())
        expert_request = {
            "request_id": request_id,
            "field_id": field_id,
            "question": question,
            "context": context or {},
            "session_id": session_id,
            "auth_id": session["auth_id"],
            "patient_mrn": session["patient_mrn"],
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "expert_response": None
        }
        
        session["expert_requests"].append(expert_request)
        
        # In a real implementation, this would notify human experts
        # For now, simulate expert response
        self._simulate_expert_response(request_id, field_id, question)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Expert help requested successfully"
        }
    
    def _simulate_expert_response(self, request_id: str, field_id: str, question: str):
        """Simulate expert response for demo purposes"""
        # In real implementation, this would be handled by human experts
        expert_responses = {
            "genetic_counseling": {
                "response": "Check the 'Genetic Counseling Note' document in the patient's chart. If not found, request a genetic counseling consultation.",
                "action": "search_documents",
                "search_terms": ["genetic counseling", "counseling note"],
                "fallback_action": "request_clinician_input"
            },
            "family_history": {
                "response": "Look for 'Family History Assessment' or check oncology consultation notes for family history documentation.",
                "action": "search_documents",
                "search_terms": ["family history", "hereditary"],
                "fallback_action": "skip_field"
            },
            "clinical_indication": {
                "response": "Use the diagnosis and stage from pathology report to create clinical indication.",
                "action": "computed_field",
                "computation": "diagnosis + stage",
                "fallback_action": "use_diagnosis_only"
            }
        }
        
        # Find the request and update it
        for session in self.active_sessions.values():
            for request in session["expert_requests"]:
                if request["request_id"] == request_id:
                    request["status"] = "completed"
                    request["expert_response"] = expert_responses.get(
                        field_id, 
                        {"response": "Please review the patient's clinical documentation for this information."}
                    )
                    request["responded_at"] = datetime.now().isoformat()
                    break
    
    def get_expert_suggestions(self, session_id: str, field_id: str) -> Dict:
        """Get expert suggestions for a specific field"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Find expert requests for this field
        field_requests = [
            req for req in session["expert_requests"] 
            if req["field_id"] == field_id and req["status"] == "completed"
        ]
        
        if not field_requests:
            return {"success": False, "error": "No expert suggestions available"}
        
        latest_request = field_requests[-1]
        return {
            "success": True,
            "suggestion": latest_request["expert_response"],
            "timestamp": latest_request["responded_at"]
        }
    
    def search_ehr_for_field(self, session_id: str, field_id: str, 
                           search_terms: List[str] = None) -> Dict:
        """Search EHR for information to fill a specific field"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        patient_mrn = session["patient_mrn"]
        
        # Use provided search terms or get from expert knowledge
        if not search_terms:
            expert_knowledge = session.get("expert_knowledge", {})
            search_strategies = expert_knowledge.get("document_search_strategies", {})
            field_strategy = search_strategies.get(field_id, {})
            search_terms = field_strategy.get("additional_terms", [field_id])
        
        # Search documents
        documents = self.ehr_system.get_patient_documents(patient_mrn)
        relevant_docs = []
        
        for doc in documents:
            doc_content = doc.get("content", "").lower()
            for term in search_terms:
                if term.lower() in doc_content:
                    relevant_docs.append({
                        "doc_id": doc.get("doc_id"),
                        "type": doc.get("type"),
                        "date": doc.get("date"),
                        "content": doc.get("content"),
                        "relevance": "high" if term.lower() in doc_content else "medium"
                    })
                    break
        
        return {
            "success": True,
            "field_id": field_id,
            "search_terms": search_terms,
            "found_documents": relevant_docs,
            "suggested_value": self._extract_suggested_value(field_id, relevant_docs)
        }
    
    def _extract_suggested_value(self, field_id: str, documents: List[Dict]) -> str:
        """Extract suggested value from found documents"""
        if not documents:
            return ""
        
        # Use the most relevant document
        best_doc = documents[0]
        content = best_doc.get("content", "")
        
        # Simple extraction logic - in real implementation, use NLP
        if field_id == "genetic_counseling":
            if "genetic counseling" in content.lower():
                return "Completed"
            elif "counseling" in content.lower():
                return "Completed"
            else:
                return "Not documented"
        
        elif field_id == "family_history":
            if "family history" in content.lower():
                return "Positive family history documented"
            else:
                return "No family history documented"
        
        # Return a summary for other fields
        return content[:100] + "..." if len(content) > 100 else content
    
    def draft_clinician_message(self, session_id: str, field_id: str, 
                               missing_info: str) -> Dict:
        """Draft a message to the clinician requesting missing information"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Get field information
        field_info = None
        for section in session["form_template"]["sections"]:
            for field in section["fields"]:
                if field["id"] == field_id:
                    field_info = field
                    break
            if field_info:
                break
        
        if not field_info:
            return {"success": False, "error": "Field not found"}
        
        # Draft message
        message = {
            "to": "Ordering Provider",
            "subject": f"Prior Authorization - Missing Information: {field_info['label']}",
            "patient": session["patient_mrn"],
            "body": f"""
Dear Provider,

I am processing a prior authorization request for {session['cpt_code']} for patient {session['patient_mrn']}.

The insurance provider requires additional information for the field: {field_info['label']}

Missing Information: {missing_info}

Please provide this information so I can complete the prior authorization submission.

Thank you,
AI Prior Authorization Agent
            """.strip(),
            "priority": "medium",
            "requested_field": field_id,
            "missing_info": missing_info
        }
        
        return {
            "success": True,
            "message": message,
            "can_send": True
        }
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get current status of the form editing session"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        return self._get_session_status(session)
    
    def _get_session_status(self, session: Dict) -> Dict:
        """Get status information for a session"""
        # Generate form preview
        preview = self.form_manager.generate_form_preview(
            session["form_data"], session["form_template"]
        )
        
        # Count pending expert requests
        pending_requests = len([
            req for req in session["expert_requests"] 
            if req["status"] == "pending"
        ])
        
        return {
            "session_id": session["session_id"],
            "status": session["status"],
            "completion_percentage": (preview["summary"]["completed_fields"] / 
                                    max(preview["summary"]["total_fields"], 1)) * 100,
            "missing_required": preview["summary"]["missing_required"],
            "validation_errors": len(session["validation_errors"]),
            "pending_expert_requests": pending_requests,
            "last_modified": session["last_modified"],
            "form_preview": preview
        }
    
    def finalize_form(self, session_id: str) -> Dict:
        """Finalize the form for submission"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Final validation
        validation_result = self.form_manager.validate_form_data(
            session["form_data"], session["form_template"]
        )
        
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "error": "Form validation failed",
                "validation_errors": validation_result["missing_required"]
            }
        
        # Mark session as finalized
        session["status"] = "finalized"
        session["finalized_at"] = datetime.now().isoformat()
        
        # Generate final form data
        final_form = {
            "form_template": session["form_template"],
            "form_data": session["form_data"],
            "validation_result": validation_result,
            "ehr_citations": session["form_data"].get("ehr_citations", []),
            "human_edits": session["human_edits"],
            "expert_requests": session["expert_requests"],
            "finalized_at": session["finalized_at"]
        }
        
        return {
            "success": True,
            "form_finalized": True,
            "final_form": final_form,
            "submission_ready": True
        }
