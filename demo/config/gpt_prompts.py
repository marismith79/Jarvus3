"""
GPT prompts configuration for enhanced insurance analysis.
Contains all the prompts used for different GPT operations.
"""

def create_medicare_search_prompt(query: str) -> str:
    """
    Create a comprehensive search prompt for all Medicare document types and supporting documents.
    """
    return f"""
    Search for medical policy documents related to: {query}
    
    IMPORTANT: Use REAL web search to find actual documents. Do NOT hallucinate or create fake URLs, titles, or sources. Only return results from real websites and documents that actually exist.
    
    COMPREHENSIVE SOURCE TYPES (in order of importance):
    
    PRIMARY MEDICARE DOCUMENTS:
    1. Medicare National Coverage Determinations (NCDs) - site:cms.gov
    2. Medicare Local Coverage Determinations (LCDs) - site:cms.gov  
    3. Medicare Local Coverage Articles (LCAs) - site:cms.gov
    4. Medicare Coverage Database (MCD) - site:cms.gov
    5. Medicare Administrative Contractor (MAC) websites and policies
    
    MEDICARE ADVANTAGE DOCUMENTS:
    6. Medicare Advantage medical policies and coverage determinations
    7. Medicare Advantage clinical policies and utilization management
    
    CLINICAL AND EVIDENCE DOCUMENTS:
    8. Clinical practice guidelines (NCCN, ASCO, etc.)
    9. Evidence-based clinical studies and trials
    10. Technology assessments and clinical evidence reviews
    11. Medical necessity criteria and clinical rationale
    
    REGULATORY AND COMPLIANCE DOCUMENTS:
    12. FDA approvals, clearances, and companion diagnostics
    13. Regulatory requirements and compliance policies
    14. Billing and coding guidelines
    15. Documentation requirements and standards
    
    COST AND UTILIZATION DOCUMENTS:
    16. Cost-effectiveness analyses and budget impact studies
    17. Utilization management policies and reviews
    18. Medical policy cost analyses
    
    PROFESSIONAL SOCIETY GUIDELINES:
    19. NCCN Clinical Practice Guidelines
    20. ASCO Clinical Practice Guidelines
    21. Other professional society recommendations
    
    SEARCH FOCUS:
    - Use REAL web search to find actual documents
    - Prioritize official Medicare coverage policies (NCDs, LCDs, LCAs)
    - Include Medicare Administrative Contractor specific policies
    - Find clinical evidence and medical necessity criteria
    - Search for FDA approvals and regulatory requirements
    - Include professional society guidelines and recommendations
    - Look for cost-effectiveness and utilization data
    - Find billing and coding requirements
    - Only return results from real, existing websites and documents
    
    Return results as a JSON array with fields: title, url, snippet, relevance (0-100), type, source.
    
    DOCUMENT TYPES TO USE:
    - "ncd" for National Coverage Determinations
    - "lcd" for Local Coverage Determinations  
    - "lca" for Local Coverage Articles
    - "mac_policy" for Medicare Administrative Contractor policies
    - "medicare_advantage" for Medicare Advantage policies
    - "clinical_guideline" for clinical practice guidelines
    - "fda_document" for FDA approvals and clearances
    - "clinical_study" for clinical trials and evidence
    - "cost_analysis" for cost-effectiveness studies
    - "utilization_policy" for utilization management
    - "billing_guideline" for billing and coding requirements
    - "regulatory_document" for regulatory requirements
    - "policy_document" for other policy documents
    - "coverage_determination" for coverage decisions
    
    CRITICAL REQUIREMENTS:
    - Use REAL web search to find actual documents
    - Do NOT create fake URLs, titles, or sources
    - Only return results from real, existing websites
    - Prioritize official sources: CMS.gov, MAC websites, FDA.gov, professional society websites
    - Include both current and recent historical documents for comprehensive coverage analysis
    - If no real results are found, return an empty array rather than fake data
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
    Analyze this medical policy document and extract structured information:
    
    Document Title: {title}
    URL: {url}
    Document Type: {doc_type.upper() if doc_type in ['ncd', 'lcd', 'lca'] else 'Policy Document'}
    Snippet: {snippet}
    
    {analysis_focus}
    
    Please extract the following information and return as JSON:
    {{
        "title": "document title",
        "url": "document url",
        "source": "source organization",
        "document_type": "{doc_type}",
        "requirements": ["list of specific requirements"],
        "evidence_basis": "clinical evidence or rationale",
        "clinical_criteria": ["list of clinical criteria"],
        "coverage_status": "covered/not covered/prior authorization required",
        "cpt_codes": ["relevant CPT codes"],
        "documentation_needed": ["list of required documentation"],
        "limitations": ["coverage limitations or exclusions"],
        "effective_date": "document effective date if available",
        "revision_date": "last revision date if available"
    }}
    
    For Medicare documents, be especially thorough in extracting:
    - Specific coverage criteria
    - Medical necessity requirements
    - Required documentation
    - Clinical indications
    - Limitations and exclusions
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
    Analyze the following medical policy documents for CPT code {cpt_code} and insurance provider {insurance_provider}:
    
    Policy Documents:
    {policy_documents}
    
    Patient Context:
    {patient_context or {}}
    
    MAC Jurisdiction:
    {mac_jurisdiction or {}}
    
    {medicare_focus}
    
    Please provide a comprehensive analysis and return as JSON:
    {{
        "coverage_status": "covered/not covered/prior authorization required",
        "coverage_details": "detailed explanation of coverage",
        "requirements": [
            {{
                "requirement_type": "specific requirement name",
                "description": "detailed description",
                "evidence_basis": "clinical evidence or rationale",
                "documentation_needed": ["list of required documents"],
                "clinical_criteria": ["list of clinical criteria"],
                "source_document": "source document title",
                "confidence_score": 0.9
            }}
        ],
        "confidence_score": 0.95,
        "key_findings": ["list of key findings"],
        "recommendations": ["list of recommendations"],
        "medicare_specific": {{
            "ncd_applicable": true/false,
            "lcd_applicable": true/false,
            "mac_jurisdiction": "MAC jurisdiction if applicable",
            "medicare_limitations": ["Medicare-specific limitations"]
        }}
    }}
    
    Focus on extracting specific requirements, clinical criteria, and providing actionable recommendations.
    For Medicare documents, ensure compliance with Medicare policies and requirements.
    """


def create_parsing_agent_prompt(relevant_docs: list, patient_context: dict, cpt_code: str, insurance_provider: str) -> str:
    """
    Create prompt for the parsing agent to analyze documents and validate requests.
    """
    # Extract document content for analysis
    doc_content = []
    for doc in relevant_docs[:5]:  # Limit to top 5 most relevant
        doc_content.append(f"""
Document: {doc.get('title', 'Unknown')}
URL: {doc.get('url', 'N/A')}
Type: {doc.get('type', 'Unknown')}
Relevance: {doc.get('relevance', 0)}%
Content: {doc.get('snippet', 'No content available')}
""")
    
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

TASK: Analyze the provided policy documents and patient context to:

1. **Extract Critical Requirements Checklist**: Identify all critical requirements for coverage approval
2. **Validate PA Request**: Check if the clinician's request is valid based on available documentation
3. **Identify Missing Documents**: If request is invalid, identify what additional documents are needed
4. **Create Requirements Checklist**: Generate a comprehensive checklist for determination
5. **Extract Medical Knowledge**: Identify relevant medical knowledge and evidence from the documents

DOCUMENTS TO ANALYZE:
{chr(10).join(doc_content)}

PATIENT CONTEXT:
{patient_summary}

ANALYSIS REQUIREMENTS:

1. **Critical Requirements Checklist**:
   - List each critical requirement with specific criteria
   - Include documentation requirements
   - Specify clinical criteria that must be met

2. **Request Validation**:
   - Determine if the PA request is valid based on available information
   - Check if all required documentation is present
   - Identify any gaps in the request

3. **Missing Documents** (if request is invalid):
   - List specific documents or information needed
   - Explain why each document is required
   - Provide guidance on how to obtain missing information

4. **Requirements Checklist for Determination**:
   - Create a comprehensive checklist for the determination process
   - Include both clinical and administrative requirements
   - Specify evidence requirements for each item

5. **Medical Knowledge from Evidence**:
   - Extract relevant medical knowledge from the policy documents
   - Identify clinical evidence mentioned in the documents
   - Note any specific medical criteria or guidelines

RESPONSE FORMAT (JSON):
{{
    "critical_requirements": [
        {{
            "requirement": "string",
            "criteria": "string",
            "documentation_needed": "string",
            "clinical_criteria": "string"
        }}
    ],
    "request_validation": {{
        "is_valid": boolean,
        "missing_documents": ["string"],
        "validation_notes": "string"
    }},
    "clinician_message": "string (message to clinician if request is invalid)",
    "requirements_checklist": [
        {{
            "category": "string",
            "items": [
                {{
                    "requirement": "string",
                    "evidence_required": "string",
                    "notes": "string"
                }}
            ]
        }}
    ],
    "medical_knowledge": [
        {{
            "topic": "string",
            "evidence": "string",
            "source_document": "string",
            "relevance": "string"
        }}
    ]
}}

Analyze the documents thoroughly and provide a comprehensive response following the JSON format above.
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
    coverage_info: dict, 
    patient_criteria_match: dict, 
    patient_context: dict = None
) -> str:
    """
    Create recommendations prompt for generating actionable recommendations.
    """
    unmet_criteria = [req for req, met in patient_criteria_match.items() if not met]
    
    return f"""
    Generate actionable recommendations for a prior authorization request based on the following information:
    
    Coverage Status: {coverage_info.get('coverage_status', 'Unknown')}
    Coverage Details: {coverage_info.get('coverage_details', 'Unknown')}
    
    Requirements:
    {chr(10).join([f"- {req.get('requirement_type', 'Unknown')}: {req.get('description', '')}" for req in coverage_info.get('requirements', [])])}
    
    Patient Criteria Match:
    {patient_criteria_match}
    
    Unmet Criteria:
    {unmet_criteria if unmet_criteria else "All criteria met"}
    
    Patient Context:
    {patient_context or {}}
    
    Provide 5-7 specific, actionable recommendations for completing the prior authorization request.
    Return as a JSON array of strings.
    """
