#!/usr/bin/env python3
"""
Test script for PDF export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.pdf_form_filler import PDFFormFiller

def test_pdf_export():
    """Test the PDF export functionality"""
    print("Testing PDF export functionality...")
    
    try:
        # Create test data
        form_data = {
            'h1': {'question': 'Ordered by qualified clinician?', 'answer': 'Yes - Dr. Jordan Rivera, Oncology'},
            'h2': {'question': 'Genetic counseling pre/post?', 'answer': 'No - Not required for cancer testing'},
            'h3': {'question': 'Mutation accepted by societies?', 'answer': 'Yes - NCCN guidelines support testing'},
            'h4': {'question': 'Diagnosable by non-genetic means?', 'answer': 'No - Molecular profiling required for treatment selection'},
            'h5': {'question': 'Test performed previously?', 'answer': 'No'},
            'h6': {'question': 'Specific reason and guidelines?', 'answer': 'NCCN Guidelines v2.2024 - Comprehensive genomic profiling for treatment selection'},
            'h7': {'question': 'Evaluation studies list?', 'answer': 'Pathology report, oncology consultation, molecular testing order attached'},
            'h8': {'question': 'Has clinical features of mutation?', 'answer': 'Yes - Lung cancer with advanced stage'},
            'h9': {'question': 'At direct risk of inheriting?', 'answer': 'No - Somatic testing for treatment selection'},
            'h10': {'question': 'Prospective parent high risk guides reproductive decisions?', 'answer': 'No - Not applicable for cancer treatment'},
            'service_info': {
                'service_type': 'Comprehensive Genomic Profiling',
                'date_of_service': '2024-01-15',
                'type_of_test': 'Gene panel',
                'gene_mutation_tested': 'Comprehensive genomic profiling (334 genes)',
                'icd10_codes': 'C34.90',
                'cpt_codes': '81445'
            },
            'provider_info': {
                'billing_provider': 'Hartford Hospital (Medicaid #123456)',
                'ordering_provider': 'Dr. Jordan Rivera, Oncology (Medicaid #789012)',
                'provider_address': '80 Seymour Street, Hartford, CT 06102'
            }
        }
        
        patient_info = {
            'mrn': '123456789',
            'name': 'John Smith',
            'dob': '1958-03-15',
            'address': '123 Main Street, Hartford, CT 06106'
        }
        
        # Create PDF form filler
        pdf_filler = PDFFormFiller()
        
        # Generate PDF
        print("Generating PDF...")
        pdf_content = pdf_filler.fill_form(form_data, patient_info)
        
        # Generate filename
        filename = pdf_filler.generate_filename(patient_info['name'])
        
        # Save test PDF
        output_path = os.path.join(os.path.dirname(__file__), 'test_output.pdf')
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
        
        print(f"✅ PDF generated successfully!")
        print(f"📄 File saved as: {output_path}")
        print(f"📊 File size: {len(pdf_content)} bytes")
        print(f"🏷️  Generated filename: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PDF export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_export()
    sys.exit(0 if success else 1)
