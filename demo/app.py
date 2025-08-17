
from flask import Flask, render_template, jsonify, request
from backend.mock_ehr_system import MockEHRSystem
from backend.gpt5_integration import GPT5Integration
from backend.insurance_analysis import enhanced_insurance_analyzer
import json
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.database import db

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

# Form Completion Streaming Endpoint
@app.route('/api/prior-auths/<int:auth_id>/form-completion-stream', methods=['POST'])
def form_completion_stream(auth_id):
    """Stream form completion with EHR data extraction"""
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
            
            # Extract data for form completion
            cpt_code = auth.get('cpt_code', '')
            insurance_provider = auth.get('payer', '')
            patient_mrn = auth.get('patient_mrn', '')
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting form completion with EHR data extraction...', 'progress': 0})}\n\n"
            
            # Get patient EHR data
            patient_data = {}
            if patient_mrn:
                try:
                    patient_data = ehr_system.get_patient_data(patient_mrn)
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Retrieved patient EHR data', 'progress': 20})}\n\n"
                except Exception as e:
                    print(f"Error getting EHR data: {e}")
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Warning: Could not retrieve EHR data', 'progress': 20})}\n\n"
            
            # Extract key EHR fields
            ehr_fields = [
                ('patient_name', 'Patient Name'),
                ('patient_dob', 'Date of Birth'),
                ('diagnosis', 'Diagnosis'),
                ('stage', 'Cancer Stage'),
                ('provider_name', 'Ordering Provider'),
                ('facility', 'Facility'),
                ('procedure_date', 'Procedure Date')
            ]
            
            extracted_data = {}
            for i, (field_key, field_name) in enumerate(ehr_fields):
                try:
                    # Simulate EHR extraction
                    if field_key in patient_data:
                        value = patient_data[field_key]
                    else:
                        value = auth.get(field_key, 'Not found in EHR')
                    
                    source = 'EHR System'
                    citation = f"Patient record {patient_mrn}, field: {field_key}"
                    
                    extracted_data[field_key] = {
                        'value': value,
                        'source': source,
                        'citation': citation
                    }
                    
                    yield f"data: {json.dumps({'type': 'ehr_extraction', 'field': field_name, 'value': value, 'source': source, 'citation': citation, 'progress': 30 + (i * 5)})}\n\n"
                    
                except Exception as e:
                    print(f"Error extracting {field_name}: {e}")
                    yield f"data: {json.dumps({'type': 'ehr_extraction', 'field': field_name, 'value': 'Error extracting data', 'source': 'Error', 'citation': str(e), 'progress': 30 + (i * 5)})}\n\n"
            
            # Fill form fields using policy analysis and EHR data
            form_fields = [
                ('patient_name', 'Patient Name', extracted_data.get('patient_name', {}).get('value', '')),
                ('cpt_code', 'CPT Code', cpt_code),
                ('diagnosis', 'Diagnosis', extracted_data.get('diagnosis', {}).get('value', '')),
                ('clinical_indication', 'Clinical Indication', 'Advanced cancer requiring targeted therapy'),
                ('provider_name', 'Ordering Provider', extracted_data.get('provider_name', {}).get('value', '')),
                ('facility', 'Facility', extracted_data.get('facility', {}).get('value', ''))
            ]
            
            for i, (field_key, field_name, value) in enumerate(form_fields):
                try:
                    justification = f"Based on EHR data and policy requirements for {cpt_code}"
                    sources = ['EHR System', 'Policy Analysis']
                    
                    yield f"data: {json.dumps({'type': 'form_field', 'field': field_name, 'value': value, 'justification': justification, 'sources': sources, 'progress': 60 + (i * 5)})}\n\n"
                    
                except Exception as e:
                    print(f"Error filling form field {field_name}: {e}")
                    yield f"data: {json.dumps({'type': 'form_field', 'field': field_name, 'value': 'Error', 'justification': 'Error occurred', 'sources': ['Error'], 'progress': 60 + (i * 5)})}\n\n"
            
            # Create final form result
            form_sections = [
                {
                    'title': 'Patient Information',
                    'fields': [
                        {'label': 'Patient Name', 'value': extracted_data.get('patient_name', {}).get('value', ''), 'sources': ['EHR']},
                        {'label': 'Date of Birth', 'value': extracted_data.get('patient_dob', {}).get('value', ''), 'sources': ['EHR']},
                        {'label': 'MRN', 'value': patient_mrn, 'sources': ['EHR']}
                    ]
                },
                {
                    'title': 'Service Information',
                    'fields': [
                        {'label': 'CPT Code', 'value': cpt_code, 'sources': ['Request']},
                        {'label': 'Diagnosis', 'value': extracted_data.get('diagnosis', {}).get('value', ''), 'sources': ['EHR']},
                        {'label': 'Clinical Indication', 'value': 'Advanced cancer requiring targeted therapy', 'sources': ['Policy Analysis']}
                    ]
                },
                {
                    'title': 'Provider Information',
                    'fields': [
                        {'label': 'Ordering Provider', 'value': extracted_data.get('provider_name', {}).get('value', ''), 'sources': ['EHR']},
                        {'label': 'Facility', 'value': extracted_data.get('facility', {}).get('value', ''), 'sources': ['EHR']}
                    ]
                }
            ]
            
            ehr_citations = [
                {'field': 'Patient Name', 'value': extracted_data.get('patient_name', {}).get('value', ''), 'source': 'EHR System'},
                {'field': 'Diagnosis', 'value': extracted_data.get('diagnosis', {}).get('value', ''), 'source': 'EHR System'},
                {'field': 'Provider', 'value': extracted_data.get('provider_name', {}).get('value', ''), 'source': 'EHR System'}
            ]
            
            policy_references = [
                {'title': 'Medicare Coverage Policy', 'url': 'https://www.cms.gov/medicare-coverage-database', 'relevance': 95},
                {'title': 'Clinical Practice Guidelines', 'url': 'https://www.nccn.org/guidelines', 'relevance': 90},
                {'title': 'FDA Approval Information', 'url': 'https://www.fda.gov/drugs', 'relevance': 85}
            ]
            
            final_result = {
                'completed_fields': len(form_fields),
                'total_fields': len(form_fields),
                'sections': form_sections,
                'ehr_citations': ehr_citations,
                'policy_references': policy_references
            }
            
            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'result': final_result, 'progress': 100})}\n\n"
            
            # Update database
            db.update_prior_auth_status(auth_id, 'completed')
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate_form_stream()), 
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

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