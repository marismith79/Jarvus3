from flask import Flask, render_template, jsonify, request
from database import db
from mock_ehr_system import MockEHRSystem
from gpt5_integration import GPT5Integration
import json

app = Flask(__name__)

# Initialize systems
ehr_system = MockEHRSystem()
gpt5_system = GPT5Integration()

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)