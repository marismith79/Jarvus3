
from flask import Flask, render_template, jsonify, request
from mock_ehr_system import MockEHRSystem
from gpt5_integration import GPT5Integration
from enhanced_insurance_analysis import enhanced_insurance_analyzer
import json
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db

app = Flask(__name__)

# Initialize systems
ehr_system = MockEHRSystem()
gpt5_system = GPT5Integration()

# In-memory demo store for workflows
# In a real app, replace with a database
workflows = [
    {
        "id": 1,
        "name": "Onboarding Flow",
        "description": "Welcomes new users and collects initial preferences.",
        "cpt_code": "",
        "payer_nuances": [],
    },
    {
        "id": 2,
        "name": "Support Triage",
        "description": "Routes incoming support requests to appropriate queues.",
        "cpt_code": "",
        "payer_nuances": [],
    },
]
next_workflow_id = 3

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    try:
        # Force database initialization
        stats = db.get_stats()
        print(f"Database initialized with {stats['total']} records")
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error initializing dashboard: {e}")
        return render_template('dashboard.html')

@app.route('/agent-setup')
def agent_setup():
    """Agent setup page"""
    return render_template('agent_setup.html')

@app.route('/api/prior-auths/<status>')
def get_prior_auths(status):
    """Get prior authorizations by status"""
    try:
        # Map frontend tab names to database status values
        status_mapping = {
            'all': 'all',
            'pending': 'pending',
            'running': 'running',
            'review': 'review',
            'feedback': 'feedback',
            'completed': 'completed'
        }
        
        db_status = status_mapping.get(status, 'all')
        prior_auths = db.get_prior_auths_by_status(db_status)
        
        print(f"Retrieved {len(prior_auths)} prior authorizations for status '{status}'")
        return jsonify(prior_auths)
    except Exception as e:
        print(f"Error getting prior authorizations: {e}")
        return jsonify([])

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({
            'total': 0,
            'pending': 0,
            'running': 0,
            'review': 0,
            'feedback': 0,
            'completed': 0,
            'providers': {},
            'step_counts': {}
        })

@app.route('/api/prior-auths/<int:auth_id>/start-automation', methods=['POST'])
def start_automation(auth_id):
    """Start automation for a prior authorization"""
    try:
        success = db.start_automation(auth_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error starting automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/pause-automation', methods=['POST'])
def pause_automation(auth_id):
    """Pause automation for a prior authorization"""
    try:
        success = db.pause_automation(auth_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error pausing automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/approve-step', methods=['POST'])
def approve_step(auth_id):
    """Approve current step and move to next"""
    try:
        data = request.get_json()
        step_number = data.get('step_number', 1)
        success = db.approve_step(auth_id, step_number)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error approving step: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/request-changes', methods=['POST'])
def request_changes(auth_id):
    """Request changes for a prior authorization"""
    try:
        data = request.get_json()
        step_number = data.get('step_number', 1)
        changes = data.get('changes', '')
        success = db.request_changes(auth_id, step_number, changes)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error requesting changes: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/provide-feedback', methods=['POST'])
def provide_feedback(auth_id):
    """Provide feedback for a prior authorization"""
    try:
        data = request.get_json()
        feedback = data.get('feedback', '')
        success = db.provide_feedback(auth_id, feedback)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error providing feedback: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/update-step', methods=['POST'])
def update_step(auth_id):
    """Update step details for a prior authorization"""
    try:
        data = request.get_json()
        step_number = data.get('step_number', 1)
        step_details = data.get('step_details', {})
        success = db.update_step(auth_id, step_number, step_details)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error updating step: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Mock EHR System Endpoints
@app.route('/api/ehr/patient/<mrn>')
def get_patient_data(mrn):
    """Get patient data from mock EHR system"""
    try:
        patient_data = ehr_system.get_patient_data(mrn)
        if patient_data:
            return jsonify(patient_data)
        else:
            return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        print(f"Error getting patient data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/documents')
def get_patient_documents(mrn):
    """Get patient documents from mock EHR system"""
    try:
        documents = ehr_system.get_patient_documents(mrn)
        return jsonify(documents)
    except Exception as e:
        print(f"Error getting patient documents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/family-history')
def get_family_history(mrn):
    """Get patient family history from mock EHR system"""
    try:
        family_history = ehr_system.get_family_history(mrn)
        return jsonify(family_history)
    except Exception as e:
        print(f"Error getting family history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/lab-results')
def get_lab_results(mrn):
    """Get patient lab results from mock EHR system"""
    try:
        lab_results = ehr_system.get_lab_results(mrn)
        return jsonify(lab_results)
    except Exception as e:
        print(f"Error getting lab results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/imaging')
def get_imaging(mrn):
    """Get patient imaging reports from mock EHR system"""
    try:
        imaging = ehr_system.get_imaging(mrn)
        return jsonify(imaging)
    except Exception as e:
        print(f"Error getting imaging: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/treatment-history')
def get_treatment_history(mrn):
    """Get patient treatment history from mock EHR system"""
    try:
        treatment_history = ehr_system.get_treatment_history(mrn)
        return jsonify(treatment_history)
    except Exception as e:
        print(f"Error getting treatment history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/search')
def search_documents(mrn):
    """Search patient documents in mock EHR system"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        results = ehr_system.search_documents(mrn, query)
        return jsonify(results)
    except Exception as e:
        print(f"Error searching documents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ehr/patient/<mrn>/clinical-summary')
def get_clinical_summary(mrn):
    """Get comprehensive clinical summary from mock EHR system"""
    try:
        summary = ehr_system.get_clinical_summary(mrn)
        if summary:
            return jsonify(summary)
        else:
            return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        print(f"Error getting clinical summary: {e}")
        return jsonify({'error': str(e)}), 500

# GPT-5 Integration Endpoints
@app.route('/api/gpt5/search-insurance')
def search_insurance_requirements():
    """Search insurance requirements using GPT-5"""
    try:
        cpt_code = request.args.get('cpt', '')
        insurance_provider = request.args.get('provider', '')
        
        if not cpt_code or not insurance_provider:
            return jsonify({'error': 'CPT code and insurance provider required'}), 400
        
        results = gpt5_system.search_insurance_requirements(cpt_code, insurance_provider)
        return jsonify(results)
    except Exception as e:
        print(f"Error searching insurance requirements: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gpt5/validate-coverage')
def validate_coverage():
    """Validate coverage criteria using GPT-5"""
    try:
        cpt_code = request.args.get('cpt', '')
        diagnosis = request.args.get('diagnosis', '')
        insurance_provider = request.args.get('provider', '')
        
        if not all([cpt_code, diagnosis, insurance_provider]):
            return jsonify({'error': 'CPT code, diagnosis, and insurance provider required'}), 400
        
        validation = gpt5_system.validate_coverage_criteria(cpt_code, diagnosis, insurance_provider)
        return jsonify(validation)
    except Exception as e:
        print(f"Error validating coverage: {e}")
        return jsonify({'error': str(e)}), 500

# Workflow Status Endpoint
@app.route('/api/automation/workflow-status/<int:auth_id>')
def get_workflow_status(auth_id):
    """Get current workflow status for a prior authorization"""
    try:
        prior_auths = db.get_prior_auths_by_status('all')
        auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
        
        if not auth:
            return jsonify({'error': 'Prior authorization not found'}), 404
        
        return jsonify({
            'auth_id': auth_id,
            'current_step': auth['current_step'],
            'status': auth['status'],
            'automation_status': auth['automation_status'],
            'step_details': json.loads(auth['step_details']) if auth['step_details'] else {}
        })
    except Exception as e:
        print(f"Error getting workflow status: {e}")
        return jsonify({'error': str(e)}), 500

# Database Reset Endpoint (for demo purposes)
@app.route('/api/reset-database', methods=['POST'])
def reset_database():
    """Reset the database for demo purposes"""
    try:
        success = db.reset_database()
        return jsonify({'success': success, 'message': 'Database reset successfully'})
    except Exception as e:
        print(f"Error resetting database: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/settings')
def settings():
    return render_template('settings.html')

# Enhanced Insurance Analysis Endpoint
@app.route('/api/prior-auths/<int:auth_id>/analyze-insurance', methods=['POST'])
def analyze_insurance_coverage_and_requirements(auth_id):
    """Analyze insurance coverage and requirements using GPT-5 search mode"""
    try:
        # Get prior authorization data
        prior_auths = db.get_prior_auths_by_status('all')
        auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
        
        if not auth:
            return jsonify({'error': 'Prior authorization not found'}), 404
        
        # Extract data for analysis
        cpt_code = auth.get('cpt_code', '')
        insurance_provider = auth.get('payer', '')
        service_type = 'genetic testing'  # Default, could be extracted from auth data
        
        # Get patient context from EHR
        patient_mrn = auth.get('patient_mrn', '')
        patient_context = {}
        patient_address = None
        
        if patient_mrn:
            try:
                ehr_data = ehr_system.get_patient_data(patient_mrn)
                
                # Extract patient address from EHR data
                if isinstance(ehr_data, dict) and 'patient_admin' in ehr_data:
                    patient_address = ehr_data['patient_admin'].get('address')
                
                patient_context = {
                    'has_genetic_counseling': 'genetic counseling' in str(ehr_data).lower(),
                    'has_family_history': 'family history' in str(ehr_data).lower(),
                    'has_clinical_indication': True,  # Default to True
                    'provider_credentials_valid': True,  # Default to True
                    'patient_state': auth.get('patient_state', 'CA')  # Get from auth data or default to CA
                }
            except Exception as e:
                print(f"Error getting EHR data: {e}")
                # Set default patient context with state
                patient_context = {
                    'has_genetic_counseling': False,
                    'has_family_history': False,
                    'has_clinical_indication': True,
                    'provider_credentials_valid': True,
                    'patient_state': auth.get('patient_state', 'CA')
                }
        
        # Run enhanced insurance analysis
        async def run_analysis():
            return await enhanced_insurance_analyzer.analyze_insurance_coverage_and_requirements(
                cpt_code=cpt_code,
                insurance_provider=insurance_provider,
                service_type=service_type,
                patient_context=patient_context,
                patient_address=patient_address
            )
        
        # Run the async analysis
        analysis_result = asyncio.run(run_analysis())
        
        # Convert dataclass to dict for JSON serialization
        result_dict = {
            'cpt_code': analysis_result.cpt_code,
            'insurance_provider': analysis_result.insurance_provider,
            'coverage_status': analysis_result.coverage_status,
            'coverage_details': analysis_result.coverage_details,
            'requirements': [
                {
                    'requirement_type': req.requirement_type,
                    'description': req.description,
                    'evidence_basis': req.evidence_basis,
                    'documentation_needed': req.documentation_needed,
                    'clinical_criteria': req.clinical_criteria,
                    'source_document': req.source_document,
                    'confidence_score': req.confidence_score
                }
                for req in analysis_result.requirements
            ],
            'patient_criteria_match': analysis_result.patient_criteria_match,
            'confidence_score': analysis_result.confidence_score,
            'search_sources': analysis_result.search_sources,
            'recommendations': analysis_result.recommendations,
            'mac_jurisdiction': analysis_result.mac_jurisdiction,
            'ncd_applicable': analysis_result.ncd_applicable,
            'lcd_applicable': analysis_result.lcd_applicable
        }
        
        # Add key information for dashboard display
        dashboard_info = {
            'cpt_requested': cpt_code,
            'insurance_provider': insurance_provider,
            'jurisdiction': analysis_result.mac_jurisdiction if analysis_result.mac_jurisdiction else 'N/A',
            'patient_state': patient_context.get('patient_state', 'N/A') if patient_context else 'N/A',
            'patient_address': patient_address if patient_address else 'N/A'
        }
        
        result_dict['dashboard_info'] = dashboard_info
        
        # Update the prior authorization status to indicate step 1 is completed
        db.update_step_status(auth_id, 1, 'completed', 'Insurance coverage & requirements analysis completed')
        
        return jsonify({
            'success': True,
            'analysis': result_dict,
            'message': 'Insurance analysis completed successfully'
        })
        
    except Exception as e:
        print(f"Error analyzing insurance coverage: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoints for workflows
@app.get('/api/workflows')
def list_workflows():
    return jsonify(workflows)


@app.get('/api/workflows/<int:workflow_id>')
def get_workflow(workflow_id: int):
    for wf in workflows:
        if wf["id"] == workflow_id:
            return jsonify(wf)
    return jsonify({"error": "Workflow not found"}), 404


@app.post('/api/workflows')
def create_workflow():
    global next_workflow_id
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    cpt_code = (data.get("cpt_code") or "").strip()
    payer_nuances = data.get("payer_nuances") or []
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    new_wf = {
        "id": next_workflow_id,
        "name": name,
        "description": description,
        "cpt_code": cpt_code,
        "payer_nuances": payer_nuances,
    }
    workflows.append(new_wf)
    next_workflow_id += 1
    return jsonify(new_wf), 201


@app.put('/api/workflows/<int:workflow_id>')
def update_workflow(workflow_id: int):
    data = request.get_json(silent=True) or {}
    for wf in workflows:
        if wf["id"] == workflow_id:
            if "name" in data:
                name = (data.get("name") or "").strip()
                if not name:
                    return jsonify({"error": "'name' is required"}), 400
                wf["name"] = name
            if "description" in data:
                wf["description"] = (data.get("description") or "").strip()
            if "cpt_code" in data:
                wf["cpt_code"] = (data.get("cpt_code") or "").strip()
            if "payer_nuances" in data:
                # expect list of { payer: str, plan_type: 'medicare_advantage'|'commercial', description: str }
                pn = data.get("payer_nuances") or []
                if not isinstance(pn, list):
                    return jsonify({"error": "'payer_nuances' must be a list"}), 400
                wf["payer_nuances"] = pn
            return jsonify(wf)
    return jsonify({"error": "Workflow not found"}), 404

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(debug=True, host='0.0.0.0', port=port)