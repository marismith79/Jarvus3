
from flask import Flask, render_template, jsonify, request
from backend.mock_ehr_system import MockEHRSystem
from backend.gpt5_integration import GPT5Integration
from backend.insurance_analysis import enhanced_insurance_analyzer, run_automation_workflow, run_form_completion_in_background
from backend.form_manager import FormManager
from backend.interactive_form_editor import InteractiveFormEditor
import json
import sys
import os
import asyncio
import threading
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.database import db

app = Flask(__name__)

# Initialize systems
ehr_system = MockEHRSystem()
gpt5_system = GPT5Integration()
form_manager = FormManager(ehr_system)
form_editor = InteractiveFormEditor(form_manager, ehr_system)

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

# Background automation tasks storage
background_tasks = {}

# Store detailed results for each automation
automation_details = {}

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

@app.route('/interactive-form')
def interactive_form():
    """Interactive form editor page"""
    return render_template('interactive_form.html')

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
    """Start automation for a prior authorization in background"""
    try:
        # Check if automation is already running
        if auth_id in background_tasks and background_tasks[auth_id]['is_running']:
            return jsonify({'success': True, 'message': 'Automation already running'})
        
        # Initialize task state
        background_tasks[auth_id] = {
            'is_running': True,
            'current_step': 1,
            'progress': 0,
            'message': 'Starting automation...',
            'start_time': datetime.now(),
            'last_update': datetime.now(),
            'results': {},
            'error': None
        }
        
        # Initialize detailed results storage
        automation_details[auth_id] = {
            'search_results': [],
            'parsing_agent_results': None,
            'form_data': {},
            'extracted_documents': [],
            'current_activity': '',
            'citations': []
        }
        
        # Start background thread
        thread = threading.Thread(target=run_automation_workflow_thread, args=(auth_id,))
        thread.daemon = True
        thread.start()
        
        # Update database status
        db.start_automation(auth_id)
        
        return jsonify({'success': True, 'message': 'Automation started in background'})
    except Exception as e:
        print(f"Error starting automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

def run_automation_workflow_thread(auth_id):
    """Run automation workflow in background thread"""
    try:
        # Get prior authorization data
        prior_auths = db.get_prior_auths_by_status('all')
        auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
        
        if not auth:
            background_tasks[auth_id]['error'] = 'Prior authorization not found'
            background_tasks[auth_id]['is_running'] = False
            return
        
        # Run the automation workflow using the insurance analysis module
        result = asyncio.run(run_automation_workflow(auth_id, auth, background_tasks, automation_details, db))
        
        if result.get('error'):
            background_tasks[auth_id]['error'] = result['error']
            background_tasks[auth_id]['is_running'] = False
            return
        
        # Store coverage results if available
        if 'coverage_result' in result:
            background_tasks[auth_id]['results']['coverage'] = result['coverage_result']
        
        # Store form results if available
        if 'form_result' in result:
            background_tasks[auth_id]['results']['form'] = result['form_result']
        
        # Check if ready for form completion
        if result.get('ready_for_form', False):
            print(f"🔄 Coverage analysis complete, starting form completion for auth {auth_id}")
            # Start form completion in background
            form_thread = threading.Thread(target=run_form_completion_in_background, args=(auth_id, auth, background_tasks, automation_details, db))
            form_thread.daemon = True
            form_thread.start()
        
    except Exception as e:
        print(f"Error in background automation workflow: {e}")
        background_tasks[auth_id]['error'] = str(e)
        background_tasks[auth_id]['is_running'] = False

def check_requirements_vs_ehr_data(auth_id, auth, coverage_result):
    """Check if insurance requirements are met by available EHR data"""
    try:
        patient_mrn = auth.get('patient_mrn', '')
        if not patient_mrn:
            return {'needs_clinician_input': False, 'missing_requirements': []}
        
        # Get EHR data
        ehr_data = ehr_system.get_patient_data(patient_mrn)
        
        # Extract requirements from coverage analysis
        requirements = coverage_result.get('requirements', [])
        missing_requirements = []
        
        for req in requirements:
            req_type = req.get('requirement_type', '').lower()
            req_description = req.get('description', '').lower()
            
            # Check specific requirement types
            if 'genetic counseling' in req_description or 'counseling' in req_type:
                if not ehr_data.get('genetic_counseling_documentation'):
                    missing_requirements.append({
                        'type': 'genetic_counseling',
                        'description': req.get('description', 'Genetic counseling documentation required'),
                        'documentation_needed': req.get('documentation_needed', 'Genetic counseling note or referral'),
                        'clinical_criteria': req.get('clinical_criteria', '')
                    })
            
            elif 'family history' in req_description or 'family' in req_type:
                if not ehr_data.get('family_history_documentation'):
                    missing_requirements.append({
                        'type': 'family_history',
                        'description': req.get('description', 'Family history documentation required'),
                        'documentation_needed': req.get('documentation_needed', 'Family history assessment'),
                        'clinical_criteria': req.get('clinical_criteria', '')
                    })
            
            elif 'clinical indication' in req_description or 'indication' in req_type:
                if not ehr_data.get('clinical_indication_documentation'):
                    missing_requirements.append({
                        'type': 'clinical_indication',
                        'description': req.get('description', 'Clinical indication documentation required'),
                        'documentation_needed': req.get('documentation_needed', 'Clinical notes supporting testing'),
                        'clinical_criteria': req.get('clinical_criteria', '')
                    })
            
            elif 'provider credentials' in req_description or 'credentials' in req_type:
                if not ehr_data.get('provider_credentials'):
                    missing_requirements.append({
                        'type': 'provider_credentials',
                        'description': req.get('description', 'Provider credentials verification required'),
                        'documentation_needed': req.get('documentation_needed', 'Provider certification or credentials'),
                        'clinical_criteria': req.get('clinical_criteria', '')
                    })
        
        return {
            'needs_clinician_input': len(missing_requirements) > 0,
            'missing_requirements': missing_requirements,
            'ehr_data_available': bool(ehr_data)
        }
        
    except Exception as e:
        print(f"Error checking requirements vs EHR data: {e}")
        return {'needs_clinician_input': False, 'missing_requirements': []}

def draft_clinician_message(auth_id, auth, missing_requirements):
    """Draft a message to the clinician requesting missing information"""
    try:
        patient_name = auth.get('patient_name', 'Unknown Patient')
        service_type = auth.get('service_type', 'Genetic Testing')
        cpt_code = auth.get('cpt_code', 'N/A')
        
        # Create message content
        message_lines = [
            f"Subject: Prior Authorization - Missing Information Required",
            "",
            f"Dear Dr. [Provider Name],",
            "",
            f"Regarding prior authorization for {patient_name} (MRN: {auth.get('patient_mrn', 'N/A')}) for {service_type} (CPT: {cpt_code}),",
            "",
            "Our automated system has identified that the following documentation is required by the insurance provider but is not currently available in the patient's EHR:",
            ""
        ]
        
        for i, req in enumerate(missing_requirements, 1):
            message_lines.extend([
                f"{i}. {req['description']}",
                f"   Required Documentation: {req['documentation_needed']}",
                ""
            ])
        
        message_lines.extend([
            "Please provide the missing documentation so we can proceed with the prior authorization request.",
            "",
            "If you have any questions or need assistance, please contact our prior authorization team.",
            "",
            "Thank you,",
            "Prior Authorization Team"
        ])
        
        return {
            'subject': f"Prior Authorization - Missing Information for {patient_name}",
            'content': '\n'.join(message_lines),
            'missing_requirements': missing_requirements,
            'patient_name': patient_name,
            'service_type': service_type,
            'cpt_code': cpt_code,
            'auth_id': auth_id
        }
        
    except Exception as e:
        print(f"Error drafting clinician message: {e}")
        return {
            'subject': 'Prior Authorization - Missing Information',
            'content': 'Error generating message content.',
            'missing_requirements': missing_requirements,
            'auth_id': auth_id
        }

def run_coverage_analysis_in_background(auth_id, auth):
    """Run coverage analysis in background"""
    try:
        # Extract data for analysis
        cpt_code = auth.get('cpt_code', '')
        insurance_provider = auth.get('payer', '')
        service_type = 'genetic testing'
        
        # Get patient context
        patient_mrn = auth.get('patient_mrn', '')
        patient_context = {}
        
        if patient_mrn:
            try:
                ehr_data = ehr_system.get_patient_data(patient_mrn)
                
                # Check for genetic counseling documentation
                has_genetic_counseling = False
                if 'genetics_counseling_and_consent' in ehr_data:
                    counseling_data = ehr_data['genetics_counseling_and_consent']
                    has_genetic_counseling = (
                        counseling_data.get('genetic_counselor') and 
                        counseling_data.get('counseling_date') and
                        counseling_data.get('risk_assessment_completed', False)
                    )
                
                # Check for family history documentation
                has_family_history = False
                if 'family_history' in ehr_data and ehr_data['family_history']:
                    has_family_history = len(ehr_data['family_history']) > 0
                
                # Check for clinical indication documentation
                has_clinical_indication = False
                if 'clinical_notes' in ehr_data and ehr_data['clinical_notes']:
                    clinical_notes = ehr_data['clinical_notes']
                    has_clinical_indication = any(
                        'medical necessity' in note.get('content', '').lower() or
                        'clinical indication' in note.get('content', '').lower()
                        for note in clinical_notes
                    )
                
                patient_context = {
                    'has_genetic_counseling': has_genetic_counseling,
                    'has_family_history': has_family_history,
                    'has_clinical_indication': has_clinical_indication,
                    'provider_credentials_valid': True,
                    'patient_state': auth.get('patient_state', 'CT')  # Updated to CT
                }
                
                print(f"🔍 Patient context for {patient_mrn}:")
                print(f"  - Has genetic counseling: {has_genetic_counseling}")
                print(f"  - Has family history: {has_family_history}")
                print(f"  - Has clinical indication: {has_clinical_indication}")
                
            except Exception as e:
                print(f"Error getting EHR data: {e}")
                patient_context = {
                    'has_genetic_counseling': False,
                    'has_family_history': False,
                    'has_clinical_indication': True,
                    'provider_credentials_valid': True,
                    'patient_state': auth.get('patient_state', 'CT')
                }
        
        # Update progress
        background_tasks[auth_id]['progress'] = 10
        background_tasks[auth_id]['message'] = 'Determining MAC jurisdiction...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Determine MAC jurisdiction
        mac_jurisdiction = None
        if any(medicare_term in insurance_provider.lower() 
               for medicare_term in ['medicare', 'original medicare', 'cms']):
            patient_state = patient_context.get('patient_state', 'CA')
            mac_jurisdiction = enhanced_insurance_analyzer.get_mac_jurisdiction(patient_state)
        
        # Update progress
        background_tasks[auth_id]['progress'] = 20
        background_tasks[auth_id]['message'] = 'Generating search queries...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Generate search queries
        search_queries = enhanced_insurance_analyzer._generate_medicare_search_queries(
            cpt_code, insurance_provider, service_type, mac_jurisdiction
        )
        
        # Take top 5 queries to avoid timeouts
        important_queries = search_queries[:5]
        
        # Update progress
        background_tasks[auth_id]['progress'] = 30
        background_tasks[auth_id]['message'] = f'Running {len(important_queries)} searches...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Run searches
        all_search_results = []
        for i, query in enumerate(important_queries):
            try:
                background_tasks[auth_id]['message'] = f'Searching: {query[:50]}...'
                background_tasks[auth_id]['last_update'] = datetime.now()
                
                # Update current activity
                automation_details[auth_id]['current_activity'] = f'Searching: {query}'
                
                search_results = asyncio.run(enhanced_insurance_analyzer._gpt_search(None, query))
                if search_results:
                    all_search_results.extend(search_results)
                    
                    # Store search results with query context
                    automation_details[auth_id]['search_results'].append({
                        'query': query,
                        'results': search_results,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Add citations
                    for result in search_results:
                        if result.get('url') and result.get('title'):
                            automation_details[auth_id]['citations'].append({
                                'source': result.get('source', 'Unknown'),
                                'url': result.get('url'),
                                'title': result.get('title'),
                                'relevance': result.get('relevance', 0),
                                'type': 'search_result'
                            })
                
                background_tasks[auth_id]['progress'] = 30 + (i * 10)
                background_tasks[auth_id]['last_update'] = datetime.now()
                
            except Exception as e:
                print(f"Error in search query '{query}': {e}")
        
        # Update progress
        background_tasks[auth_id]['progress'] = 70
        background_tasks[auth_id]['message'] = 'Processing search results...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Process and deduplicate results
        unique_results = enhanced_insurance_analyzer._deduplicate_results(all_search_results)
        unique_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        # Update progress
        background_tasks[auth_id]['progress'] = 80
        background_tasks[auth_id]['message'] = 'Extracting policy documents...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Extract policy documents
        automation_details[auth_id]['current_activity'] = 'Extracting policy documents from search results'
        policy_documents = asyncio.run(enhanced_insurance_analyzer._extract_policy_documents_with_gpt(unique_results[:10]))
        
        # Store extracted documents
        automation_details[auth_id]['extracted_documents'] = policy_documents
        
        # Update progress
        background_tasks[auth_id]['progress'] = 85
        background_tasks[auth_id]['message'] = 'Running parsing agent analysis...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Run parsing agent analysis
        automation_details[auth_id]['current_activity'] = 'Running parsing agent analysis'
        parsing_agent_result = asyncio.run(enhanced_insurance_analyzer._analyze_documents_with_parsing_agent(
            unique_results[:10], patient_context, cpt_code, insurance_provider
        ))
        
        # Store parsing agent results
        automation_details[auth_id]['parsing_agent_results'] = parsing_agent_result
        
        # Update progress
        background_tasks[auth_id]['progress'] = 90
        background_tasks[auth_id]['message'] = 'Analyzing coverage and requirements...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Analyze coverage and requirements
        coverage_info = asyncio.run(enhanced_insurance_analyzer._analyze_coverage_and_requirements_with_gpt(
            cpt_code, insurance_provider, policy_documents, patient_context, mac_jurisdiction
        ))
        
        # Check patient criteria
        patient_criteria_match = {}
        if patient_context:
            patient_criteria_match = asyncio.run(enhanced_insurance_analyzer._check_patient_criteria_with_gpt(
                coverage_info.requirements, patient_context
            ))
        
        # Generate recommendations
        recommendations = asyncio.run(enhanced_insurance_analyzer._generate_recommendations_with_gpt(
            coverage_info, patient_criteria_match, patient_context
        ))
        
        # Create final result
        final_result = {
            'cpt_code': cpt_code,
            'insurance_provider': insurance_provider,
            'coverage_status': coverage_info.coverage_status,
            'coverage_details': coverage_info.coverage_details,
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
                for req in coverage_info.requirements
            ],
            'patient_criteria_match': patient_criteria_match,
            'confidence_score': coverage_info.confidence_score,
            'search_sources': unique_results[:10],
            'recommendations': recommendations,
            'mac_jurisdiction': mac_jurisdiction["name"] if mac_jurisdiction else None,
            'ncd_applicable': coverage_info.ncd_applicable if hasattr(coverage_info, 'ncd_applicable') else False,
            'lcd_applicable': coverage_info.lcd_applicable if hasattr(coverage_info, 'lcd_applicable') else False,
            'parsing_agent_result': parsing_agent_result
        }
        
        return final_result
        
    except Exception as e:
        print(f"Error in coverage analysis: {e}")
        return {'error': str(e)}





@app.route('/api/prior-auths/<int:auth_id>/cancel-automation', methods=['POST'])
def cancel_automation(auth_id):
    """Cancel automation for a prior authorization"""
    try:
        # Remove from background tasks
        if auth_id in background_tasks:
            background_tasks[auth_id]['is_running'] = False
            background_tasks[auth_id]['error'] = 'Cancelled by user'
        
        if auth_id in automation_details:
            del automation_details[auth_id]
        
        # Update database status
        db.update_prior_auth_status(auth_id, 'pending')
        
        return jsonify({'success': True, 'message': 'Automation cancelled'})
    except Exception as e:
        print(f"Error cancelling automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/send-clinician-message', methods=['POST'])
def send_clinician_message(auth_id):
    """Send clinician message and mark case as deferred"""
    try:
        # Get the clinician message from automation details
        if auth_id not in automation_details or 'clinician_message' not in automation_details[auth_id]:
            return jsonify({'success': False, 'error': 'No clinician message found'})
        
        clinician_message = automation_details[auth_id]['clinician_message']
        
        # In a real system, this would send the message via EPIC or other messaging system
        # For demo purposes, we'll just log it
        print(f"Sending clinician message for auth {auth_id}:")
        print(f"Subject: {clinician_message['subject']}")
        print(f"Content: {clinician_message['content']}")
        
        # Mark case as deferred
        db.update_prior_auth_status(auth_id, 'deferred')
        
        # Update automation details to indicate message was sent
        automation_details[auth_id]['clinician_message_sent'] = True
        automation_details[auth_id]['message_sent_date'] = datetime.now().isoformat()
        
        # Update background task status
        if auth_id in background_tasks:
            background_tasks[auth_id]['message'] = 'Clinician message sent - case deferred'
            background_tasks[auth_id]['last_update'] = datetime.now()
        
        return jsonify({
            'success': True, 
            'message': 'Clinician message sent and case marked as deferred',
            'clinician_message': clinician_message
        })
        
    except Exception as e:
        print(f"Error sending clinician message: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prior-auths/<int:auth_id>/resume-automation', methods=['POST'])
def resume_automation(auth_id):
    """Resume automation after clinician provides missing information"""
    try:
        # Check if case is in deferred status
        auth = db.get_prior_auth_by_id(auth_id)
        if not auth or auth.get('status') != 'deferred':
            return jsonify({'success': False, 'error': 'Case not in deferred status'})
        
        # Reset automation state
        if auth_id in automation_details:
            # Clear clinician message data
            automation_details[auth_id].pop('clinician_message', None)
            automation_details[auth_id].pop('missing_requirements', None)
            automation_details[auth_id].pop('needs_clinician_input', None)
            automation_details[auth_id].pop('clinician_message_sent', None)
            automation_details[auth_id].pop('message_sent_date', None)
        
        # Restart automation from step 2 (form completion)
        background_tasks[auth_id] = {
            'is_running': True,
            'current_step': 2,
            'progress': 50,
            'message': 'Resuming automation - starting form completion...',
            'start_time': datetime.now(),
            'last_update': datetime.now(),
            'results': {},
            'error': None
        }
        
        # Start background thread for form completion
        thread = threading.Thread(target=run_form_completion_only, args=(auth_id, auth))
        thread.daemon = True
        thread.start()
        
        # Update database status
        db.update_prior_auth_status(auth_id, 'running')
        
        return jsonify({'success': True, 'message': 'Automation resumed'})
        
    except Exception as e:
        print(f"Error resuming automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

def run_form_completion_only(auth_id, auth):
    """Run only form completion step (for resumed automations)"""
    try:
        form_result = run_form_completion_in_background(auth_id, auth, background_tasks, automation_details, db)
        
        if 'error' in form_result:
            background_tasks[auth_id]['error'] = form_result['error']
            background_tasks[auth_id]['is_running'] = False
            return
        
        # Complete automation
        background_tasks[auth_id]['progress'] = 100
        background_tasks[auth_id]['message'] = 'Automation completed successfully!'
        background_tasks[auth_id]['is_running'] = False
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Update database status
        db.update_prior_auth_status(auth_id, 'completed')
        
    except Exception as e:
        print(f"Error in form completion only: {e}")
        background_tasks[auth_id]['error'] = str(e)
        background_tasks[auth_id]['is_running'] = False

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
@app.route('/api/automation/status/<int:auth_id>')
def get_automation_status(auth_id):
    """Get current automation status for a prior authorization"""
    try:
        if auth_id not in background_tasks:
            return jsonify({
                'is_running': False,
                'error': 'No automation found for this authorization'
            })
        
        task = background_tasks[auth_id]
        details = automation_details.get(auth_id, {})
        
        return jsonify({
            'is_running': task['is_running'],
            'current_step': task['current_step'],
            'progress': task['progress'],
            'message': task['message'],
            'start_time': task['start_time'].isoformat() if task['start_time'] else None,
            'last_update': task['last_update'].isoformat() if task['last_update'] else None,
            'results': task['results'],
            'error': task['error'],
            'details': details
        })
    except Exception as e:
        print(f"Error getting automation status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-all-cases', methods=['POST'])
def reset_all_cases():
    """Reset all cases to pending status and clear background tasks"""
    try:
        # Clear all background tasks
        global background_tasks, automation_details
        background_tasks.clear()
        automation_details.clear()
        
        # Reset all cases to pending in database
        db.reset_all_to_pending()
        
        return jsonify({'success': True, 'message': 'All cases reset to pending status'})
    except Exception as e:
        print(f"Error resetting cases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        db.update_prior_auth_status(auth_id, 'running')
        db.update_prior_auth_step(auth_id, 2)  # Move to step 2
        
        return jsonify({
            'success': True,
            'analysis': result_dict
        })
        
    except Exception as e:
        print(f"Error in insurance analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# New Streaming GPT-5 Search Endpoint
@app.route('/api/prior-auths/<int:auth_id>/step', methods=['PUT'])
def update_prior_auth_step(auth_id):
    """Update the current step of a prior authorization"""
    try:
        data = request.get_json()
        step = data.get('step', 1)
        
        # Update the step in the database
        db.update_prior_auth_step(auth_id, step)
        
        return jsonify({'success': True, 'step': step})
    except Exception as e:
        print(f"Error updating prior auth step: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prior-auths/<int:auth_id>/gpt5-search-stream', methods=['POST'])
def gpt5_search_stream(auth_id):
    """Stream GPT-5 search results in real-time"""
    from flask import Response, stream_with_context
    import json
    
    def generate_search_stream():
        try:
            # Get prior authorization data
            prior_auths = db.get_prior_auths_by_status('all')
            auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
            
            if not auth:
                yield f"data: {json.dumps({'error': 'Prior authorization not found'})}\n\n"
                return
            
            # Extract data for analysis
            cpt_code = auth.get('cpt_code', '')
            insurance_provider = auth.get('payer', '')
            service_type = 'genetic testing'
            
            # Get patient context
            patient_mrn = auth.get('patient_mrn', '')
            patient_context = {}
            patient_address = None
            
            if patient_mrn:
                try:
                    ehr_data = ehr_system.get_patient_data(patient_mrn)
                    if isinstance(ehr_data, dict) and 'patient_admin' in ehr_data:
                        patient_address = ehr_data['patient_admin'].get('address')
                    
                    patient_context = {
                        'has_genetic_counseling': 'genetic counseling' in str(ehr_data).lower(),
                        'has_family_history': 'family history' in str(ehr_data).lower(),
                        'has_clinical_indication': True,
                        'provider_credentials_valid': True,
                        'patient_state': auth.get('patient_state', 'CA')
                    }
                except Exception as e:
                    print(f"Error getting EHR data: {e}")
                    patient_context = {
                        'has_genetic_counseling': False,
                        'has_family_history': False,
                        'has_clinical_indication': True,
                        'provider_credentials_valid': True,
                        'patient_state': auth.get('patient_state', 'CA')
                    }
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting GPT-5 search...', 'progress': 0})}\n\n"
            
            # Determine MAC jurisdiction
            mac_jurisdiction = None
            if any(medicare_term in insurance_provider.lower() 
                   for medicare_term in ['medicare', 'original medicare', 'cms']):
                patient_state = patient_context.get('patient_state', 'CA')
                mac_jurisdiction = enhanced_insurance_analyzer.get_mac_jurisdiction(patient_state)
            
            if mac_jurisdiction:
                jurisdiction_name = mac_jurisdiction["name"]
                jurisdiction_id = mac_jurisdiction["jurisdiction_id"]
                yield f"data: {json.dumps({'type': 'status', 'message': f'MAC Jurisdiction: {jurisdiction_name} ({jurisdiction_id})', 'progress': 10})}\n\n"
            
            # Generate search queries
            search_queries = enhanced_insurance_analyzer._generate_medicare_search_queries(
                cpt_code, insurance_provider, service_type, mac_jurisdiction
            )
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Generated {len(search_queries)} search queries', 'progress': 20})}\n\n"
            
            # Take top 5 queries to avoid timeouts
            important_queries = search_queries[:5]
            yield f"data: {json.dumps({'type': 'status', 'message': f'Using top {len(important_queries)} queries for search', 'progress': 30})}\n\n"
            
            # Run searches and stream results
            all_search_results = []
            for i, query in enumerate(important_queries):
                try:
                    yield f"data: {json.dumps({'type': 'search_start', 'query': query, 'progress': 30 + (i * 5)})}\n\n"
                    
                    # Run the actual GPT search
                    search_results = asyncio.run(enhanced_insurance_analyzer._gpt_search(None, query))
                    
                    if search_results:
                        all_search_results.extend(search_results)
                        yield f"data: {json.dumps({'type': 'search_result', 'query': query, 'results': search_results, 'count': len(search_results), 'progress': 35 + (i * 5)})}\n\n"
                        
                        # Log detailed results for debugging
                        print(f"\n📊 Search Results for '{query}':")
                        for j, result in enumerate(search_results):
                            print(f"  {j+1}. {result.get('title', 'No title')}")
                            print(f"     URL: {result.get('url', 'No URL')}")
                            print(f"     Type: {result.get('type', 'Unknown')}")
                            print(f"     Relevance: {result.get('relevance', 0)}%")
                            print(f"     Source: {result.get('source', 'Unknown')}")
                    else:
                        yield f"data: {json.dumps({'type': 'search_error', 'query': query, 'error': 'No results found', 'progress': 35 + (i * 5)})}\n\n"
                        
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'search_error', 'query': query, 'error': str(e), 'progress': 50 + (i * 10)})}\n\n"
            
            # Process and deduplicate results
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing and deduplicating results...', 'progress': 80})}\n\n"
            
            unique_results = enhanced_insurance_analyzer._deduplicate_results(all_search_results)
            unique_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(unique_results)} unique results', 'progress': 90})}\n\n"
            
            # Extract policy documents
            yield f"data: {json.dumps({'type': 'status', 'message': 'Extracting policy documents...', 'progress': 92})}\n\n"
            
            policy_documents = asyncio.run(enhanced_insurance_analyzer._extract_policy_documents_with_gpt(unique_results[:10]))
            
            # Run parsing agent analysis
            yield f"data: {json.dumps({'type': 'status', 'message': 'Running parsing agent analysis...', 'progress': 95})}\n\n"
            
            parsing_agent_result = asyncio.run(enhanced_insurance_analyzer._analyze_documents_with_parsing_agent(
                unique_results[:10], patient_context, cpt_code, insurance_provider
            ))
            
            # Analyze coverage and requirements
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing coverage and requirements...', 'progress': 98})}\n\n"
            
            coverage_info = asyncio.run(enhanced_insurance_analyzer._analyze_coverage_and_requirements_with_gpt(
                cpt_code, insurance_provider, policy_documents, patient_context, mac_jurisdiction
            ))
            
            # Check patient criteria
            patient_criteria_match = {}
            if patient_context:
                patient_criteria_match = asyncio.run(enhanced_insurance_analyzer._check_patient_criteria_with_gpt(
                    coverage_info.requirements, patient_context
                ))
            
            # Generate recommendations
            recommendations = asyncio.run(enhanced_insurance_analyzer._generate_recommendations_with_gpt(
                coverage_info, patient_criteria_match, patient_context
            ))
            
            # Create final result
            final_result = {
                'cpt_code': cpt_code,
                'insurance_provider': insurance_provider,
                'coverage_status': coverage_info.coverage_status,
                'coverage_details': coverage_info.coverage_details,
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
                    for req in coverage_info.requirements
                ],
                'patient_criteria_match': patient_criteria_match,
                'confidence_score': coverage_info.confidence_score,
                'search_sources': unique_results[:10],
                'recommendations': recommendations,
                'mac_jurisdiction': mac_jurisdiction["name"] if mac_jurisdiction else None,
                'ncd_applicable': coverage_info.ncd_applicable if hasattr(coverage_info, 'ncd_applicable') else False,
                'lcd_applicable': coverage_info.lcd_applicable if hasattr(coverage_info, 'lcd_applicable') else False,
                'parsing_agent_result': parsing_agent_result
            }
            
            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'result': final_result, 'progress': 100})}\n\n"
            
            # Update database status only (let frontend control step progression)
            db.update_prior_auth_status(auth_id, 'running')
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate_search_stream()), 
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

# Interactive Form Editor Endpoints

@app.route('/api/form-session/create', methods=['POST'])
def create_form_session():
    """Create a new interactive form editing session"""
    try:
        data = request.get_json()
        auth_id = data.get('auth_id')
        patient_mrn = data.get('patient_mrn')
        insurance_provider = data.get('insurance_provider')
        cpt_code = data.get('cpt_code')
        coverage_analysis = data.get('coverage_analysis')
        
        if not all([auth_id, patient_mrn, insurance_provider, cpt_code]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        session = form_editor.create_form_session(
            auth_id, patient_mrn, insurance_provider, cpt_code, coverage_analysis
        )
        
        return jsonify({
            'success': True,
            'session_id': session['session_id'],
            'session': session
        })
    except Exception as e:
        print(f"Error creating form session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/update-field', methods=['POST'])
def update_form_field(session_id):
    """Update a specific form field"""
    try:
        data = request.get_json()
        section_id = data.get('section_id')
        field_id = data.get('field_id')
        value = data.get('value')
        source = data.get('source', 'human_edit')
        
        if not all([section_id, field_id, value]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        result = form_editor.update_form_field(session_id, section_id, field_id, value, source)
        return jsonify(result)
    except Exception as e:
        print(f"Error updating form field: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/request-help', methods=['POST'])
def request_expert_help(session_id):
    """Request help from human expert for a specific field"""
    try:
        data = request.get_json()
        field_id = data.get('field_id')
        question = data.get('question')
        context = data.get('context')
        
        if not all([field_id, question]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        result = form_editor.request_expert_help(session_id, field_id, question, context)
        return jsonify(result)
    except Exception as e:
        print(f"Error requesting expert help: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/search-ehr', methods=['POST'])
def search_ehr_for_field(session_id):
    """Search EHR for information to fill a specific field"""
    try:
        data = request.get_json()
        field_id = data.get('field_id')
        search_terms = data.get('search_terms')
        
        if not field_id:
            return jsonify({'success': False, 'error': 'Missing field_id parameter'})
        
        result = form_editor.search_ehr_for_field(session_id, field_id, search_terms)
        return jsonify(result)
    except Exception as e:
        print(f"Error searching EHR: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/draft-form-message', methods=['POST'])
def draft_form_clinician_message(session_id):
    """Draft a message to the clinician requesting missing information for form fields"""
    try:
        data = request.get_json()
        field_id = data.get('field_id')
        missing_info = data.get('missing_info')
        
        if not all([field_id, missing_info]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        result = form_editor.draft_clinician_message(session_id, field_id, missing_info)
        return jsonify(result)
    except Exception as e:
        print(f"Error drafting clinician message: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/status')
def get_form_session_status(session_id):
    """Get current status of the form editing session"""
    try:
        result = form_editor.get_session_status(session_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error getting session status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/form-session/<session_id>/finalize', methods=['POST'])
def finalize_form(session_id):
    """Finalize the form for submission"""
    try:
        result = form_editor.finalize_form(session_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error finalizing form: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Enhanced Form Completion Streaming Endpoint
@app.route('/api/prior-auths/<int:auth_id>/form-completion-stream', methods=['POST'])
def form_completion_stream(auth_id):
    """Stream form completion with systematic question processing"""
    from flask import Response, stream_with_context
    import json
    
    def generate_form_stream():
        try:
            # Get prior authorization data
            prior_auths = db.get_prior_auths_by_status('all')
            auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
            
            if not auth:
                yield f"data: {json.dumps({'error': 'Prior authorization not found'})}\n\n"
                return
            
            # Import the form question processor
            from backend.form_question_processor import FormQuestionProcessor
            from backend.mock_ehr_system import MockEHRSystem
            
            # Initialize systems
            ehr_system = MockEHRSystem()
            form_processor = FormQuestionProcessor(ehr_system)
            
            # Extract data for form completion
            patient_mrn = auth.get('patient_mrn', '')
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting systematic form question processing...', 'progress': 0})}\n\n"
            
            # Process all questions systematically
            question_results = form_processor.process_all_questions(
                patient_mrn=patient_mrn,
                auth_data=auth,
                progress_callback=None  # We'll handle progress updates manually
            )
            
            if 'error' in question_results:
                yield f"data: {json.dumps({'type': 'error', 'error': question_results['error'], 'progress': 100})}\n\n"
                return
            
            # Send progress updates for each section
            total_questions = question_results['total_questions']
            processed_questions = 0
            
            for section in question_results['sections']:
                yield f"data: {json.dumps({'type': 'status', 'message': f'Processing {section["section_name"]} section...', 'progress': 20})}\n\n"
                
                for question in section['questions']:
                    processed_questions += 1
                    progress = 20 + int((processed_questions / total_questions) * 70)
                    
                    # Send question processing update
                    yield f"data: {json.dumps({
                        'type': 'question_processed',
                        'question_id': question['id'],
                        'question': question['question'],
                        'status': question['status'],
                        'answer': question.get('answer', ''),
                        'source': question.get('source', ''),
                        'progress': progress
                    })}\n\n"
                    
                    # Small delay to simulate processing
                    time.sleep(0.1)
            
            # Send completion status
            yield f"data: {json.dumps({
                'type': 'complete', 
                'progress': 100, 
                'result': {
                    'form_title': question_results['form_title'],
                    'form_id': question_results['form_id'],
                    'version': question_results['version'],
                    'total_questions': question_results['total_questions'],
                    'completed_questions': question_results['completed_questions'],
                    'missing_data': question_results['missing_data'],
                    'processing_time': question_results['processing_time'],
                    'sections': question_results['sections']
                }
            })}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate_form_stream()), mimetype='text/plain')

# Real-time Question Processing Endpoint
@app.route('/api/prior-auths/<int:auth_id>/process-questions-realtime', methods=['POST'])
def process_questions_realtime(auth_id):
    """Process questions in real-time and stream updates"""
    from flask import Response, stream_with_context
    import json
    import time
    
    def generate_realtime_stream():
        try:
            # Get prior authorization data
            prior_auths = db.get_prior_auths_by_status('all')
            auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
            
            if not auth:
                yield f"data: {json.dumps({'error': 'Prior authorization not found'})}\n\n"
                return
            
            # Import the form question processor
            from backend.form_question_processor import FormQuestionProcessor
            from backend.mock_ehr_system import MockEHRSystem
            
            # Initialize systems
            ehr_system = MockEHRSystem()
            form_processor = FormQuestionProcessor(ehr_system)
            
            # Extract data for form completion
            patient_mrn = auth.get('patient_mrn', '')
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting real-time question processing...', 'progress': 0})}\n\n"
            
            # Get all questions from the form
            form_questions = form_processor.form_questions
            total_questions = form_processor.get_total_questions()
            processed_questions = 0
            
            # Process each section and question
            for section in form_questions.get('sections', []):
                section_name = section.get('section_name', '')
                yield f"data: {json.dumps({'type': 'section_start', 'section': section_name, 'progress': 10})}\n\n"
                
                for question in section.get('questions', []):
                    # Handle nested provider information structure
                    if question.get('subsection') and question.get('fields'):
                        # Process each field in the subsection
                        for field in question.get('fields', []):
                            processed_questions += 1
                            progress = 10 + int((processed_questions / total_questions) * 80)
                            
                            # Send field start
                            yield f"data: {json.dumps({
                                'type': 'question_start',
                                'question_id': field.get('id'),
                                'question': field.get('label'),
                                'progress': progress
                            })}\n\n"
                            
                            # Simulate processing time
                            time.sleep(0.5)
                            
                            # Create a question-like structure for the field
                            field_question = {
                                "id": field.get("id"),
                                "question": field.get("label"),
                                "type": field.get("type", "text"),
                                "required": field.get("required", False)
                            }
                            
                            # Process the field
                            patient_data = ehr_system.get_patient_data(patient_mrn)
                            field_result = form_processor._process_question(
                                field_question, patient_data, patient_mrn, auth
                            )
                            
                            # Send field result
                            result_data = {
                                'type': 'question_result',
                                'question_id': field.get('id'),
                                'status': field_result.get('status'),
                                'answer': field_result.get('answer'),
                                'source': field_result.get('source'),
                                'confidence': field_result.get('confidence'),
                                'progress': progress + 5
                            }
                            
                            yield f"data: {json.dumps(result_data)}\n\n"
                            
                            # Small delay between fields
                            time.sleep(0.2)
                    else:
                        # Process regular question
                        processed_questions += 1
                        progress = 10 + int((processed_questions / total_questions) * 80)
                        
                        # Send question start
                        yield f"data: {json.dumps({
                            'type': 'question_start',
                            'question_id': question.get('id'),
                            'question': question.get('question'),
                            'progress': progress
                        })}\n\n"
                        
                        # Simulate processing time
                        time.sleep(0.5)
                        
                        # Process the question
                        patient_data = ehr_system.get_patient_data(patient_mrn)
                        question_result = form_processor._process_question(
                            question, patient_data, patient_mrn, auth
                        )
                        
                        # Send question result
                        result_data = {
                            'type': 'question_result',
                            'question_id': question.get('id'),
                            'status': question_result.get('status'),
                            'answer': question_result.get('answer'),
                            'source': question_result.get('source'),
                            'confidence': question_result.get('confidence'),
                            'progress': progress + 5
                        }
                        
                        # Include follow-up data if present
                        if question_result.get('follow_up'):
                            result_data['follow_up'] = question_result.get('follow_up')
                        
                        yield f"data: {json.dumps(result_data)}\n\n"
                        
                        # Process follow-up question if it exists
                        if question_result.get('follow_up'):
                            processed_questions += 1
                            progress = 10 + int((processed_questions / total_questions) * 80)
                            
                            # Send follow-up question start
                            yield f"data: {json.dumps({
                                'type': 'question_start',
                                'question_id': f"{question.get('id')}_followup",
                                'question': question_result['follow_up']['question'],
                                'progress': progress
                            })}\n\n"
                            
                            # Simulate processing time
                            time.sleep(0.5)
                            
                            # Create follow-up question structure
                            follow_up_question = {
                                "id": f"{question.get('id')}_followup",
                                "question": question_result["follow_up"]["question"],
                                "type": question_result["follow_up"]["type"],
                                "required": False,
                                "is_follow_up": True,
                                "parent_question_id": question.get("id")
                            }
                            
                            # Process the follow-up question
                            follow_up_result = form_processor._process_question(
                                follow_up_question, patient_data, patient_mrn, auth
                            )
                            
                            # Send follow-up question result
                            follow_up_result_data = {
                                'type': 'question_result',
                                'question_id': f"{question.get('id')}_followup",
                                'status': follow_up_result.get('status'),
                                'answer': follow_up_result.get('answer'),
                                'source': follow_up_result.get('source'),
                                'confidence': follow_up_result.get('confidence'),
                                'progress': progress + 5
                            }
                            
                            yield f"data: {json.dumps(follow_up_result_data)}\n\n"
                            
                            # Small delay between follow-up questions
                            time.sleep(0.2)
                        
                        # Small delay between questions
                        time.sleep(0.2)
                
                # Send section complete
                yield f"data: {json.dumps({'type': 'section_complete', 'section': section_name, 'progress': progress + 5})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({
                'type': 'complete',
                'total_questions': total_questions,
                'processed_questions': processed_questions,
                'progress': 100
            })}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate_realtime_stream()), 
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

# API endpoint to get form questions
@app.route('/api/form-questions', methods=['GET'])
def get_form_questions():
    """Get all form questions from the genetic testing form"""
    try:
        from backend.form_question_processor import FormQuestionProcessor
        from backend.mock_ehr_system import MockEHRSystem
        
        ehr_system = MockEHRSystem()
        form_processor = FormQuestionProcessor(ehr_system)
        
        return jsonify({
            'success': True,
            'form_questions': form_processor.form_questions,
            'total_questions': form_processor.get_total_questions()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API endpoint to save form answers
@app.route('/api/prior-auths/<int:auth_id>/save-form-answers', methods=['POST'])
def save_form_answers(auth_id):
    """Save form answers for a prior authorization"""
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        # Store answers in database (for demo, we'll just return success)
        # In a real implementation, this would save to the database
        
        return jsonify({
            'success': True,
            'message': f'Saved {len(answers)} answers for prior authorization {auth_id}',
            'saved_answers': answers
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API endpoint to export filled PDF form
@app.route('/api/prior-auths/<int:auth_id>/export-pdf', methods=['POST'])
def export_pdf_form(auth_id):
    """Export the filled Medicaid Genetic Testing PA Form as PDF"""
    try:
        from flask import send_file
        from backend.pdf_form_filler import PDFFormFiller
        from backend.form_question_processor import FormQuestionProcessor
        from backend.mock_ehr_system import MockEHRSystem
        
        # Get the form data from the request
        data = request.get_json()
        form_data = data.get('form_data', {})
        
        # Get prior authorization data
        prior_auths = db.get_prior_auths_by_status('all')
        auth = next((pa for pa in prior_auths if pa['id'] == auth_id), None)
        
        if not auth:
            return jsonify({'success': False, 'error': 'Prior authorization not found'}), 404
        
        # Initialize systems
        ehr_system = MockEHRSystem()
        form_processor = FormQuestionProcessor(ehr_system)
        
        # Get patient information
        patient_info = {
            'mrn': auth.get('patient_mrn', ''),
            'name': auth.get('patient_name', ''),
            'dob': auth.get('patient_dob', ''),
            'address': '123 Main Street, Hartford, CT 06106'  # Default address
        }
        
        # Get service information
        service_info = {
            'service_type': auth.get('service_type', ''),
            'date_of_service': datetime.now().strftime('%Y-%m-%d'),
            'type_of_test': 'Gene panel',
            'gene_mutation_tested': 'Comprehensive genomic profiling (334 genes)',
            'icd10_codes': auth.get('icd10', 'C34.90'),
            'cpt_codes': auth.get('cpt_code', '')
        }
        
        # Get provider information
        provider_info = {
            'billing_provider': 'Hartford Hospital (Medicaid #123456)',
            'ordering_provider': f"{auth.get('ordering_provider', 'Dr. Jordan Rivera')}, Oncology (Medicaid #789012)",
            'provider_address': '80 Seymour Street, Hartford, CT 06102'
        }
        
        # Combine all data for PDF filling
        complete_form_data = {
            **form_data,
            'service_info': service_info,
            'provider_info': provider_info
        }
        
        # Create PDF form filler and generate PDF
        pdf_filler = PDFFormFiller()
        pdf_content = pdf_filler.fill_form(complete_form_data, patient_info)
        
        # Generate filename
        filename = pdf_filler.generate_filename(patient_info['name'])
        
        # Create a temporary file-like object
        from io import BytesIO
        pdf_stream = BytesIO(pdf_content)
        pdf_stream.seek(0)
        
        return send_file(
            pdf_stream,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    app.run(debug=True, host='0.0.0.0', port=5001)