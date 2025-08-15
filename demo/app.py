
from flask import Flask, render_template, jsonify, request
from epic_api_simulation import EpicAPISimulation
from gpt5_integration import GPT5Integration
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db

app = Flask(__name__)

# Initialize systems
epic_api = EpicAPISimulation()
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

# EPIC API Simulation Endpoints
@app.route('/api/epic/Patient/<mrn>')
def get_patient_data(mrn):
    """Get patient data from EPIC FHIR API"""
    try:
        patient_response = epic_api.get_patient_by_mrn(mrn)
        if patient_response and patient_response.get('entry'):
            return jsonify(patient_response)
        else:
            return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        print(f"Error getting patient data from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/DocumentReference')
def get_patient_documents():
    """Get patient documents from EPIC FHIR API"""
    try:
        patient_id = request.args.get('patient', '')
        doc_type = request.args.get('type', '')
        
        if not patient_id:
            return jsonify({'error': 'Patient parameter required'}), 400
        
        documents = epic_api.get_patient_documents(patient_id, doc_type)
        return jsonify(documents)
    except Exception as e:
        print(f"Error getting patient documents from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/Observation')
def get_patient_observations():
    """Get patient observations (labs, vitals) from EPIC FHIR API"""
    try:
        patient_id = request.args.get('patient', '')
        category = request.args.get('category', '')
        
        if not patient_id:
            return jsonify({'error': 'Patient parameter required'}), 400
        
        observations = epic_api.get_patient_observations(patient_id, category)
        return jsonify(observations)
    except Exception as e:
        print(f"Error getting patient observations from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/Condition')
def get_patient_conditions():
    """Get patient conditions (diagnoses) from EPIC FHIR API"""
    try:
        patient_id = request.args.get('patient', '')
        
        if not patient_id:
            return jsonify({'error': 'Patient parameter required'}), 400
        
        conditions = epic_api.get_patient_conditions(patient_id)
        return jsonify(conditions)
    except Exception as e:
        print(f"Error getting patient conditions from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/Procedure')
def get_patient_procedures():
    """Get patient procedures from EPIC FHIR API"""
    try:
        patient_id = request.args.get('patient', '')
        
        if not patient_id:
            return jsonify({'error': 'Patient parameter required'}), 400
        
        procedures = epic_api.get_patient_procedures(patient_id)
        return jsonify(procedures)
    except Exception as e:
        print(f"Error getting patient procedures from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/FamilyMemberHistory')
def get_family_history():
    """Get patient family history from EPIC FHIR API"""
    try:
        patient_id = request.args.get('patient', '')
        
        if not patient_id:
            return jsonify({'error': 'Patient parameter required'}), 400
        
        family_history = epic_api.get_family_history(patient_id)
        return jsonify(family_history)
    except Exception as e:
        print(f"Error getting family history from EPIC: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/Patient')
def search_patients():
    """Search for patients in EPIC FHIR API"""
    try:
        name_query = request.args.get('name', '')
        identifier_query = request.args.get('identifier', '')
        
        if not name_query and not identifier_query:
            return jsonify({'error': 'Name or identifier parameter required'}), 400
        
        query = name_query or identifier_query
        patients = epic_api.search_patients(query)
        return jsonify(patients)
    except Exception as e:
        print(f"Error searching patients in EPIC: {e}")
        return jsonify({'error': str(e)}), 500

# Legacy endpoints for backward compatibility
@app.route('/api/ehr/patient/<mrn>')
def get_patient_data_legacy(mrn):
    """Legacy endpoint - redirects to EPIC API"""
    return get_patient_data(mrn)

@app.route('/api/ehr/patient/<mrn>/documents')
def get_patient_documents_legacy(mrn):
    """Legacy endpoint - redirects to EPIC API"""
    # Add patient parameter to request args
    from flask import request
    request.args = request.args.copy()
    request.args['patient'] = mrn
    return get_patient_documents()

@app.route('/api/ehr/patient/<mrn>/lab-results')
def get_lab_results_legacy(mrn):
    """Legacy endpoint - redirects to EPIC API"""
    # Add patient parameter to request args
    from flask import request
    request.args = request.args.copy()
    request.args['patient'] = mrn
    return get_patient_observations()

@app.route('/api/ehr/patient/<mrn>/family-history')
def get_family_history_legacy(mrn):
    """Legacy endpoint - redirects to EPIC API"""
    # Add patient parameter to request args
    from flask import request
    request.args = request.args.copy()
    request.args['patient'] = mrn
    return get_family_history()

@app.route('/api/ehr/patient/<mrn>/clinical-summary')
def get_clinical_summary_legacy(mrn):
    """Get comprehensive clinical summary from EPIC FHIR API"""
    try:
        # Get patient data
        patient_response = epic_api.get_patient_by_mrn(mrn)
        if not patient_response or not patient_response.get('entry'):
            return jsonify({'error': 'Patient not found'}), 404
        
        patient = patient_response['entry'][0]['resource']
        
        # Get additional data
        observations = epic_api.get_patient_observations(mrn)
        documents = epic_api.get_patient_documents(mrn)
        conditions = epic_api.get_patient_conditions(mrn)
        procedures = epic_api.get_patient_procedures(mrn)
        
        # Create summary
        summary = {
            'patient': patient,
            'lab_count': observations.get('total', 0),
            'document_count': documents.get('total', 0),
            'condition_count': conditions.get('total', 0),
            'procedure_count': procedures.get('total', 0)
        }
        
        return jsonify(summary)
    except Exception as e:
        print(f"Error getting clinical summary from EPIC: {e}")
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
        # Delete the database file to force recreation
        import os
        if os.path.exists('demo.db'):
            os.remove('demo.db')
        
        # Reinitialize the database
        success = db.reset_database()
        return jsonify({'success': success, 'message': 'Database reset successfully with new schema'})
    except Exception as e:
        print(f"Error resetting database: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/settings')
def settings():
    return render_template('settings.html')

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
    app.run(debug=True, host='0.0.0.0', port=5000)