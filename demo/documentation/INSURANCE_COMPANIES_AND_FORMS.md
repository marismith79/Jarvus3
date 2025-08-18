# Insurance Companies and Prior Authorization Forms

This document lists the insurance companies that have been added to the mock database and their associated prior authorization forms for genetic testing and tumor profiling.

## Insurance Companies in Database

The following insurance companies have been diversified across the patient population in the mock database:

1. **Husky Health CT**
2. **Humana**
3. **UnitedHealthcare**
4. **Aetna**
5. **Kaiser Permanente**
6. **Cigna**

## Prior Authorization Forms and Policies

### Husky Health CT
- **Main Form**: https://www.huskyhealthct.org/providers/provider_postings/provider_forms/Genetic_Testing_Prior_Authorization_Form.pdf
- **Policy Page**: https://www.huskyhealthct.org/providers/provider_postings/policies_procedures/GeneticTestingPolicy.pdf

### Humana
- **Form**: https://docushare-web.apps.external.pioneer.humana.com/Marketing/docushare-app?file=1986712

### UnitedHealthcare
- **BRCA Form**: https://www.baylorgenetics.com/wp-content/uploads/2019/03/baylor-genetics-uhc-brca-form.pdf

### Aetna
- **Main List**: https://www.aetna.com/content/dam/aetna/pdfs/aetnacom/healthcare-professionals/2025_Precert_List.pdf
- **Medical Policy Bulletin**: https://www.aetna.com/health-care-professionals/clinical-policy-bulletins/medical-clinical-policy-bulletins.html#tab_content_section_responsivegrid_responsivegrid_tabs_link_tabs_4
- **Whole Exome Sequencing Form**: https://www.baylorgenetics.com/wp-content/uploads/2024/02/Aetna%20-%20whole-exome-sequencing-precert-form%20%281.24%29.pdf
- **Prior Authorization Form**: https://www.baylorgenetics.com/wp-content/uploads/2019/03/baylor-genetics-aetna-prior-authorization-form.pdf
- **Whole Exome Sequencing Precert Form**: https://www.aetna.com/content/dam/aetna/pdfs/aetnacom/pharmacy-insurance/healthcare-professional/documents/whole-exome-sequencing-precert-form.pdf
- **BRCA Precertification Form**: https://www.aetna.com/content/dam/aetna/pdfs/aetnacom/pharmacy-insurance/healthcare-professional/documents/BRCA-precertification-request-form.pdf

### Kaiser Permanente
- **Genetic Screening Policy**: https://wa-provider.kaiserpermanente.org/static/pdf/hosting/clinical/criteria/pdf/genetic_screening.pdf
- **Genetic Panel Tests**: https://wa-provider.kaiserpermanente.org/static/pdf/hosting/clinical/criteria/pdf/genetic-panel-tests.pdf
- **Next Gen Sequencing**: https://wa-provider.kaiserpermanente.org/static/pdf/hosting/clinical/criteria/pdf/next_gen_sequencing.pdf
- **Cell Free Fetal DNA Analysis**: https://wa-provider.kaiserpermanente.org/static/pdf/hosting/clinical/criteria/pdf/cell_free_fetal_dna_analysis_for_trisomies.pdf
- **Genetic Testing MAS**: https://healthy.kaiserpermanente.org/content/dam/kporg/final/documents/health-plan-documents/notice/utilization-management/genetic-testing-mas-en1.pdf

### Cigna
- **PA List**: https://legacy.cigna.com/static/www-cigna-com/docs/individuals-families/master-precertification-list-for-providers.pdf
- **Genetic Testing Form**: https://www.cigna.com/static/www-cigna-com/docs/gtgc-external-recommendation-form.pdf
- **Genetic Counseling Form**: https://www.baylorgenetics.com/wp-content/uploads/2019/03/baylor-genetics-cigna-genetic-counseling-form.pdf
- **Exome Sequencing Form**: https://www.baylorgenetics.com/wp-content/uploads/2019/03/baylor-genetics-cigna-whole-exome-sequencing-recommendation-form.pdf
- **Cigna MA General Form**: https://medicareproviders.cigna.com/static/medicareproviders-cigna-com/docs/prior-authorization-request-form.pdf

## Database Updates

### Changes Made
1. **Insurance Diversification**: All patients now have insurance from one of the six companies listed above
2. **Connecticut Addresses**: All patients now have addresses in Connecticut cities
3. **Plan Types**: Appropriate plan types assigned based on insurance company (e.g., HUSKY A/B/C/D for Husky Health CT)
4. **Member IDs**: New unique member IDs generated for each patient

### Patient Distribution
The database contains 10 patients with the following insurance distribution:
- Aetna: 1 patient
- UnitedHealthcare: 2 patients  
- Cigna: 2 patients
- Husky Health CT: 2 patients
- Humana: 1 patient
- Kaiser Permanente: 2 patients

### Connecticut Cities Used
Patients are distributed across various Connecticut cities including:
- New Haven, Hartford, Stamford, Bridgeport, Waterbury
- Norwalk, Danbury, New Britain, Bristol, Meriden
- West Haven, Milford, Middletown, Torrington, New London
- Stratford, Shelton, Vernon, Wallingford, East Hartford

## Notes
- All patients maintain their original genetic testing and tumor profiling cases
- Only the insurance provider, address, and associated identifiers were updated
- The original database has been backed up as `mock_ehr_pa_oncology_genomics_with_notes_and_fhir_backup.json`
