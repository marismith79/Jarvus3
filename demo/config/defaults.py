"""
Default values and fallback data configuration for enhanced insurance analysis.
Contains default values used when GPT responses fail or are unavailable.
"""

# Default requirements when no policy documents are found
DEFAULT_REQUIREMENTS = [
    {
        "requirement_type": "Genetic counselor consultation required",
        "description": "Requirement for genetic counselor consultation",
        "evidence_basis": "Based on clinical studies and medical literature",
        "documentation_needed": ["Genetic counselor consultation documentation"],
        "clinical_criteria": ["High-risk patient population", "Appropriate clinical indication"],
        "source_document": "Medical Policy Document",
        "confidence_score": 0.9
    },
    {
        "requirement_type": "Family history documentation",
        "description": "Requirement for family history documentation",
        "evidence_basis": "Based on clinical studies and medical literature",
        "documentation_needed": ["Family history documentation"],
        "clinical_criteria": ["High-risk patient population", "Appropriate clinical indication"],
        "source_document": "Medical Policy Document",
        "confidence_score": 0.9
    },
    {
        "requirement_type": "Clinical indication documentation",
        "description": "Requirement for clinical indication documentation",
        "evidence_basis": "Based on clinical studies and medical literature",
        "documentation_needed": ["Clinical indication documentation"],
        "clinical_criteria": ["High-risk patient population", "Appropriate clinical indication"],
        "source_document": "Medical Policy Document",
        "confidence_score": 0.9
    },
    {
        "requirement_type": "Provider credentials verification",
        "description": "Requirement for provider credentials verification",
        "evidence_basis": "Based on clinical studies and medical literature",
        "documentation_needed": ["Provider credentials verification"],
        "clinical_criteria": ["High-risk patient population", "Appropriate clinical indication"],
        "source_document": "Medical Policy Document",
        "confidence_score": 0.9
    }
]

# Default clinical criteria
DEFAULT_CLINICAL_CRITERIA = [
    "High-risk patient population",
    "Appropriate clinical indication",
    "Qualified provider"
]

# Default recommendations
DEFAULT_RECOMMENDATIONS = [
    "Ensure all required documentation is complete and current",
    "Verify provider credentials and network participation",
    "Include clinical justification for the requested service",
    "Submit prior authorization request with all supporting documentation"
]

# Default document information
DEFAULT_DOCUMENT_INFO = {
    "title": "",
    "url": "",
    "source": "Unknown",
    "requirements": [
        "Genetic counselor consultation required",
        "Family history documentation",
        "Clinical indication documentation",
        "Provider credentials verification"
    ],
    "evidence_basis": "Based on clinical studies and medical literature",
    "clinical_criteria": [
        "High-risk patient population",
        "Appropriate clinical indication",
        "Qualified provider"
    ],
    "coverage_status": "Covered with prior authorization",
    "cpt_codes": [],
    "documentation_needed": []
}

# Default parsing agent result
DEFAULT_PARSING_RESULT = {
    'critical_requirements': [
        {
            'requirement': 'Medical necessity documentation',
            'criteria': 'Clinical indication must be documented with specific details from policy documents',
            'documentation_needed': 'Physician notes, clinical documentation, and policy-specific requirements',
            'clinical_criteria': 'Appropriate clinical indication as defined in policy documents'
        }
    ],
    'request_validation': {
        'is_valid': False,  # Default to invalid to ensure proper validation
        'missing_documents': [
            'Detailed medical necessity documentation',
            'Policy-specific clinical criteria documentation'
        ],
        'validation_notes': 'Parsing agent unable to validate request - additional documentation required'
    },
    'clinician_message': 'Dear Provider,\n\nOur analysis of your prior authorization request indicates that additional documentation is required to proceed. Please provide:\n\n1. Detailed medical necessity documentation with specific clinical criteria\n2. Policy-specific requirements documentation\n3. Any additional clinical evidence required by the insurance policy\n\nPlease submit these documents so we can complete the prior authorization process.\n\nThank you,\nPrior Authorization Team',
    'requirements_checklist': [
        {
            'category': 'Clinical Requirements',
            'items': [
                {
                    'requirement': 'Medical necessity',
                    'evidence_required': 'Detailed clinical documentation',
                    'notes': 'Must demonstrate specific clinical indication as per policy'
                }
            ]
        }
    ],
    'medical_knowledge': [
        {
            'topic': 'General coverage',
            'evidence': 'Standard medical necessity criteria apply',
            'source_document': 'Policy guidelines',
            'relevance': 'Standard'
        }
    ]
}

# Default coverage analysis
def get_default_coverage_analysis(cpt_code: str, insurance_provider: str, mac_jurisdiction: dict = None) -> dict:
    """
    Get default coverage analysis structure.
    """
    return {
        "cpt_code": cpt_code,
        "insurance_provider": insurance_provider,
        "coverage_status": "Covered with prior authorization",
        "coverage_details": f"CPT code {cpt_code} is covered under {insurance_provider} with prior authorization requirements.",
        "requirements": DEFAULT_REQUIREMENTS,
        "patient_criteria_match": {},
        "confidence_score": 0.8,
        "search_sources": [],
        "recommendations": DEFAULT_RECOMMENDATIONS,
        "mac_jurisdiction": mac_jurisdiction["name"] if mac_jurisdiction else None,
        "ncd_applicable": False,
        "lcd_applicable": False
    }

# Default criteria matching
def get_default_criteria_match(requirements: list, patient_context: dict) -> dict:
    """
    Get default criteria matching based on patient context.
    """
    criteria_match = {}
    for req in requirements:
        if isinstance(req, dict):
            req_type = req.get('requirement_type', '')
        else:
            req_type = req.requirement_type if hasattr(req, 'requirement_type') else str(req)
            
        if "genetic counselor" in req_type.lower():
            criteria_match[req_type] = patient_context.get('has_genetic_counseling', False)
        elif "family history" in req_type.lower():
            criteria_match[req_type] = patient_context.get('has_family_history', False)
        elif "clinical indication" in req_type.lower():
            criteria_match[req_type] = patient_context.get('has_clinical_indication', True)
        elif "provider credentials" in req_type.lower():
            criteria_match[req_type] = patient_context.get('provider_credentials_valid', True)
        else:
            criteria_match[req_type] = True
    return criteria_match
