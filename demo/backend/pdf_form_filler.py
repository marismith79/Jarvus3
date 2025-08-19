import os
import json
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io

class PDFFormFiller:
    def __init__(self):
        self.pdf_template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'db', 
            'Medicaid Genetic Testing PA Form.pdf'
        )
        
    def fill_form(self, form_data: Dict[str, Any], patient_info: Dict[str, Any]) -> bytes:
        """
        Fill the Medicaid Genetic Testing PA Form PDF with form data
        
        Args:
            form_data: Dictionary containing form question answers
            patient_info: Dictionary containing patient information
            
        Returns:
            bytes: PDF file content
        """
        try:
            # Read the template PDF
            reader = PdfReader(self.pdf_template_path)
            writer = PdfWriter()
            
            # Get the first page
            page = reader.pages[0]
            writer.add_page(page)
            
            # Create a new PDF with form data
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Set font and size
            can.setFont("Helvetica", 10)
            
            # Map form data to PDF coordinates
            field_mappings = self._get_field_mappings()
            
            # Fill in patient information
            self._fill_patient_info(can, patient_info)
            
            # Fill in form answers
            self._fill_form_answers(can, form_data, field_mappings)
            
            can.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            
            # Create a new PDF with the form data
            form_pdf = PdfReader(packet)
            form_page = form_pdf.pages[0]
            
            # Merge the form data with the template
            page.merge_page(form_page)
            
            # Write the final PDF
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Error filling PDF form: {e}")
            raise
    
    def _get_field_mappings(self) -> Dict[str, tuple]:
        """
        Get field mappings for the Medicaid form
        Returns coordinates (x, y) for each form field
        """
        return {
            # Member Information Section
            'member_id': (1.5*inch, 9.5*inch),
            'member_name': (1.5*inch, 9.2*inch),
            'date_of_birth': (1.5*inch, 8.9*inch),
            'address': (1.5*inch, 8.6*inch),
            
            # Requested Testing Section
            'test_name': (1.5*inch, 7.8*inch),
            'date_of_service': (1.5*inch, 7.5*inch),
            'type_of_test': (1.5*inch, 7.2*inch),
            'gene_mutation_tested': (1.5*inch, 6.9*inch),
            'icd10_codes': (1.5*inch, 6.6*inch),
            'cpt_codes': (1.5*inch, 6.3*inch),
            
            # Form Questions Section
            'ordered_by_qualified_clinician': (1.5*inch, 5.5*inch),
            'genetic_counseling': (1.5*inch, 5.2*inch),
            'mutation_accepted_by_societies': (1.5*inch, 4.9*inch),
            'diagnosable_by_non_genetic_means': (1.5*inch, 4.6*inch),
            'test_performed_previously': (1.5*inch, 4.3*inch),
            'specific_reason_and_guidelines': (1.5*inch, 4.0*inch),
            'evaluation_studies_list': (1.5*inch, 3.7*inch),
            
            # Clinical Presentation Section
            'has_clinical_features': (1.5*inch, 3.0*inch),
            'at_direct_risk': (1.5*inch, 2.7*inch),
            'prospective_parent_high_risk': (1.5*inch, 2.4*inch),
            
            # Provider Information Section
            'billing_provider': (1.5*inch, 1.8*inch),
            'ordering_provider': (1.5*inch, 1.5*inch),
            'provider_address': (1.5*inch, 1.2*inch),
        }
    
    def _fill_patient_info(self, canvas_obj, patient_info: Dict[str, Any]):
        """Fill in patient information section"""
        # Member ID
        canvas_obj.drawString(1.5*inch, 9.5*inch, str(patient_info.get('mrn', '')))
        
        # Member Name
        canvas_obj.drawString(1.5*inch, 9.2*inch, str(patient_info.get('name', '')))
        
        # Date of Birth
        canvas_obj.drawString(1.5*inch, 8.9*inch, str(patient_info.get('dob', '')))
        
        # Address
        canvas_obj.drawString(1.5*inch, 8.6*inch, str(patient_info.get('address', '123 Main Street, Hartford, CT 06106')))
    
    def _fill_form_answers(self, canvas_obj, form_data: Dict[str, Any], field_mappings: Dict[str, tuple]):
        """Fill in form answers based on the form data"""
        
        # Map form question IDs to field names
        question_mappings = {
            'h1': 'ordered_by_qualified_clinician',
            'h2': 'genetic_counseling', 
            'h3': 'mutation_accepted_by_societies',
            'h4': 'diagnosable_by_non_genetic_means',
            'h5': 'test_performed_previously',
            'h6': 'specific_reason_and_guidelines',
            'h7': 'evaluation_studies_list',
            'h8': 'has_clinical_features',
            'h9': 'at_direct_risk',
            'h10': 'prospective_parent_high_risk',
        }
        
        # Fill in form answers
        for question_id, answer_data in form_data.items():
            if question_id in question_mappings:
                field_name = question_mappings[question_id]
                if field_name in field_mappings:
                    x, y = field_mappings[field_name]
                    answer = answer_data.get('answer', '') if isinstance(answer_data, dict) else str(answer_data)
                    canvas_obj.drawString(x, y, str(answer))
        
        # Fill in service information
        service_info = form_data.get('service_info', {})
        if service_info:
            canvas_obj.drawString(1.5*inch, 7.8*inch, str(service_info.get('service_type', '')))
            canvas_obj.drawString(1.5*inch, 7.5*inch, str(service_info.get('date_of_service', '')))
            canvas_obj.drawString(1.5*inch, 7.2*inch, str(service_info.get('type_of_test', 'Gene panel')))
            canvas_obj.drawString(1.5*inch, 6.9*inch, str(service_info.get('gene_mutation_tested', 'Comprehensive genomic profiling (334 genes)')))
            canvas_obj.drawString(1.5*inch, 6.6*inch, str(service_info.get('icd10_codes', '')))
            canvas_obj.drawString(1.5*inch, 6.3*inch, str(service_info.get('cpt_codes', '')))
        
        # Fill in provider information
        provider_info = form_data.get('provider_info', {})
        if provider_info:
            canvas_obj.drawString(1.5*inch, 1.8*inch, str(provider_info.get('billing_provider', 'Hartford Hospital (Medicaid #123456)')))
            canvas_obj.drawString(1.5*inch, 1.5*inch, str(provider_info.get('ordering_provider', 'Dr. Jordan Rivera, Oncology (Medicaid #789012)')))
            canvas_obj.drawString(1.5*inch, 1.2*inch, str(provider_info.get('provider_address', '80 Seymour Street, Hartford, CT 06102')))
    
    def generate_filename(self, patient_name: str, date: str = None) -> str:
        """Generate a filename for the filled PDF"""
        if not date:
            from datetime import datetime
            date = datetime.now().strftime('%Y%m%d')
        
        # Clean patient name for filename
        clean_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')
        
        return f"Medicaid_Genetic_Testing_PA_Form_{clean_name}_{date}.pdf"
