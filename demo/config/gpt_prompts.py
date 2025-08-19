"""
GPT prompts configuration for enhanced insurance analysis.
Contains all the prompts used for different GPT operations.
"""

def create_medicare_search_prompt(query: str) -> str:
    """
    Create a comprehensive search prompt for all Medicare document types and supporting documents.
    """
    return f"""
    You are a medical policy search assistant. Search for medical policy documents related to: {query}
    
    CRITICAL INSTRUCTIONS:
    1. Use REAL web search to find actual documents
    2. Do NOT hallucinate or create fake URLs, titles, or sources
    3. Only return results from real websites and documents that actually exist
    4. Return results in EXACT JSON format as specified below
    5. If no real results are found, return an empty array: []
    
    SEARCH PRIORITY (in order):
    1. Medicare National Coverage Determinations (NCDs) - site:cms.gov
    2. Medicare Local Coverage Determinations (LCDs) - site:cms.gov  
    3. Medicare Local Coverage Articles (LCAs) - site:cms.gov
    4. Medicare Coverage Database (MCD) - site:cms.gov
    5. Medicare Administrative Contractor (MAC) websites and policies
    6. Medicare Advantage medical policies and coverage determinations
    7. Clinical practice guidelines (NCCN, ASCO, etc.)
    8. FDA approvals, clearances, and companion diagnostics
    9. Professional society guidelines and recommendations
    
    REQUIRED JSON FORMAT:
    You MUST return results in this EXACT JSON format:
    [
        {{
            "title": "Exact document title from the webpage",
            "url": "Full URL to the document",
            "snippet": "Brief description or excerpt from the document",
            "relevance": 85,
            "type": "ncd|lcd|lca|mac_policy|medicare_advantage|clinical_guideline|fda_document|policy_document",
            "source": "Organization name (e.g., CMS, FDA, NCCN, ASCO)"
        }}
    ]
    
    DOCUMENT TYPE MAPPING:
    - "ncd" = National Coverage Determinations
    - "lcd" = Local Coverage Determinations  
    - "lca" = Local Coverage Articles
    - "mac_policy" = Medicare Administrative Contractor policies
    - "medicare_advantage" = Medicare Advantage policies
    - "clinical_guideline" = Clinical practice guidelines
    - "fda_document" = FDA approvals and clearances
    - "policy_document" = Other policy documents
    
    EXAMPLES OF VALID RESULTS:
    [
        {{
            "title": "National Coverage Determination (NCD) for Next Generation Sequencing (NGS) (90.2)",
            "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=372&ncdver=1",
            "snippet": "Medicare covers diagnostic laboratory tests using NGS when performed in a CLIA-certified laboratory",
            "relevance": 95,
            "type": "ncd",
            "source": "CMS"
        }}
    ]
    
    DO NOT:
    - Return markdown links like [title](url)
    - Include explanatory text outside the JSON
    - Create fake or example URLs
    - Return partial or malformed JSON
    
    DO:
    - Return ONLY valid JSON array
    - Use real URLs from actual websites
    - Include accurate titles and descriptions
    - Set appropriate relevance scores (0-100)
    """


def create_general_insurance_search_prompt(query: str) -> str:
    """
    Create a comprehensive search prompt for general insurance documents including Medicaid and commercial insurance.
    """
    return f"""
    You are a medical policy search assistant. Search for medical policy documents related to: {query}
    
    CRITICAL INSTRUCTIONS:
    1. Use REAL web search to find actual documents
    2. Do NOT hallucinate or create fake URLs, titles, or sources
    3. Only return results from real websites and documents that actually exist
    4. Return results in EXACT JSON format as specified below
    5. If no real results are found, return an empty array: []
    
    SEARCH PRIORITY (in order):
    1. Insurance provider medical policies and coverage documents
    2. State Medicaid policies and coverage determinations
    3. Medicaid managed care organization policies
    4. Clinical practice guidelines (NCCN, ASCO, etc.)
    5. FDA approvals, clearances, and companion diagnostics
    6. Professional society guidelines and recommendations
    7. State health department policies
    8. Insurance provider prior authorization forms and requirements
    
    REQUIRED JSON FORMAT:
    You MUST return results in this EXACT JSON format:
    [
        {{
            "title": "Exact document title from the webpage",
            "url": "Full URL to the document",
            "snippet": "Brief description or excerpt from the document",
            "relevance": 85,
            "type": "medicaid_policy|insurance_policy|clinical_guideline|fda_document|policy_document|prior_auth_form",
            "source": "Organization name (e.g., Medicaid, Insurance Provider, FDA, NCCN, ASCO)"
        }}
    ]
    
    DOCUMENT TYPE MAPPING:
    - "medicaid_policy" = Medicaid state policies and coverage determinations
    - "insurance_policy" = Insurance provider medical policies
    - "clinical_guideline" = Clinical practice guidelines
    - "fda_document" = FDA approvals and clearances
    - "policy_document" = Other policy documents
    - "prior_auth_form" = Prior authorization forms and requirements
    
    EXAMPLES OF VALID RESULTS:
    [
        {{
            "title": "Medicaid Genetic Testing Prior Authorization Form",
            "url": "https://portal.ct.gov/dss/health-and-home-care/medical-programs/medicaid-husky-health",
            "snippet": "Connecticut Medicaid prior authorization requirements for genetic testing services",
            "relevance": 95,
            "type": "medicaid_policy",
            "source": "Connecticut Department of Social Services"
        }}
    ]
    
    DO NOT:
    - Return markdown links like [title](url)
    - Include explanatory text outside the JSON
    - Create fake or example URLs
    - Return partial or malformed JSON
    
    DO:
    - Return ONLY valid JSON array
    - Use real URLs from actual websites
    - Include accurate titles and descriptions
    - Set appropriate relevance scores (0-100)
    """


def create_medicare_document_analysis_prompt(search_result: dict) -> str:
    """
    Create an optimized analysis prompt for Medicare documents.
    """
    doc_type = search_result.get('type', 'Unknown')
    title = search_result.get('title', 'Unknown')
    url = search_result.get('url', 'N/A')
    snippet = search_result.get('snippet', 'N/A')
    
    # Medicare-specific analysis instructions
    if doc_type in ['ncd', 'lcd', 'lca']:
        analysis_focus = f"""
        This appears to be a Medicare {doc_type.upper()} document. Pay special attention to:
        - Coverage criteria and medical necessity requirements
        - Specific CPT/HCPCS codes covered
        - Documentation requirements
        - Clinical indications for coverage
        - Limitations and exclusions
        - Effective dates and revision history
        """
    else:
        analysis_focus = """
        Analyze this medical policy document for:
        - Coverage criteria and requirements
        - Medical necessity guidelines
        - Documentation requirements
        - Clinical indications
        """
    
    return f"""
    You are a medical policy document analyzer. Analyze this document and extract structured information:
    
    Document Title: {title}
    URL: {url}
    Document Type: {doc_type.upper() if doc_type in ['ncd', 'lcd', 'lca'] else 'Policy Document'}
    Snippet: {snippet}
    
    {analysis_focus}
    
    CRITICAL INSTRUCTIONS:
    1. Return ONLY valid JSON in the exact format specified below
    2. Do NOT include any explanatory text outside the JSON
    3. Do NOT use markdown formatting
    4. Extract information from the actual document content
    
    REQUIRED JSON FORMAT:
    You MUST return results in this EXACT JSON format:
    {{
        "title": "{title}",
        "url": "{url}",
        "source": "source organization name",
        "document_type": "{doc_type}",
        "requirements": [
            "requirement 1",
            "requirement 2",
            "requirement 3"
        ],
        "evidence_basis": "clinical evidence or rationale for coverage",
        "clinical_criteria": [
            "clinical criterion 1",
            "clinical criterion 2"
        ],
        "coverage_status": "covered|not covered|prior authorization required",
        "cpt_codes": [
            "81455",
            "81450"
        ],
        "documentation_needed": [
            "required document 1",
            "required document 2"
        ],
        "limitations": [
            "limitation 1",
            "limitation 2"
        ],
        "effective_date": "YYYY-MM-DD or N/A",
        "revision_date": "YYYY-MM-DD or N/A"
    }}
    
    EXAMPLE OF VALID RESPONSE:
    {{
        "title": "National Coverage Determination (NCD) for Next Generation Sequencing (NGS) (90.2)",
        "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=372&ncdver=1",
        "source": "CMS",
        "document_type": "ncd",
        "requirements": [
            "Test must be performed in a CLIA-certified laboratory",
            "Patient must have cancer diagnosis",
            "Test must be ordered by treating physician"
        ],
        "evidence_basis": "Based on clinical evidence showing improved outcomes with targeted therapy",
        "clinical_criteria": [
            "Advanced or metastatic cancer",
            "No prior comprehensive NGS testing on same tumor",
            "Results will guide treatment decisions"
        ],
        "coverage_status": "prior authorization required",
        "cpt_codes": ["81455", "81450"],
        "documentation_needed": [
            "Pathology report",
            "Clinical notes",
            "Test order form"
        ],
        "limitations": [
            "Limited to one test per tumor",
            "Must be FDA-approved companion diagnostic"
        ],
        "effective_date": "2018-03-16",
        "revision_date": "2023-01-01"
    }}
    
    DO NOT:
    - Include markdown formatting
    - Add explanatory text outside JSON
    - Use placeholder or example data
    - Return malformed JSON
    
    DO:
    - Extract real information from the document
    - Use exact JSON format specified
    - Include all required fields
    - Use appropriate data types (arrays for lists, strings for text)
    """


def create_medicare_analysis_prompt(
    cpt_code: str, 
    insurance_provider: str, 
    policy_documents: list,
    patient_context: dict = None,
    mac_jurisdiction: dict = None
) -> str:
    """
    Create an enhanced analysis prompt for Medicare documents.
    """
    # Check if any documents are Medicare-specific
    has_medicare_docs = any(
        doc.get('document_type') in ['ncd', 'lcd', 'lca'] 
        for doc in policy_documents
    )
    
    medicare_focus = ""
    if has_medicare_docs:
        medicare_focus = """
        MEDICARE DOCUMENT ANALYSIS FOCUS:
        - Prioritize NCDs over LCDs (NCDs are nationwide, LCDs are local)
        - Consider LCDs only if no applicable NCD exists
        - Pay attention to Medicare Administrative Contractor (MAC) jurisdictions
        - Include Medicare-specific requirements and limitations
        - Consider Medicare medical necessity criteria
        """
    
    return f"""
    You are a medical policy analyst. Analyze the following medical policy documents for CPT code {cpt_code} and insurance provider {insurance_provider}:
    
    Policy Documents:
    {policy_documents}
    
    Patient Context:
    {patient_context or {}}
    
    MAC Jurisdiction:
    {mac_jurisdiction or {}}
    
    {medicare_focus}
    
    CRITICAL INSTRUCTIONS:
    1. Return ONLY valid JSON in the exact format specified below
    2. Do NOT include any explanatory text outside the JSON
    3. Do NOT use markdown formatting
    4. Base analysis on the provided policy documents
    
    REQUIRED JSON FORMAT:
    You MUST return results in this EXACT JSON format:
    {{
        "coverage_status": "covered|not covered|prior authorization required",
        "coverage_details": "detailed explanation of coverage decision",
        "requirements": [
            {{
                "requirement_type": "requirement category name",
                "description": "detailed requirement description",
                "evidence_basis": "clinical evidence or rationale",
                "documentation_needed": [
                    "required document 1",
                    "required document 2"
                ],
                "clinical_criteria": [
                    "clinical criterion 1",
                    "clinical criterion 2"
                ],
                "source_document": "source document title",
                "confidence_score": 0.9
            }}
        ],
        "confidence_score": 0.95,
        "key_findings": [
            "key finding 1",
            "key finding 2"
        ],
        "recommendations": [
            "recommendation 1",
            "recommendation 2"
        ],
        "medicare_specific": {{
            "ncd_applicable": true,
            "lcd_applicable": false,
            "mac_jurisdiction": "MAC jurisdiction name or null",
            "medicare_limitations": [
                "Medicare limitation 1",
                "Medicare limitation 2"
            ]
        }}
    }}
    
    EXAMPLE OF VALID RESPONSE:
    {{
        "coverage_status": "prior authorization required",
        "coverage_details": "CPT 81455 is covered under Medicare with prior authorization when patient meets clinical criteria",
        "requirements": [
            {{
                "requirement_type": "Genetic Counseling",
                "description": "Genetic counseling consultation required before testing",
                "evidence_basis": "Based on Medicare policy requirements for genetic testing",
                "documentation_needed": [
                    "Genetic counseling note",
                    "Counselor credentials"
                ],
                "clinical_criteria": [
                    "Patient has cancer diagnosis",
                    "Test results will guide treatment"
                ],
                "source_document": "NCD 90.2",
                "confidence_score": 0.9
            }}
        ],
        "confidence_score": 0.85,
        "key_findings": [
            "Test requires prior authorization",
            "Genetic counseling documentation needed",
            "Patient meets clinical criteria"
        ],
        "recommendations": [
            "Submit prior authorization request",
            "Include genetic counseling documentation",
            "Provide clinical justification"
        ],
        "medicare_specific": {{
            "ncd_applicable": true,
            "lcd_applicable": false,
            "mac_jurisdiction": null,
            "medicare_limitations": [
                "Limited to one test per tumor",
                "Must be CLIA-certified laboratory"
            ]
        }}
    }}
    
    DO NOT:
    - Include markdown formatting
    - Add explanatory text outside JSON
    - Use placeholder or example data
    - Return malformed JSON
    
    DO:
    - Base analysis on provided policy documents
    - Use exact JSON format specified
    - Include all required fields
    - Use appropriate data types (arrays for lists, strings for text, booleans for true/false)
    """


def create_parsing_agent_prompt(relevant_docs: list, patient_context: dict, cpt_code: str, insurance_provider: str, patient_mrn: str = None) -> str:
    """
    Create prompt for the parsing agent to analyze documents and validate requests.
    """
    # Extract document content for analysis
    doc_content = []
    for doc in relevant_docs[:5]:  # Limit to top 5 most relevant
        # Use full content if available, otherwise fall back to snippet
        content = doc.get('full_content', doc.get('snippet', 'No content available'))
        doc_content.append(f"""
Document: {doc.get('title', 'Unknown')}
URL: {doc.get('url', 'N/A')}
Type: {doc.get('type', 'Unknown')}
Relevance: {doc.get('relevance', 0)}%
Full Content: {content}
""")
    
    # Get patient EHR data if MRN is provided
    patient_ehr_data = ""
    if patient_mrn:
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from backend.mock_ehr_system import MockEHRSystem
            ehr_system = MockEHRSystem()
            ehr_data = ehr_system.get_full_patient_record(patient_mrn)
            
            if ehr_data:
                # Extract relevant patient data for analysis
                patient_ehr_data = f"""
PATIENT EHR DATA (MRN: {patient_mrn}):
Patient Name: {ehr_data.get('patient_admin', {}).get('name', {}).get('given', 'Unknown')} {ehr_data.get('patient_admin', {}).get('name', {}).get('family', 'Unknown')}
Diagnosis: {ehr_data.get('diagnosis_and_stage', {}).get('description', 'Unknown')}
Stage: {ehr_data.get('diagnosis_and_stage', {}).get('stage_group', 'Unknown')}
Ordering Provider: {ehr_data.get('ordering_provider', {}).get('name', 'Unknown')}
Lab Performing: {ehr_data.get('lab_performing', {}).get('lab_name', 'Unknown')}
CLIA Number: {ehr_data.get('lab_performing', {}).get('clia', 'Unknown')}
NPI: {ehr_data.get('lab_performing', {}).get('npi', 'Unknown')}

Genetic Counseling & Consent:
{ehr_data.get('genetics_counseling_and_consent', 'Not available')}

Family History:
{ehr_data.get('family_history', 'Not available')}

Clinical Notes:
"""
                # Add clinical notes
                for note in ehr_data.get('clinical_notes', [])[:3]:  # Limit to first 3 notes
                    patient_ehr_data += f"""
- Type: {note.get('type', 'Unknown')}
  Date: {note.get('date', 'Unknown')}
  Author: {note.get('author', 'Unknown')}
  Content: {note.get('text', 'No content')[:200]}...
"""
        except Exception as e:
            patient_ehr_data = f"Error loading patient EHR data: {str(e)}"
    
    # Create patient context summary
    patient_summary = f"""
Patient Context:
- CPT Code: {cpt_code}
- Insurance Provider: {insurance_provider}
- Has Genetic Counseling: {patient_context.get('has_genetic_counseling', False)}
- Has Family History: {patient_context.get('has_family_history', False)}
- Has Clinical Indication: {patient_context.get('has_clinical_indication', True)}
- Provider Credentials Valid: {patient_context.get('provider_credentials_valid', True)}
- Patient State: {patient_context.get('patient_state', 'Unknown')}
"""
    
    return f"""
You are a medical insurance parsing agent analyzing policy documents for prior authorization requests. 

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON in the exact format specified below
2. Do NOT include any explanatory text outside the JSON
3. Do NOT use markdown formatting
4. Extract SPECIFIC, DETAILED criteria from the policy documents
5. If request is invalid, ALWAYS draft a detailed clinician message

TASK: Analyze the provided policy documents, patient context, and patient EHR data to:

1. **Extract DETAILED Critical Requirements**: 
   - Extract SPECIFIC medical necessity criteria from the documents
   - Include EXACT clinical indications mentioned in policies
   - List SPECIFIC documentation requirements with details
   - Include EXACT CPT codes, diagnosis codes, or other specific requirements

2. **Validate PA Request**: 
   - Check if the clinician's request is valid based on available information
   - Check if all required documentation is present in the patient EHR data
   - Identify any gaps in the request
   - Set is_valid to FALSE if ANY required documentation is missing
   - Set is_valid to TRUE ONLY if ALL required documentation is present

3. **Identify Missing Documents**: 
   - List SPECIFIC documents or information needed
   - Explain WHY each document is required
   - Provide GUIDANCE on how to obtain missing information

4. **Create Detailed Requirements Checklist**: 
   - Create a comprehensive checklist for the determination process
   - Include both clinical and administrative requirements
   - Specify EXACT evidence requirements for each item

5. **Extract Medical Knowledge**: 
   - Extract relevant medical knowledge from the policy documents
   - Identify clinical evidence mentioned in the documents
   - Note any specific medical criteria or guidelines

DOCUMENTS TO ANALYZE:
{chr(10).join(doc_content)}

PATIENT CONTEXT:
{patient_summary}

{patient_ehr_data}

REQUIRED JSON FORMAT:
{{
    "critical_requirements": [
        {{
            "requirement": "Specific requirement name (e.g., 'CLIA Certification', 'Genetic Counseling')",
            "criteria": "DETAILED criteria from policy documents (e.g., 'Laboratory must be CLIA-certified with certificate number. Test must be performed in a laboratory that meets CLIA requirements for high complexity testing.')",
            "documentation_needed": "SPECIFIC documentation required (e.g., 'CLIA certificate with laboratory number, test validation report, laboratory director credentials')",
            "clinical_criteria": "SPECIFIC clinical criteria from policy (e.g., 'Patient must have confirmed cancer diagnosis. Test must be ordered by treating physician. Results must guide treatment decisions.')"
        }}
    ],
    "request_validation": {{
        "is_valid": true/false,
        "missing_documents": [
            "Specific missing document 1",
            "Specific missing document 2"
        ],
        "validation_notes": "Detailed explanation of validation decision"
    }},
    "clinician_message": "DETAILED message to clinician requesting missing information. Include specific documents needed, why they are required, and how to provide them. Format as a professional medical communication.",
    "requirements_checklist": [
        {{
            "category": "Clinical Requirements|Administrative Requirements|Documentation Requirements",
            "items": [
                {{
                    "requirement": "Specific requirement",
                    "evidence_required": "Exact evidence needed",
                    "notes": "Additional notes or guidance"
                }}
            ]
        }}
    ],
    "medical_knowledge": [
        {{
            "topic": "Medical topic (e.g., 'Genetic Testing Indications')",
            "evidence": "Specific evidence from documents",
            "source_document": "Document title",
            "relevance": "High|Medium|Low"
        }}
    ]
}}

EXAMPLE OF DETAILED CRITICAL REQUIREMENTS:
{{
    "requirement": "CLIA Certification",
    "criteria": "Laboratory must be CLIA-certified with certificate number. Test must be performed in a laboratory that meets CLIA requirements for high complexity testing. Laboratory director must be board-certified in appropriate specialty.",
    "documentation_needed": "CLIA certificate with laboratory number, test validation report, laboratory director credentials, quality control documentation",
    "clinical_criteria": "Test must be ordered by treating physician. Patient must have confirmed cancer diagnosis. Test results must be used to guide treatment decisions. Patient must meet specific clinical indications outlined in policy."
}}

EXAMPLE OF DETAILED CLINICIAN MESSAGE:
"Dear Dr. [Provider Name],

Regarding the prior authorization request for [Patient Name] (MRN: [MRN]) for [Test Name] (CPT: [CPT Code]), our review has identified the following missing documentation required by [Insurance Provider]:

1. **CLIA Certification Documentation**: Please provide the laboratory's CLIA certificate number and validation report. This is required to ensure the laboratory meets federal standards for genetic testing.

2. **Genetic Counseling Documentation**: Please provide documentation of genetic counseling consultation, including counselor credentials and date of consultation. This is required by [Insurance Provider] policy for genetic testing coverage.

3. **Physician Order**: Please provide a signed physician order specifying the clinical indication and medical necessity for this test.

Please submit these documents so we can proceed with the prior authorization request. If you have any questions, please contact our prior authorization team.

Thank you,
Prior Authorization Team"

IMPORTANT: Extract SPECIFIC details from the policy documents. Do not use generic statements like "meets medical necessity criteria" - instead extract the EXACT criteria mentioned in the documents.

VALIDATION RULES:
- Set is_valid to FALSE if ANY of these are missing:
  * Genetic counseling documentation (when patient_context shows has_genetic_counseling: false)
  * Family history documentation (when patient_context shows has_family_history: false)
  * Clinical indication documentation (when patient_context shows has_clinical_indication: false)
  * CLIA certification documentation (check if lab_performing.clia is present in patient EHR data)
  * Physician order documentation (check if ordering_provider is present and clinical notes contain physician orders)
  * Any other specific requirements mentioned in policy documents

- Set is_valid to TRUE ONLY if ALL required documentation is present and verified.

IMPORTANT VALIDATION GUIDELINES:
- CLIA Certification: If lab_performing.clia is present in patient EHR data, consider CLIA certification documented
- Physician Order: If ordering_provider is present and clinical notes contain physician orders or medical necessity documentation, consider physician order documented
- Genetic Counseling: If genetics_counseling_and_consent is present OR clinical notes contain genetic counseling documentation, consider genetic counseling documented
- Family History: If family_history is present OR clinical notes mention family history, consider family history documented
- Clinical Indication: If clinical notes contain medical necessity, clinical indication, or treatment planning documentation, consider clinical indication documented
"""


def create_criteria_matching_prompt(requirements_text: str, patient_context: dict) -> str:
    """
    Create criteria matching prompt for checking patient data against insurance requirements.
    """
    return f"""
    Check if the patient meets the following insurance requirements:
    
    Requirements:
    {requirements_text}
    
    Patient Context:
    {patient_context}
    
    Return a JSON object mapping each requirement to true/false:
    {{
        "requirement_name": true/false,
        "requirement_name": true/false
    }}
    
    Consider the patient context carefully and be conservative in your assessment.
    """


def create_recommendations_prompt(
    coverage_info, 
    patient_criteria_match: dict, 
    patient_context: dict = None
) -> str:
    """
    Create recommendations prompt for generating actionable recommendations.
    """
    unmet_criteria = [req for req, met in patient_criteria_match.items() if not met]
    
    # Handle both CoverageAnalysis dataclass and dictionary
    if hasattr(coverage_info, 'coverage_status'):
        # CoverageAnalysis dataclass
        coverage_status = coverage_info.coverage_status
        coverage_details = coverage_info.coverage_details
        requirements = coverage_info.requirements
    else:
        # Dictionary
        coverage_status = coverage_info.get('coverage_status', 'Unknown')
        coverage_details = coverage_info.get('coverage_details', 'Unknown')
        requirements = coverage_info.get('requirements', [])
    
    # Format requirements
    requirements_text = ""
    for req in requirements:
        if hasattr(req, 'requirement_type'):
            # InsuranceRequirement dataclass
            req_type = req.requirement_type
            req_desc = req.description
        else:
            # Dictionary
            req_type = req.get('requirement_type', 'Unknown')
            req_desc = req.get('description', '')
        requirements_text += f"- {req_type}: {req_desc}\n"
    
    return f"""
    Generate actionable recommendations for a prior authorization request based on the following information:
    
    Coverage Status: {coverage_status}
    Coverage Details: {coverage_details}
    
    Requirements:
    {requirements_text}
    
    Patient Criteria Match:
    {patient_criteria_match}
    
    Unmet Criteria:
    {unmet_criteria if unmet_criteria else "All criteria met"}
    
    Patient Context:
    {patient_context or {}}
    
    Provide 5-7 specific, actionable recommendations for completing the prior authorization request.
    Return as a JSON array of strings.
    """
