import sqlite3
import json
import os
from datetime import datetime, timedelta
import threading
import random

class PriorAuthDatabase:
    def __init__(self):
        self.db_path = 'demo.db'
        self._init_db()
    
    def get_connection(self):
        """Get database connection with thread safety"""
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """Initialize database with realistic data from JSON file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prior_auths'")
        if cursor.fetchone():
            return  # Tables already exist
        
        # Create prior_auths table
        cursor.execute('''
            CREATE TABLE prior_auths (
                id INTEGER PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_mrn TEXT NOT NULL,
                patient_dob TEXT,
                patient_gender TEXT,
                insurance_provider TEXT NOT NULL,
                service_type TEXT NOT NULL,
                cpt_code TEXT,
                diagnosis TEXT,
                treatment_history TEXT,
                allergies TEXT,
                procedure_date TEXT,
                status TEXT NOT NULL,
                current_step INTEGER DEFAULT 1,
                step_details TEXT,
                automation_status TEXT DEFAULT 'pending',
                created_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                assigned_to TEXT,
                notes TEXT,
                clinical_urgency TEXT,
                insurance_requirements TEXT,
                ehr_documents TEXT,
                last_updated TEXT NOT NULL
            )
        ''')
        
        # Create patients table
        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                mrn TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                dob TEXT,
                gender TEXT,
                race TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                insurance_provider TEXT,
                insurance_plan TEXT,
                member_id TEXT,
                diagnosis TEXT,
                icd10 TEXT,
                stage TEXT,
                ecog TEXT,
                diagnosis_date TEXT
            )
        ''')
        
        # Create lab_results table
        cursor.execute('''
            CREATE TABLE lab_results (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                test_name TEXT NOT NULL,
                test_date TEXT,
                result_value REAL,
                result_unit TEXT,
                reference_range TEXT,
                status TEXT,
                ordering_provider TEXT,
                lab_name TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create clinical_documents table
        cursor.execute('''
            CREATE TABLE clinical_documents (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_date TEXT,
                document_title TEXT,
                document_content TEXT,
                author TEXT,
                note_id TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create patient_conditions table
        cursor.execute('''
            CREATE TABLE patient_conditions (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                condition_name TEXT NOT NULL,
                onset_date TEXT,
                status TEXT,
                icd10_code TEXT,
                severity TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create patient_procedures table
        cursor.execute('''
            CREATE TABLE patient_procedures (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                procedure_name TEXT NOT NULL,
                procedure_date TEXT,
                cpt_code TEXT,
                status TEXT,
                provider TEXT,
                facility TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create family_history table
        cursor.execute('''
            CREATE TABLE family_history (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                relative TEXT NOT NULL,
                condition TEXT NOT NULL,
                age_at_onset INTEGER,
                status TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create imaging_reports table
        cursor.execute('''
            CREATE TABLE imaging_reports (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                study_type TEXT NOT NULL,
                study_date TEXT,
                report_content TEXT,
                radiologist TEXT,
                facility TEXT,
                status TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Create treatment_history table
        cursor.execute('''
            CREATE TABLE treatment_history (
                id INTEGER PRIMARY KEY,
                patient_mrn TEXT NOT NULL,
                treatment_type TEXT NOT NULL,
                drug_name TEXT,
                start_date TEXT,
                end_date TEXT,
                line_of_therapy INTEGER,
                status TEXT,
                provider TEXT,
                FOREIGN KEY (patient_mrn) REFERENCES patients (mrn)
            )
        ''')
        
        # Load realistic data from JSON file
        self._load_realistic_data(cursor)
        
        conn.commit()
    
    def _load_realistic_data(self, cursor):
        """Load realistic data from JSON file into all tables"""
        json_file_path = os.path.join(os.path.dirname(__file__), 'mock_ehr_pa_oncology_genomics_with_notes_and_fhir.json')
        
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            
            # Load patients data
            patients_data = []
            for i, patient_record in enumerate(data, 1):
                admin = patient_record['patient_admin']
                coverage = patient_record['coverage']
                diagnosis = patient_record['diagnosis_and_stage']
                
                patients_data.append((
                    i,
                    admin['mrn'],
                    f"{admin['name']['given']} {admin['name']['family']}",
                    admin['dob'],
                    admin['sex_at_birth'],
                    admin.get('race', 'Unknown'),
                    admin.get('address', ''),
                    admin.get('contact', {}).get('phone', ''),
                    admin.get('contact', {}).get('email', ''),
                    coverage['payer'],
                    coverage.get('plan_type', ''),
                    coverage.get('member_id', ''),
                    diagnosis['description'],
                    diagnosis['primary_icd10'],
                    diagnosis['stage_group'],
                    diagnosis['ecog'],
                    diagnosis['date_of_diagnosis']
                ))
            
            # Insert patients data
            cursor.executemany('''
                INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', patients_data)
            
            # Load lab results data
            lab_data = []
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                labs = patient_record.get('labs', [])
                for lab in labs:
                    lab_data.append((
                        len(lab_data) + 1,
                        mrn,
                        lab.get('test_name', 'Unknown Test'),
                        lab.get('date', datetime.now().strftime('%Y-%m-%d')),
                        lab.get('value', 0.0),
                        lab.get('unit', ''),
                        lab.get('reference_range', ''),
                        lab.get('status', 'final'),
                        lab.get('ordering_provider', 'Unknown'),
                        lab.get('lab_name', 'Unknown Lab')
                    ))
            
            # Insert lab results data
            if lab_data:
                cursor.executemany('''
                    INSERT INTO lab_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', lab_data)
            
            # Load clinical documents data
            doc_data = []
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                
                # Add pathology report
                if 'pathology_synoptic' in patient_record:
                    path = patient_record['pathology_synoptic']
                    doc_data.append((
                        len(doc_data) + 1,
                        mrn,
                        'Pathology Report',
                        path['specimen']['collection_date'],
                        f"Pathology Report - {path['specimen']['type']}",
                        f"Specimen: {path['specimen']['type']} from {path['specimen']['site']}. Histology: {path['histology']}, Grade: {path['grade']}, Size: {path['tumor_size_mm']}mm. Margins: {path['margins']}, LVI: {path['lvi']}.",
                        'Pathologist',
                        f"DOC_{mrn}_PATH"
                    ))
                
                # Add genomic testing report
                if 'genomic_testing' in patient_record and 'current_test' in patient_record['genomic_testing']:
                    test = patient_record['genomic_testing']['current_test']
                    doc_data.append((
                        len(doc_data) + 1,
                        mrn,
                        'Genomic Testing Report',
                        test['report_date'],
                        f"Genomic Testing Report - {test['test_name']}",
                        f"Test: {test['test_name']} (CPT {test['cpt']}). Methodology: {test['methodology']}. Genes analyzed: {test['genes_analyzed']}.",
                        'Genetic Counselor',
                        f"DOC_{mrn}_GEN"
                    ))
                
                # Add clinical notes
                for note in patient_record.get('clinical_notes', []):
                    doc_data.append((
                        len(doc_data) + 1,
                        mrn,
                        note['type'],
                        note['date'],
                        f"{note['type']} - {note['author']}",
                        note['text'],
                        note['author'],
                        note['note_id']
                    ))
            
            # Insert clinical documents data
            if doc_data:
                cursor.executemany('''
                    INSERT INTO clinical_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', doc_data)
            
            # Load patient conditions data
            condition_data = []
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                diagnosis = patient_record['diagnosis_and_stage']
                
                condition_data.append((
                    len(condition_data) + 1,
                    mrn,
                    diagnosis['description'],
                    diagnosis['date_of_diagnosis'],
                    'active',
                    diagnosis['primary_icd10'],
                    diagnosis['stage_group']
                ))
            
            # Insert patient conditions data
            if condition_data:
                cursor.executemany('''
                    INSERT INTO patient_conditions VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', condition_data)
            
            # Load family history data
            family_data = []
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                family_history = patient_record.get('family_history', [])
                
                for relative in family_history:
                    family_data.append((
                        len(family_data) + 1,
                        mrn,
                        relative['relationship'],
                        relative['condition'],
                        relative.get('age_at_diagnosis', 0),
                        'alive'
                    ))
            
            # Insert family history data
            if family_data:
                cursor.executemany('''
                    INSERT INTO family_history VALUES (?, ?, ?, ?, ?, ?)
                ''', family_data)
            
            # Load treatment history data
            treatment_data = []
            for patient_record in data:
                mrn = patient_record['patient_admin']['mrn']
                treatments = patient_record.get('treatment_history', {}).get('systemic_therapies', [])
                
                for therapy in treatments:
                    treatment_data.append((
                        len(treatment_data) + 1,
                        mrn,
                        'Systemic Therapy',
                        therapy['drug'],
                        therapy['start'],
                        therapy.get('stop'),
                        therapy['line_of_therapy'],
                        'completed' if therapy.get('stop') else 'active',
                        therapy.get('provider', 'Unknown')
                    ))
            
            # Insert treatment history data
            if treatment_data:
                cursor.executemany('''
                    INSERT INTO treatment_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', treatment_data)
            
            # Load prior authorization data
            pa_data = []
            for i, patient_record in enumerate(data, 1):
                admin = patient_record['patient_admin']
                coverage = patient_record['coverage']
                diagnosis = patient_record['diagnosis_and_stage']
                genomic_test = patient_record['genomic_testing']['current_test']
                pa_metadata = patient_record.get('pa_metadata', {})
                
                # Determine status based on PA metadata or random assignment
                status_options = ['pending', 'running', 'review', 'feedback', 'completed']
                status = pa_metadata.get('status', 'pending')
                if status == 'Submitted':
                    status = 'pending'
                elif status == 'Pending clinical review':
                    status = 'review'
                elif status == 'Denied - need additional documentation':
                    status = 'feedback'
                else:
                    status = random.choice(status_options)
                
                # Determine current step based on status
                if status == 'pending':
                    current_step = 1
                elif status == 'running':
                    current_step = random.randint(2, 3)
                elif status in ['review', 'feedback', 'completed']:
                    current_step = 4
                else:
                    current_step = 1
                
                # Create step details
                step_details = {
                    "step1": {"status": "completed" if current_step > 1 else "pending", "details": "Insurance coverage & requirements analysis"},
                    "step2": {"status": "completed" if current_step > 2 else "pending", "details": "Screening analysis"},
                    "step3": {"status": "completed" if current_step > 3 else "pending", "details": "Data extraction"},
                    "step4": {"status": "completed" if current_step == 4 else "pending", "details": "Form completion"}
                }
                
                # Generate dates
                created_date = datetime.now() - timedelta(days=random.randint(1, 30))
                due_date = created_date + timedelta(days=random.randint(7, 21))
                last_updated = datetime.now() - timedelta(hours=random.randint(1, 72))
                
                # Determine clinical urgency
                if diagnosis['stage_group'] in ['IV', 'IVB']:
                    clinical_urgency = 'urgent'
                elif diagnosis['stage_group'] in ['III', 'IIIC']:
                    clinical_urgency = 'routine'
                else:
                    clinical_urgency = 'routine'
                
                # Create EHR documents list
                ehr_documents = [
                    {"name": "Pathology Report", "type": "document"},
                    {"name": "Genomic Testing Report", "type": "document"},
                    {"name": "Clinical Notes", "type": "document"}
                ]
                
                # Add genetic counseling note if family history exists
                if patient_record.get('family_history'):
                    ehr_documents.append({"name": "Genetic Counseling Note", "type": "document"})
                
                pa_data.append((
                    i,
                    f"{admin['name']['given']} {admin['name']['family']}",
                    admin['mrn'],
                    admin['dob'],
                    admin['sex_at_birth'],
                    coverage['payer'],
                    genomic_test['test_name'],
                    genomic_test['cpt'],
                    diagnosis['description'],
                    "See treatment history",  # Simplified for demo
                    "None",  # Simplified for demo
                    datetime.now().strftime('%Y-%m-%d'),
                    status,
                    current_step,
                    json.dumps(step_details),
                    "pending" if status == 'pending' else "running" if status == 'running' else "completed",
                    created_date.strftime('%Y-%m-%d'),
                    due_date.strftime('%Y-%m-%d'),
                    "Jarvus Agent" if status != 'pending' else None,
                    f"Prior authorization for {genomic_test['test_name']}",
                    clinical_urgency,
                    f"Requires {coverage['payer']} approval for {genomic_test['cpt']}",
                    json.dumps(ehr_documents),
                    last_updated.strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            # Insert prior authorization data
            cursor.executemany('''
                INSERT INTO prior_auths VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', pa_data)
            
            print(f"Loaded {len(patients_data)} patients, {len(lab_data)} lab results, {len(doc_data)} documents, and {len(pa_data)} prior authorizations from JSON file")
            
        except FileNotFoundError:
            print(f"Warning: Mock EHR JSON file not found at {json_file_path}")
            # Fallback to basic mock data
            self._load_basic_mock_data(cursor)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            self._load_basic_mock_data(cursor)
        except Exception as e:
            print(f"Error loading realistic data: {e}")
            self._load_basic_mock_data(cursor)
    
    def _load_basic_mock_data(self, cursor):
        """Fallback to basic mock data if JSON file is not available"""
        # Basic mock data (simplified version of the original)
        mock_data = [
            (1, "John Smith", "MRN001", "1985-03-15", "Male", "Original Medicare", "BRCA1/BRCA2 Genetic Testing", "81162", "Family history of breast cancer", "No prior treatment", "None", "2024-02-15", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Insurance coverage & requirements analysis not started"}}), "pending", "2024-01-15", "2024-01-22", None, "Family history of breast cancer", "urgent", "Requires genetic counselor review - Medicare LCD", json.dumps([{"name": "Family History Form", "type": "document"}, {"name": "Genetic Counseling Note", "type": "document"}]), "2024-01-15 09:00:00")
        ]
        
        cursor.executemany('''
            INSERT INTO prior_auths VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', mock_data)
        
        print("Loaded basic mock data (fallback)")
    
    def get_prior_auths_by_status(self, status):
        """Get prior authorizations by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'all':
            cursor.execute('SELECT * FROM prior_auths ORDER BY created_date ASC')
        else:
            cursor.execute('SELECT * FROM prior_auths WHERE status = ? ORDER BY created_date ASC', (status,))
        
        rows = cursor.fetchall()
        
        prior_auths = []
        for row in rows:
            prior_auths.append({
                'id': row[0],
                'patient_name': row[1],
                'patient_mrn': row[2],
                'patient_dob': row[3],
                'patient_gender': row[4],
                'insurance_provider': row[5],
                'service_type': row[6],
                'cpt_code': row[7],
                'diagnosis': row[8],
                'treatment_history': row[9],
                'allergies': row[10],
                'procedure_date': row[11],
                'status': row[12],
                'current_step': row[13],
                'step_details': row[14],
                'automation_status': row[15],
                'created_date': row[16],
                'due_date': row[17],
                'assigned_to': row[18],
                'notes': row[19],
                'clinical_urgency': row[20],
                'insurance_requirements': row[21],
                'ehr_documents': row[22],
                'last_updated': row[23]
            })
        
        return prior_auths
    
    def get_stats(self):
        """Get statistics for the dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get counts for each status
        cursor.execute('SELECT status, COUNT(*) FROM prior_auths GROUP BY status')
        status_counts = dict(cursor.fetchall())
        
        # Get insurance provider distribution
        cursor.execute('SELECT insurance_provider, COUNT(*) FROM prior_auths GROUP BY insurance_provider')
        provider_counts = dict(cursor.fetchall())
        
        # Get step distribution
        cursor.execute('SELECT current_step, COUNT(*) FROM prior_auths GROUP BY current_step')
        step_counts = dict(cursor.fetchall())
        
        return {
            'total': sum(status_counts.values()),
            'pending': status_counts.get('pending', 0),
            'running': status_counts.get('running', 0),
            'review': status_counts.get('review', 0),
            'feedback': status_counts.get('feedback', 0),
            'completed': status_counts.get('completed', 0),
            'providers': provider_counts,
            'step_counts': step_counts
        }
    
    def start_automation(self, auth_id):
        """Start automation for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET status = 'running', automation_status = 'running', assigned_to = 'Jarvus Agent', last_updated = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        
        conn.commit()
        return True
    

    
    def update_step(self, auth_id, step_number, step_details):
        """Update the current step for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current step details
        cursor.execute('SELECT step_details FROM prior_auths WHERE id = ?', (auth_id,))
        result = cursor.fetchone()
        if result:
            current_step_details = json.loads(result[0]) if result[0] else {}
            current_step_details[f"step{step_number}"] = step_details
            
            cursor.execute('''
                UPDATE prior_auths 
                SET current_step = ?, step_details = ?, last_updated = ?
                WHERE id = ?
            ''', (step_number, json.dumps(current_step_details), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
            
            conn.commit()
            return True
        return False
    
    def update_prior_auth_step(self, auth_id, step_number):
        """Update the current step for a prior authorization (simplified version)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET current_step = ?, last_updated = ?
            WHERE id = ?
        ''', (step_number, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        
        conn.commit()
        return True
    
    def update_prior_auth_status(self, auth_id, status):
        """Update the status of a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET status = ?, last_updated = ?
            WHERE id = ?
        ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        
        conn.commit()
        return True
    
    def update_step_status(self, auth_id, step_number, status, details):
        """Update the status of a specific step"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current step details
        cursor.execute('SELECT step_details FROM prior_auths WHERE id = ?', (auth_id,))
        result = cursor.fetchone()
        if result:
            current_step_details = json.loads(result[0]) if result[0] else {}
            current_step_details[f"step{step_number}"] = {"status": status, "details": details}
            
            cursor.execute('''
                UPDATE prior_auths 
                SET step_details = ?, last_updated = ?
                WHERE id = ?
            ''', (json.dumps(current_step_details), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
            
            conn.commit()
            return True
        return False
    
    def approve_step(self, auth_id, step_number):
        """Approve a step and move to next"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update step status
        cursor.execute('SELECT step_details FROM prior_auths WHERE id = ?', (auth_id,))
        result = cursor.fetchone()
        if result:
            step_details = json.loads(result[0]) if result[0] else {}
            step_details[f"step{step_number}"] = {"status": "approved", "details": "Step approved by user"}
            
            # Move to next step or complete
            next_step = step_number + 1
            if next_step > 4:
                # Complete the automation
                cursor.execute('''
                    UPDATE prior_auths 
                    SET status = 'completed', current_step = 4, step_details = ?, last_updated = ?
                    WHERE id = ?
                ''', (json.dumps(step_details), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
            else:
                cursor.execute('''
                    UPDATE prior_auths 
                    SET current_step = ?, step_details = ?, last_updated = ?
                    WHERE id = ?
                ''', (next_step, json.dumps(step_details), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
            
            conn.commit()
            return True
        return False
    
    def request_changes(self, auth_id, step_number, changes):
        """Request changes for a step"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET status = 'feedback', last_updated = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        
        conn.commit()
        return True
    
    def provide_feedback(self, auth_id, feedback):
        """Provide feedback for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET notes = ?, last_updated = ?
            WHERE id = ?
        ''', (feedback, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        
        conn.commit()
        return True
    
    def reset_database(self):
        """Reset the database for demo purposes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS prior_auths')
        conn.commit()
        
        # Reinitialize with fresh data
        self._init_db()
        return True
    
    def reset_all_to_pending(self):
        """Reset all prior authorizations to pending status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET status = 'pending', 
                current_step = 1, 
                step_details = '{}', 
                automation_status = 'pending',
                last_updated = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        conn.commit()
        return True

# Global database instance
db = PriorAuthDatabase()
