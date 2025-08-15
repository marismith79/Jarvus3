# EPIC API Simulation

This document describes the EPIC API simulation system that has been implemented to replace the hardcoded EHR data with a more realistic production-like approach.

## Overview

The EPIC API simulation mimics the behavior of EPIC's FHIR API endpoints, allowing the application to pull patient data in a way that closely resembles how it would work in production. Instead of using hardcoded JSON files, all data is now stored in a SQLite database and accessed through simulated EPIC FHIR API calls.

## Architecture

### Components

1. **EpicAPISimulation** (`epic_api_simulation.py`)
   - Simulates EPIC FHIR API endpoints
   - Handles authentication and API calls
   - Converts database data to FHIR resources
   - Includes realistic API latency and error simulation

2. **Enhanced Database Schema** (`database.py`)
   - Multiple tables for different types of patient data
   - Normalized structure for efficient querying
   - Foreign key relationships for data integrity

3. **Updated API Endpoints** (`app.py`)
   - New EPIC-style FHIR endpoints
   - Legacy endpoints for backward compatibility
   - Proper error handling and response formatting

## Database Schema

The database now includes the following tables:

- **patients**: Patient demographic and administrative data
- **lab_results**: Laboratory test results
- **clinical_documents**: Clinical notes, reports, and documents
- **patient_conditions**: Patient diagnoses and conditions
- **patient_procedures**: Medical procedures performed
- **family_history**: Family medical history
- **imaging_reports**: Radiology and imaging reports
- **treatment_history**: Treatment history and medications
- **prior_auths**: Prior authorization requests (existing)

## EPIC FHIR API Endpoints

### Patient Data
- `GET /api/epic/Patient/{mrn}` - Get patient by MRN
- `GET /api/epic/Patient?name={name}` - Search patients by name
- `GET /api/epic/Patient?identifier={mrn}` - Search patients by identifier

### Clinical Data
- `GET /api/epic/Observation?patient={patient_id}` - Get lab results and observations
- `GET /api/epic/DocumentReference?patient={patient_id}` - Get clinical documents
- `GET /api/epic/Condition?patient={patient_id}` - Get patient conditions/diagnoses
- `GET /api/epic/Procedure?patient={patient_id}` - Get patient procedures
- `GET /api/epic/FamilyMemberHistory?patient={patient_id}` - Get family history

### Query Parameters
- `patient`: Patient identifier (MRN)
- `category`: For observations (e.g., "laboratory", "vital-signs")
- `type`: For documents (e.g., "Pathology Report", "Clinical Note")
- `name`: For patient search
- `identifier`: For patient search by MRN

## FHIR Resource Format

All endpoints return data in FHIR Bundle format:

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 1,
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "patient-1",
        "identifier": [{"value": "MRN001"}],
        "name": [{"text": "John Smith"}],
        "birthDate": "1985-03-15",
        "gender": "male"
      }
    }
  ]
}
```

## Legacy Endpoints

For backward compatibility, the following legacy endpoints are still available:

- `GET /api/ehr/patient/{mrn}` - Redirects to EPIC Patient endpoint
- `GET /api/ehr/patient/{mrn}/documents` - Redirects to EPIC DocumentReference endpoint
- `GET /api/ehr/patient/{mrn}/lab-results` - Redirects to EPIC Observation endpoint
- `GET /api/ehr/patient/{mrn}/family-history` - Redirects to EPIC FamilyMemberHistory endpoint
- `GET /api/ehr/patient/{mrn}/clinical-summary` - Comprehensive patient summary

## Production Migration

To migrate to production EPIC API:

1. **Update Configuration**
   ```python
   # In epic_api_simulation.py
   base_url = "https://fhir.epic.com/api/FHIR/R4"  # Production EPIC URL
   api_key = os.getenv('EPIC_API_KEY')  # Production API key
   client_id = os.getenv('EPIC_CLIENT_ID')  # Production client ID
   ```

2. **Enable Real HTTP Requests**
   ```python
   # Uncomment and modify the _make_epic_request method
   headers = {
       'Authorization': f'Bearer {self._get_access_token()}',
       'Epic-Client-ID': self.client_id,
       'Content-Type': 'application/fhir+json'
   }
   response = requests.get(f"{self.base_url}/{endpoint}", headers=headers, params=params)
   ```

3. **Add Authentication**
   - Implement OAuth2 token management
   - Handle token refresh
   - Add proper error handling for authentication failures

4. **Update Error Handling**
   - Handle network timeouts
   - Implement retry logic
   - Add proper logging for API calls

## Testing

Use the provided test script to verify the EPIC API simulation:

```bash
cd demo
python test_epic_api.py
```

This will test all endpoints and verify that data is being retrieved correctly from the database.

## Database Reset

To reset the database with the new schema:

```bash
curl -X POST http://localhost:5001/api/reset-database
```

This will:
1. Delete the existing database file
2. Create new tables with the enhanced schema
3. Load realistic data from the JSON file into all tables

## Benefits

1. **Production-Ready**: Simulates real EPIC API behavior
2. **Scalable**: Database-based approach supports larger datasets
3. **Maintainable**: Clean separation between data storage and API simulation
4. **Realistic**: Includes API latency, error simulation, and proper FHIR formatting
5. **Backward Compatible**: Legacy endpoints ensure existing functionality continues to work

## Future Enhancements

1. **Caching**: Implement caching for frequently accessed data
2. **Pagination**: Add support for large result sets
3. **Filtering**: Add more sophisticated query parameters
4. **Real-time Updates**: Implement webhooks for real-time data updates
5. **Audit Logging**: Track all API calls for compliance
