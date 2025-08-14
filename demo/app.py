from flask import Flask, render_template, jsonify, request
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db

app = Flask(__name__)

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/agent-setup')
def agent_setup():
    return render_template('agent_setup.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/prior-auths/<status>')
def get_prior_auths(status):
    prior_auths = db.get_prior_auths_by_status(status)
    return jsonify(prior_auths)

@app.route('/api/prior-auths/stats')
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/prior-auths/<int:auth_id>/start-automation', methods=['POST'])
def start_automation(auth_id):
    success = db.start_automation(auth_id)
    if success:
        return jsonify({'success': True, 'message': f'Automation started for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start automation'}), 400

@app.route('/api/prior-auths/<int:auth_id>/pause-automation', methods=['POST'])
def pause_automation(auth_id):
    success = db.pause_automation(auth_id)
    if success:
        return jsonify({'success': True, 'message': f'Automation paused for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to pause automation'}), 400

@app.route('/api/prior-auths/<int:auth_id>/approve-step', methods=['POST'])
def approve_step(auth_id):
    success = db.approve_step(auth_id)
    if success:
        return jsonify({'success': True, 'message': f'Step approved for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to approve step'}), 400

@app.route('/api/prior-auths/<int:auth_id>/request-changes', methods=['POST'])
def request_changes(auth_id):
    data = request.get_json()
    changes = data.get('changes')
    
    if not changes:
        return jsonify({'success': False, 'message': 'Changes description is required'}), 400
    
    success = db.request_changes(auth_id, changes)
    if success:
        return jsonify({'success': True, 'message': f'Changes requested for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to request changes'}), 400

@app.route('/api/prior-auths/<int:auth_id>/provide-feedback', methods=['POST'])
def provide_feedback(auth_id):
    data = request.get_json()
    feedback = data.get('feedback')
    
    if not feedback:
        return jsonify({'success': False, 'message': 'Feedback is required'}), 400
    
    success = db.provide_feedback(auth_id, feedback)
    if success:
        return jsonify({'success': True, 'message': f'Feedback provided for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to provide feedback'}), 400

@app.route('/api/prior-auths/<int:auth_id>/update-step', methods=['POST'])
def update_step(auth_id):
    data = request.get_json()
    step_number = data.get('step_number')
    step_status = data.get('step_status')
    step_details = data.get('step_details')
    
    if not all([step_number, step_status, step_details]):
        return jsonify({'success': False, 'message': 'Step number, status, and details are required'}), 400
    
    success = db.update_step(auth_id, step_number, step_status, step_details)
    if success:
        return jsonify({'success': True, 'message': f'Step {step_number} updated for prior auth {auth_id}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update step'}), 400

@app.route('/api/prior-auths/<int:auth_id>/update-status', methods=['POST'])
def update_status(auth_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status is required'}), 400
    
    success = db.update_status(auth_id, new_status)
    if success:
        return jsonify({'success': True, 'message': f'Prior auth {auth_id} status updated to {new_status}'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update status'}), 400

if __name__ == '__main__':
    app.run(debug=True)
