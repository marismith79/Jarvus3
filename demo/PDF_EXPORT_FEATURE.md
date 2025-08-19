# PDF Export Feature

## Overview

The PDF export feature allows users to automatically populate and download the Medicaid Genetic Testing PA Form PDF with data that the agent fills in during the form processing section.

## Features

- **Automatic PDF Population**: The system automatically fills the Medicaid Genetic Testing PA Form PDF with:
  - Patient information (name, MRN, DOB, address)
  - Service information (test type, CPT codes, ICD-10 codes)
  - Form question answers populated by the AI agent
  - Provider information (billing and ordering providers)

- **Smart Data Mapping**: Maps form question IDs to specific PDF field locations
- **Fallback Support**: If PDF generation fails, falls back to JSON export
- **User-Friendly Interface**: Shows loading states and success/error messages
- **Automatic Filename Generation**: Creates descriptive filenames with patient name and date

## Technical Implementation

### Backend Components

1. **PDFFormFiller Class** (`backend/pdf_form_filler.py`)
   - Handles PDF template reading and form field mapping
   - Uses PyPDF2 and ReportLab for PDF manipulation
   - Maps form question IDs to PDF coordinates
   - Generates properly formatted filenames

2. **API Endpoint** (`/api/prior-auths/<auth_id>/export-pdf`)
   - Accepts form data via POST request
   - Retrieves patient and service information from database
   - Calls PDFFormFiller to generate populated PDF
   - Returns PDF file for download

### Frontend Components

1. **Updated Export Button** (`dashboard.js`)
   - Changed from JSON export to PDF export
   - Shows loading state during PDF generation
   - Handles success and error states
   - Provides fallback to JSON if PDF fails

2. **Enhanced UI** (`dashboard.html`, `dashboard.css`)
   - Updated button text and icon to indicate PDF export
   - Added alert message styling for user feedback
   - Improved visual feedback during export process

## Usage

1. **Complete Form Processing**: Run the agent processing to populate all form questions
2. **Review Answers**: Verify that all form fields are correctly populated
3. **Export PDF**: Click the "Export PDF Form" button
4. **Download**: The populated PDF will automatically download to your computer

## File Structure

```
demo/
├── backend/
│   └── pdf_form_filler.py          # PDF form filling logic
├── db/
│   └── Medicaid Genetic Testing PA Form.pdf  # PDF template
├── static/
│   ├── js/
│   │   └── dashboard.js            # Updated export function
│   └── css/
│       └── dashboard.css           # Alert styling
├── templates/
│   └── dashboard.html              # Updated button text
├── requirements.txt                # Added PDF libraries
├── test_pdf_export.py             # Test script
└── PDF_EXPORT_FEATURE.md          # This documentation
```

## Dependencies

The following Python packages are required for PDF functionality:

```txt
PyPDF2==3.0.1
reportlab==4.0.7
```

## Testing

Run the test script to verify PDF functionality:

```bash
cd demo
python test_pdf_export.py
```

This will generate a test PDF file (`test_output.pdf`) to verify the functionality works correctly.

## Field Mappings

The system maps form question IDs to specific PDF field locations:

| Question ID | PDF Field | Description |
|-------------|-----------|-------------|
| h1 | ordered_by_qualified_clinician | Ordered by qualified clinician? |
| h2 | genetic_counseling | Genetic counseling pre/post? |
| h3 | mutation_accepted_by_societies | Mutation accepted by societies? |
| h4 | diagnosable_by_non_genetic_means | Diagnosable by non-genetic means? |
| h5 | test_performed_previously | Test performed previously? |
| h6 | specific_reason_and_guidelines | Specific reason and guidelines? |
| h7 | evaluation_studies_list | Evaluation studies list? |
| h8 | has_clinical_features | Has clinical features of mutation? |
| h9 | at_direct_risk | At direct risk of inheriting? |
| h10 | prospective_parent_high_risk | Prospective parent high risk guides reproductive decisions? |

## Error Handling

- **PDF Generation Errors**: If PDF generation fails, the system falls back to JSON export
- **Missing Data**: Handles missing patient or service information gracefully
- **Network Issues**: Provides clear error messages for API failures
- **File System Errors**: Handles file creation and download issues

## Future Enhancements

Potential improvements for the PDF export feature:

1. **Multiple Form Templates**: Support for different insurance company forms
2. **Custom Field Mapping**: Allow users to customize field positions
3. **Digital Signatures**: Add support for digital signatures on forms
4. **Batch Export**: Export multiple forms at once
5. **Form Validation**: Validate form completeness before export
6. **Preview Mode**: Show PDF preview before download
