"""
MAC (Medicare Administrative Contractor) jurisdictions configuration.
Contains all MAC jurisdictions and their associated states and information.
"""

MAC_JURISDICTIONS = {
    "jurisdiction_a": {
        "name": "Noridian Healthcare Solutions",
        "states": ["CT", "DE", "DC", "ME", "MD", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction A - DME MAC"
    },
    "jurisdiction_b": {
        "name": "CGS Administrators",
        "states": ["IL", "IN", "KY", "MI", "MN", "OH", "WI"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction B - DME MAC"
    },
    "jurisdiction_c": {
        "name": "CGS Administrators",
        "states": ["AL", "AR", "CO", "FL", "GA", "LA", "MS", "NM", "NC", "OK", "SC", "TN", "TX", "VA", "WV"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction C - DME MAC"
    },
    "jurisdiction_d": {
        "name": "Noridian Healthcare Solutions",
        "states": ["AK", "AZ", "CA", "HI", "ID", "IA", "KS", "MO", "MT", "NE", "NV", "ND", "OR", "SD", "UT", "WA", "WY"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction D - DME MAC"
    },
    "jurisdiction_e": {
        "name": "CGS Administrators",
        "states": ["CA", "HI", "NV"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction E - DME MAC"
    },
    "jurisdiction_f": {
        "name": "CGS Administrators",
        "states": ["AL", "GA", "TN"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction F - DME MAC"
    },
    "jurisdiction_g": {
        "name": "CGS Administrators",
        "states": ["FL", "PR", "VI"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction G - DME MAC"
    },
    "jurisdiction_h": {
        "name": "CGS Administrators",
        "states": ["CA"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction H - DME MAC"
    },
    "jurisdiction_j": {
        "name": "Palmetto GBA",
        "states": ["AL", "GA", "NC", "SC", "TN", "VA", "WV"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction J - Part A/B MAC"
    },
    "jurisdiction_k": {
        "name": "National Government Services",
        "states": ["CT", "ME", "MA", "NH", "RI", "VT"],
        "website": "https://www.ngsmedicare.com",
        "description": "Jurisdiction K - Part A/B MAC"
    },
    "jurisdiction_l": {
        "name": "First Coast Service Options",
        "states": ["FL"],
        "website": "https://www.fcso.com",
        "description": "Jurisdiction L - Part A/B MAC"
    },
    "jurisdiction_m": {
        "name": "CGS Administrators",
        "states": ["IN", "KY"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction M - Part A/B MAC"
    },
    "jurisdiction_n": {
        "name": "Wisconsin Physicians Service",
        "states": ["IL", "MI", "MN", "WI"],
        "website": "https://www.wpsgha.com",
        "description": "Jurisdiction N - Part A/B MAC"
    },
    "jurisdiction_p": {
        "name": "Palmetto GBA",
        "states": ["CA", "HI", "NV"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction P - Part A/B MAC"
    },
    "jurisdiction_r": {
        "name": "Novitas Solutions",
        "states": ["AR", "CO", "LA", "MS", "NM", "OK", "TX"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction R - Part A/B MAC"
    },
    "jurisdiction_s": {
        "name": "Palmetto GBA",
        "states": ["AZ", "MT", "ND", "SD", "UT", "WY"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction S - Part A/B MAC"
    },
    "jurisdiction_t": {
        "name": "First Coast Service Options",
        "states": ["FL", "PR", "VI"],
        "website": "https://www.fcso.com",
        "description": "Jurisdiction T - Part A/B MAC"
    },
    "jurisdiction_u": {
        "name": "Noridian Healthcare Solutions",
        "states": ["AK", "ID", "OR", "WA"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction U - Part A/B MAC"
    },
    "jurisdiction_v": {
        "name": "Noridian Healthcare Solutions",
        "states": ["CA"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction V - Part A/B MAC"
    },
    "jurisdiction_w": {
        "name": "Noridian Healthcare Solutions",
        "states": ["IA", "KS", "MO", "NE"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction W - Part A/B MAC"
    },
    "jurisdiction_x": {
        "name": "Novitas Solutions",
        "states": ["DE", "DC", "MD", "NJ", "PA"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction X - Part A/B MAC"
    },
    "jurisdiction_y": {
        "name": "Novitas Solutions",
        "states": ["NC", "SC", "VA", "WV"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction Y - Part A/B MAC"
    },
    "jurisdiction_z": {
        "name": "Wisconsin Physicians Service",
        "states": ["IL", "MI", "MN", "WI"],
        "website": "https://www.wpsgha.com",
        "description": "Jurisdiction Z - Part A/B MAC"
    }
}

# State to full name mapping for address parsing
STATE_MAPPING = {
    'new york': 'NY',
    'michigan': 'MI',
    'connecticut': 'CT',
    'california': 'CA',
    'texas': 'TX',
    'florida': 'FL',
    'illinois': 'IL',
    'pennsylvania': 'PA',
    'ohio': 'OH',
    'georgia': 'GA',
    'north carolina': 'NC',
    'virginia': 'VA',
    'washington': 'WA',
    'oregon': 'OR',
    'colorado': 'CO',
    'arizona': 'AZ',
    'nevada': 'NV',
    'utah': 'UT',
    'montana': 'MT',
    'wyoming': 'WY',
    'idaho': 'ID',
    'alaska': 'AK',
    'hawaii': 'HI',
    'new mexico': 'NM',
    'oklahoma': 'OK',
    'arkansas': 'AR',
    'louisiana': 'LA',
    'mississippi': 'MS',
    'alabama': 'AL',
    'tennessee': 'TN',
    'kentucky': 'KY',
    'indiana': 'IN',
    'wisconsin': 'WI',
    'minnesota': 'MN',
    'iowa': 'IA',
    'missouri': 'MO',
    'kansas': 'KS',
    'nebraska': 'NE',
    'south dakota': 'SD',
    'north dakota': 'ND',
    'maine': 'ME',
    'new hampshire': 'NH',
    'vermont': 'VT',
    'massachusetts': 'MA',
    'rhode island': 'RI',
    'new jersey': 'NJ',
    'delaware': 'DE',
    'maryland': 'MD',
    'west virginia': 'WV',
    'south carolina': 'SC'
}
