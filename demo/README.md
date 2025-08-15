# AI Agent Prior Authorization Demo

## Overview

This demo showcases an AI agent that automates the prior authorization process for hospitals. The system demonstrates how AI can streamline the complex workflow of obtaining insurance approval for medical procedures while maintaining human oversight and ensuring compliance.

## Key Features

### 🤖 AI Agent Automation Workflow
- **4-Step Automation Process**: Insurance coverage & requirements analysis (merged), screening, data extraction, and form completion
- **Real-time Streaming**: Watch the AI agent work through each step with streaming text and visual feedback
- **Human Oversight**: Built-in checkpoints for human review and intervention
- **Non-Hallucinating Design**: Agent asks for help when uncertain or encounters issues
- **GPT-5 Enhanced Analysis**: Real-time insurance policy search and analysis

### 📊 Interactive Dashboard
- **Work Queue Management**: View and manage prior authorization requests
- **Progress Tracking**: Real-time progress bars and step indicators
- **Filtering & Search**: Find specific requests by patient, provider, or step
- **Status Management**: Track requests through different automation states

### 🏥 Mock EHR Integration
- **Comprehensive Patient Data**: Realistic patient demographics, diagnoses, and medical history
- **Clinical Documents**: Progress notes, lab results, imaging reports, and treatment plans
- **Family History**: Detailed family cancer history for genetic testing scenarios
- **Document Search**: Search through patient documents with citations

### 🔍 Enhanced GPT-5 Integration (Real)
- **Real GPT-5 Search Mode**: Uses actual GPT-5 API to search insurance portals for requirements
- **Live Document Analysis**: Extracts requirements from real policy documents
- **Intelligent Coverage Validation**: Validates CPT codes and clinical criteria with GPT-5 reasoning
- **Smart Form Requirements**: Identifies required documentation and forms with high accuracy
- **Fallback Support**: Gracefully handles API failures with intelligent fallback methods

### 📋 Medicaid Husky Form Integration
- **Form Population**: Automatically fills out Medicaid Husky forms for genetic testing
- **Data Validation**: Ensures all required fields are completed
- **Document Attachments**: Links supporting documentation with citations
- **Human Review**: Final form review before submission

## Demo Scenarios

### Scenario 1: Complete Automation
- **Patient**: John Smith (MRN001) - BRCA1/BRCA2 Genetic Testing
- **Insurance**: Original Medicare
- **Outcome**: Full automation with successful form completion

### Scenario 2: Missing Documentation
- **Patient**: Sarah Johnson (MRN002) - Lynch Syndrome Testing
- **Insurance**: Humana Medicare Advantage
- **Outcome**: Agent detects missing genetic counseling note and requests clinician input

### Scenario 3: Complex Case
- **Patient**: Michael Brown (MRN003) - Comprehensive Tumor Profiling
- **Insurance**: UnitedHealthcare Medicare Advantage
- **Outcome**: Agent processes complex oncology case with multiple data sources

### Scenario 4: Treatment Monitoring
- **Patient**: Lisa Anderson (MRN006) - FoundationOne CDx
- **Insurance**: Original Medicare
- **Outcome**: Agent handles advanced cancer case with treatment monitoring

### Scenario 5: Liquid Biopsy
- **Patient**: Robert Taylor (MRN007) - Guardant360 Liquid Biopsy
- **Insurance**: Anthem Medicare Advantage
- **Outcome**: Agent processes liquid biopsy for treatment monitoring

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Flask
- SQLite3 (included with Python)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd demo
   ```

2. **Install dependencies**
   ```bash
   pip install -r demo/requirements.txt
   ```

3. **Set up GPT-5 API key** (recommended for full functionality)
   ```bash
   # Run the setup script to configure GPT-5 API key
   python setup_gpt5.py
   
   # Or manually create .env file
   echo "GPT5_API_KEY=your_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Test the enhanced functionality**
   ```bash
   # Run the test script to verify GPT-5 integration
   python test_enhanced_insurance.py
   ```

6. **Access the demo**
   - Open your browser and go to `http://localhost:5001`
   - The dashboard will load with mock prior authorization data
   - Use the enhanced insurance analysis with real GPT-5 search mode

## How to Use the Demo

### 1. Explore the Dashboard
- View the main dashboard showing all prior authorization requests
- Use the tabs to filter by status: All Requests, In Progress, Human Review, Needs Input, Completed
- Use the search and filter options to find specific requests

### 2. Start Automation
- Select one or more prior authorization requests
- Click the "Start Automation" button
- Watch the interactive popup as the AI agent works through each step

### 3. Observe the Automation Process
- **Step 1 - Coverage Determination**: Agent checks if the CPT code is covered
- **Step 2 - Insurance Documentation**: Agent searches for requirements using GPT-5
- **Step 3 - Screening**: Agent analyzes request notes and EHR data
- **Step 4 - Data Extraction**: Agent extracts relevant data with citations
- **Step 5 - Form Completion**: Agent fills out the Medicaid Husky form

### 4. Human Intervention Points
- **Missing Documentation**: Agent pauses and requests clinician input
- **Review Required**: Human can approve, request changes, or send to clinician
- **EPIC Integration**: Agent can send messages to clinicians via EPIC

### 5. View Results
- See the completed form with all extracted data
- Review citations and data sources
- Understand the automation workflow

## Technical Architecture

### Frontend
- **HTML/CSS/JavaScript**: Modern, responsive dashboard
- **Real-time Updates**: Streaming text and progress indicators
- **Interactive Modals**: Step-by-step automation visualization

### Backend
- **Flask**: Lightweight web framework
- **SQLite**: In-memory database for demo data
- **Mock Systems**: EHR and GPT-5 integration simulation

### Data Flow
1. **User Interface**: Dashboard displays prior authorization requests
2. **Automation Trigger**: User selects requests and starts automation
3. **Step Execution**: AI agent processes each step with visual feedback
4. **Data Integration**: Mock EHR and GPT-5 systems provide data
5. **Human Review**: Checkpoints for human oversight and intervention
6. **Form Completion**: Final form with all extracted data

## Mock Data Structure

### Patient Data
- **Demographics**: Name, DOB, gender, MRN
- **Insurance**: Provider information and coverage details
- **Medical History**: Diagnoses, medications, allergies
- **Family History**: Cancer history for genetic testing scenarios

### Clinical Documents
- **Progress Notes**: Clinician assessments and recommendations
- **Lab Results**: Blood work and diagnostic tests
- **Imaging Reports**: CT scans, MRIs, and other imaging
- **Treatment Plans**: Chemotherapy, surgery, and other treatments

### Insurance Policies
- **Coverage Rules**: CPT code coverage and requirements
- **Documentation Requirements**: Required forms and supporting documents
- **Provider Networks**: Network requirements and restrictions

## Customization

### Adding New Patients
1. Edit `mock_ehr_system.py` to add new patient data
2. Update the database schema in `database.py` if needed
3. Add corresponding prior authorization requests

### Modifying Insurance Policies
1. Edit `gpt5_integration.py` to update insurance policies
2. Add new CPT codes and coverage rules
3. Update form requirements and documentation needs

### Changing Automation Steps
1. Modify the automation workflow in the dashboard JavaScript
2. Update step definitions and execution logic
3. Add new human intervention points as needed

## Production Considerations

### Security
- **HIPAA Compliance**: All patient data should be encrypted
- **Access Control**: Role-based permissions for different user types
- **Audit Logging**: Complete audit trail for all actions

### Scalability
- **Database**: Use PostgreSQL or similar for production
- **Caching**: Implement Redis for session management
- **Load Balancing**: Multiple application instances for high availability

### Integration
- **Real EHR**: Replace mock EHR with actual EPIC or Cerner integration
- **GPT-5 API**: Implement actual OpenAI API calls
- **Insurance Portals**: Real-time integration with insurance provider portals

## Troubleshooting

### Common Issues

1. **Application won't start**
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed
   - Check port 5001 is available

2. **No data appears**
   - Refresh the page
   - Check browser console for JavaScript errors
   - Verify database initialization

3. **Automation popup doesn't work**
   - Check browser console for errors
   - Ensure JavaScript is enabled
   - Try a different browser

### Debug Mode
- Run with `python app.py --debug` for detailed logging
- Check browser developer tools for frontend issues
- Review Flask logs for backend errors

## Support

For questions or issues with the demo:
- Check the troubleshooting section above
- Review the code comments for implementation details
- Contact the development team for technical support

## License

This demo is provided for educational and demonstration purposes. Please ensure compliance with all applicable healthcare regulations when implementing in production environments.