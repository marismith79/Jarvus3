"""
MAC (Medicare Administrative Contractor) jurisdictions configuration.
Contains all MAC jurisdictions and their associated states and information.
"""

MAC_JURISDICTIONS = {
    "jurisdiction_a": {
        "name": "Noridian Healthcare Solutions",
        "states": ["CT", "DE", "DC", "ME", "MD", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction A - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://med.noridianmedicare.com/web/jea/topics/genetic-testing",
            "molecular_diagnostics": "https://med.noridianmedicare.com/web/jea/topics/molecular-diagnostics",
            "lcd_search": "https://med.noridianmedicare.com/web/jea/local-coverage-determinations",
            "ncd_search": "https://med.noridianmedicare.com/web/jea/national-coverage-determinations",
            "coverage_database": "https://med.noridianmedicare.com/web/jea/coverage-database"
        }
    },
    "jurisdiction_b": {
        "name": "CGS Administrators",
        "states": ["IL", "IN", "KY", "MI", "MN", "OH", "WI"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction B - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_c": {
        "name": "CGS Administrators",
        "states": ["AL", "AR", "CO", "FL", "GA", "LA", "MS", "NM", "NC", "OK", "SC", "TN", "TX", "VA", "WV"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction C - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_d": {
        "name": "Noridian Healthcare Solutions",
        "states": ["AK", "AZ", "CA", "HI", "ID", "IA", "KS", "MO", "MT", "NE", "NV", "ND", "OR", "SD", "UT", "WA", "WY"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction D - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://med.noridianmedicare.com/web/jea/topics/genetic-testing",
            "molecular_diagnostics": "https://med.noridianmedicare.com/web/jea/topics/molecular-diagnostics",
            "lcd_search": "https://med.noridianmedicare.com/web/jea/local-coverage-determinations",
            "ncd_search": "https://med.noridianmedicare.com/web/jea/national-coverage-determinations",
            "coverage_database": "https://med.noridianmedicare.com/web/jea/coverage-database"
        }
    },
    "jurisdiction_e": {
        "name": "CGS Administrators",
        "states": ["CA", "HI", "NV"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction E - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_f": {
        "name": "CGS Administrators",
        "states": ["AL", "GA", "TN"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction F - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_g": {
        "name": "CGS Administrators",
        "states": ["FL", "PR", "VI"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction G - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_h": {
        "name": "CGS Administrators",
        "states": ["CA"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction H - DME MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_j": {
        "name": "Palmetto GBA",
        "states": ["AL", "GA", "NC", "SC", "TN", "VA", "WV"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction J - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "molecular_diagnostics": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "lcd_search": "https://www.palmettogba.com/palmetto/providers.nsf/lcds",
            "ncd_search": "https://www.palmettogba.com/palmetto/providers.nsf/ncds",
            "coverage_database": "https://www.palmettogba.com/palmetto/providers.nsf/coverage"
        }
    },
    "jurisdiction_k": {
        "name": "National Government Services",
        "states": ["CT", "ME", "MA", "NH", "RI", "VT"],
        "website": "https://www.ngsmedicare.com",
        "description": "Jurisdiction K - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.ngsmedicare.com/ngsmedicare/parta/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.ngsmedicare.com/ngsmedicare/parta/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.ngsmedicare.com/ngsmedicare/parta/policies/lcds",
            "ncd_search": "https://www.ngsmedicare.com/ngsmedicare/parta/policies/ncds",
            "coverage_database": "https://www.ngsmedicare.com/ngsmedicare/parta/policies"
        }
    },
    "jurisdiction_l": {
        "name": "First Coast Service Options",
        "states": ["FL"],
        "website": "https://www.fcso.com",
        "description": "Jurisdiction L - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.fcso.com/Providers/PartA/Policy/LCDs/Genetic-Testing",
            "molecular_diagnostics": "https://www.fcso.com/Providers/PartA/Policy/LCDs/Molecular-Diagnostics",
            "lcd_search": "https://www.fcso.com/Providers/PartA/Policy/LCDs",
            "ncd_search": "https://www.fcso.com/Providers/PartA/Policy/NCDs",
            "coverage_database": "https://www.fcso.com/Providers/PartA/Policy"
        }
    },
    "jurisdiction_m": {
        "name": "CGS Administrators",
        "states": ["IN", "KY"],
        "website": "https://www.cgsmedicare.com",
        "description": "Jurisdiction M - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.cgsmedicare.com/parta/policies/lcds/genetic-testing.html",
            "molecular_diagnostics": "https://www.cgsmedicare.com/parta/policies/lcds/molecular-diagnostics.html",
            "lcd_search": "https://www.cgsmedicare.com/parta/policies/lcds/",
            "ncd_search": "https://www.cgsmedicare.com/parta/policies/ncds/",
            "coverage_database": "https://www.cgsmedicare.com/parta/policies/"
        }
    },
    "jurisdiction_n": {
        "name": "Wisconsin Physicians Service",
        "states": ["IL", "MI", "MN", "WI"],
        "website": "https://www.wpsgha.com",
        "description": "Jurisdiction N - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds",
            "ncd_search": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/ncds",
            "coverage_database": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies"
        }
    },
    "jurisdiction_p": {
        "name": "Palmetto GBA",
        "states": ["CA", "HI", "NV"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction P - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "molecular_diagnostics": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "lcd_search": "https://www.palmettogba.com/palmetto/providers.nsf/lcds",
            "ncd_search": "https://www.palmettogba.com/palmetto/providers.nsf/ncds",
            "coverage_database": "https://www.palmettogba.com/palmetto/providers.nsf/coverage"
        }
    },
    "jurisdiction_r": {
        "name": "Novitas Solutions",
        "states": ["AR", "CO", "LA", "MS", "NM", "OK", "TX"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction R - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.novitas-solutions.com/parta/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.novitas-solutions.com/parta/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.novitas-solutions.com/parta/policies/lcds",
            "ncd_search": "https://www.novitas-solutions.com/parta/policies/ncds",
            "coverage_database": "https://www.novitas-solutions.com/parta/policies"
        }
    },
    "jurisdiction_s": {
        "name": "Palmetto GBA",
        "states": ["AZ", "MT", "ND", "SD", "UT", "WY"],
        "website": "https://www.palmettogba.com",
        "description": "Jurisdiction S - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "molecular_diagnostics": "https://www.palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
            "lcd_search": "https://www.palmettogba.com/palmetto/providers.nsf/lcds",
            "ncd_search": "https://www.palmettogba.com/palmetto/providers.nsf/ncds",
            "coverage_database": "https://www.palmettogba.com/palmetto/providers.nsf/coverage"
        }
    },
    "jurisdiction_t": {
        "name": "First Coast Service Options",
        "states": ["FL", "PR", "VI"],
        "website": "https://www.fcso.com",
        "description": "Jurisdiction T - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.fcso.com/Providers/PartA/Policy/LCDs/Genetic-Testing",
            "molecular_diagnostics": "https://www.fcso.com/Providers/PartA/Policy/LCDs/Molecular-Diagnostics",
            "lcd_search": "https://www.fcso.com/Providers/PartA/Policy/LCDs",
            "ncd_search": "https://www.fcso.com/Providers/PartA/Policy/NCDs",
            "coverage_database": "https://www.fcso.com/Providers/PartA/Policy"
        }
    },
    "jurisdiction_u": {
        "name": "Noridian Healthcare Solutions",
        "states": ["AK", "ID", "OR", "WA"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction U - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://med.noridianmedicare.com/web/jea/topics/genetic-testing",
            "molecular_diagnostics": "https://med.noridianmedicare.com/web/jea/topics/molecular-diagnostics",
            "lcd_search": "https://med.noridianmedicare.com/web/jea/local-coverage-determinations",
            "ncd_search": "https://med.noridianmedicare.com/web/jea/national-coverage-determinations",
            "coverage_database": "https://med.noridianmedicare.com/web/jea/coverage-database"
        }
    },
    "jurisdiction_v": {
        "name": "Noridian Healthcare Solutions",
        "states": ["CA"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction V - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://med.noridianmedicare.com/web/jea/topics/genetic-testing",
            "molecular_diagnostics": "https://med.noridianmedicare.com/web/jea/topics/molecular-diagnostics",
            "lcd_search": "https://med.noridianmedicare.com/web/jea/local-coverage-determinations",
            "ncd_search": "https://med.noridianmedicare.com/web/jea/national-coverage-determinations",
            "coverage_database": "https://med.noridianmedicare.com/web/jea/coverage-database"
        }
    },
    "jurisdiction_w": {
        "name": "Noridian Healthcare Solutions",
        "states": ["IA", "KS", "MO", "NE"],
        "website": "https://med.noridianmedicare.com",
        "description": "Jurisdiction W - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://med.noridianmedicare.com/web/jea/topics/genetic-testing",
            "molecular_diagnostics": "https://med.noridianmedicare.com/web/jea/topics/molecular-diagnostics",
            "lcd_search": "https://med.noridianmedicare.com/web/jea/local-coverage-determinations",
            "ncd_search": "https://med.noridianmedicare.com/web/jea/national-coverage-determinations",
            "coverage_database": "https://med.noridianmedicare.com/web/jea/coverage-database"
        }
    },
    "jurisdiction_x": {
        "name": "Novitas Solutions",
        "states": ["DE", "DC", "MD", "NJ", "PA"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction X - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.novitas-solutions.com/parta/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.novitas-solutions.com/parta/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.novitas-solutions.com/parta/policies/lcds",
            "ncd_search": "https://www.novitas-solutions.com/parta/policies/ncds",
            "coverage_database": "https://www.novitas-solutions.com/parta/policies"
        }
    },
    "jurisdiction_y": {
        "name": "Novitas Solutions",
        "states": ["NC", "SC", "VA", "WV"],
        "website": "https://www.novitas-solutions.com",
        "description": "Jurisdiction Y - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.novitas-solutions.com/parta/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.novitas-solutions.com/parta/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.novitas-solutions.com/parta/policies/lcds",
            "ncd_search": "https://www.novitas-solutions.com/parta/policies/ncds",
            "coverage_database": "https://www.novitas-solutions.com/parta/policies"
        }
    },
    "jurisdiction_z": {
        "name": "Wisconsin Physicians Service",
        "states": ["IL", "MI", "MN", "WI"],
        "website": "https://www.wpsgha.com",
        "description": "Jurisdiction Z - Part A/B MAC",
        "policy_urls": {
            "genetic_testing": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds/genetic-testing",
            "molecular_diagnostics": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds/molecular-diagnostics",
            "lcd_search": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/lcds",
            "ncd_search": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies/ncds",
            "coverage_database": "https://www.wpsgha.com/wps/portal/mac/site/claims/part-a/policies"
        }
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

# CPT-specific policy URL database for direct access to high-value policy pages
CPT_POLICY_URLS = {
    "81455": [
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=290",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.2",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.3",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.4",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.5",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.6",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.7",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.8",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.9",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.10"
    ],
    "81220": [
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.11",
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.12"
    ],
    "81329": [
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.13"
    ],
    "81528": [
        "https://www.cms.gov/medicare-coverage-database/view/ncacal-decision-memo.aspx?proposed=N&NCAId=90.14"
    ]
}

# Direct URLs to high-value policy pages for immediate access
DIRECT_POLICY_URLS = [
    "https://www.cms.gov/medicare-coverage-database/search/search.aspx",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.2",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.3",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.4",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.5",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.6",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.7",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.8",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.9",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.10",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.11",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.12",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.13",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.14",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.15",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.16",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.17",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.18",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.19",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.20",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.21",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.22",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.23",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.24",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.25",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.26",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.27",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.28",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.29",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.30",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.31",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.32",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.33",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.34",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.35",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.36",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.37",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.38",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.39",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.40",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.41",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.42",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.43",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.44",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.45",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.46",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.47",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.48",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.49",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.50",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.51",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.52",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.53",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.54",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.55",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.56",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.57",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.58",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.59",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.60",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.61",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.62",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.63",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.64",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.65",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.66",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.67",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.68",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.69",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.70",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.71",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.72",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.73",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.74",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.75",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.76",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.77",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.78",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.79",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.80",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.81",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.82",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.83",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.84",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.85",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.86",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.87",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.88",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.89",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.90",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.91",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.92",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.93",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.94",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.95",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.96",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.97",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.98",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.99",
    "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=90.100",
    "https://palmettogba.com/palmetto/providers.nsf/files/MolDx_Overview/$File/MolDx_Overview.pdf",
    "https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/companion-diagnostic-devices",
    "https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/breakthrough-devices-program",
    "https://www.nccn.org/guidelines/category_1",
    "https://www.asco.org/practice-patients/guidelines",
    "https://www.uptodate.com/contents/next-generation-dna-sequencing-ngs-principles-and-clinical-applications"
]

MEDICAID_POLICY_URLS = {
    "connecticut": {
        "provider_name": "HUSKY Health",
        "state": "CT",
        "genetic_testing_policy": "https://www.huskyhealthct.org/providers/provider_postings/policies_procedures/GeneticTestingPolicy.pdf",
        "lab_benefits_grid": "https://www.huskyhealthct.org/providers/provider_postings/benefits_grids/Lab_Grid.pdf",
        "physician_benefits_grid": "https://www.huskyhealthct.org/providers/provider_postings/benefits_grids/Physician_Grid.pdf",
        "authorization_phone": "800-440-5071",
        "authorization_fax": "203-265-3994",
        "member_services": "800-859-9889",
        "website": "https://www.huskyhealthct.org",
        "policy_urls": {
            "genetic_testing": "https://www.huskyhealthct.org/providers/provider_postings/policies_procedures/GeneticTestingPolicy.pdf",
            "lab_benefits": "https://www.huskyhealthct.org/providers/provider_postings/benefits_grids/Lab_Grid.pdf",
            "physician_benefits": "https://www.huskyhealthct.org/providers/provider_postings/benefits_grids/Physician_Grid.pdf",
            "fee_schedules": "https://www.ctdssmap.com/ctportal/Information/Download/Download.aspx",
            "provider_manual": "https://www.ctdssmap.com/ctportal/Information/Provider%20Manual/Provider%20Manual.aspx",
            "lcd_lookup": "https://www.cms.gov/medicare-coverage-database/search/search.aspx?list_type=ncd&state=CT&contractor=all&ncd_id=90.2&ncd_id=90.3&ncd_id=90.4&ncd_id=90.5&ncd_id=90.6&ncd_id=90.7&ncd_id=90.8&ncd_id=90.9&ncd_id=90.10&ncd_id=90.11&ncd_id=90.12&ncd_id=90.13&ncd_id=90.14&ncd_id=90.15&ncd_id=90.16&ncd_id=90.17&ncd_id=90.18&ncd_id=90.19&ncd_id=90.20&ncd_id=90.21&ncd_id=90.22&ncd_id=90.23&ncd_id=90.24&ncd_id=90.25&ncd_id=90.26&ncd_id=90.27&ncd_id=90.28&ncd_id=90.29&ncd_id=90.30&ncd_id=90.31&ncd_id=90.32&ncd_id=90.33&ncd_id=90.34&ncd_id=90.35&ncd_id=90.36&ncd_id=90.37&ncd_id=90.38&ncd_id=90.39&ncd_id=90.40&ncd_id=90.41&ncd_id=90.42&ncd_id=90.43&ncd_id=90.44&ncd_id=90.45&ncd_id=90.46&ncd_id=90.47&ncd_id=90.48&ncd_id=90.49&ncd_id=90.50&ncd_id=90.51&ncd_id=90.52&ncd_id=90.53&ncd_id=90.54&ncd_id=90.55&ncd_id=90.56&ncd_id=90.57&ncd_id=90.58&ncd_id=90.59&ncd_id=90.60&ncd_id=90.61&ncd_id=90.62&ncd_id=90.63&ncd_id=90.64&ncd_id=90.65&ncd_id=90.66&ncd_id=90.67&ncd_id=90.68&ncd_id=90.69&ncd_id=90.70&ncd_id=90.71&ncd_id=90.72&ncd_id=90.73&ncd_id=90.74&ncd_id=90.75&ncd_id=90.76&ncd_id=90.77&ncd_id=90.78&ncd_id=90.79&ncd_id=90.80&ncd_id=90.81&ncd_id=90.82&ncd_id=90.83&ncd_id=90.84&ncd_id=90.85&ncd_id=90.86&ncd_id=90.87&ncd_id=90.88&ncd_id=90.89&ncd_id=90.90&ncd_id=90.91&ncd_id=90.92&ncd_id=90.93&ncd_id=90.94&ncd_id=90.95&ncd_id=90.96&ncd_id=90.97&ncd_id=90.98&ncd_id=90.99&ncd_id=90.100&bc=0",
            "genetic_testing_criteria": "https://www.cms.gov/medicare-coverage-database/search/search.aspx?list_type=lcd&state=CT&contractor=all&keyword=genetic+testing&bc=0",
            "molecular_diagnostics_criteria": "https://www.cms.gov/medicare-coverage-database/search/search.aspx?list_type=lcd&state=CT&contractor=all&keyword=molecular+diagnostics&bc=0",
            "dss_fee_schedule_instructions": "https://www.ctdssmap.com/ctportal/Information/Download/Download.aspx"
        }
    }
    # Can add other states' Medicaid programs here later
}
