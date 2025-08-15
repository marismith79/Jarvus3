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
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prior_auths'")
        if cursor.fetchone():
            return  # Table already exists
        
        # Create table
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
        
        # Load realistic data from JSON file
        self._load_realistic_data(cursor)
        
        conn.commit()
    
    def _load_realistic_data(self, cursor):
        """Load realistic prior authorization data from JSON file"""
        json_file_path = os.path.join(os.path.dirname(__file__), 'mock_ehr_pa_oncology_genomics_with_notes_and_fhir.json')
        
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            
            # Convert JSON data to database format
            mock_data = []
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
                    current_step = random.randint(2, 4)
                elif status in ['review', 'feedback', 'completed']:
                    current_step = 5
                else:
                    current_step = 1
                
                # Create step details
                step_details = {
                    "step1": {"status": "completed" if current_step > 1 else "pending", "details": "Coverage determination"},
                    "step2": {"status": "completed" if current_step > 2 else "pending", "details": "Insurance requirements"},
                    "step3": {"status": "completed" if current_step > 3 else "pending", "details": "Screening analysis"},
                    "step4": {"status": "completed" if current_step > 4 else "pending", "details": "Data extraction"},
                    "step5": {"status": "completed" if current_step == 5 else "pending", "details": "Form completion"}
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
                
                mock_data.append((
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
            
            # Insert the data
            cursor.executemany('''
                INSERT INTO prior_auths VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', mock_data)
            
            print(f"Loaded {len(mock_data)} realistic prior authorization records from JSON file")
            
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
            (1, "John Smith", "MRN001", "1985-03-15", "Male", "Original Medicare", "BRCA1/BRCA2 Genetic Testing", "81162", "Family history of breast cancer", "No prior treatment", "None", "2024-02-15", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-15", "2024-01-22", None, "Family history of breast cancer", "urgent", "Requires genetic counselor review - Medicare LCD", json.dumps([{"name": "Family History Form", "type": "document"}, {"name": "Genetic Counseling Note", "type": "document"}]), "2024-01-15 09:00:00")
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
    
    def pause_automation(self, auth_id):
        """Pause automation for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prior_auths 
            SET automation_status = 'paused', last_updated = ?
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
            if next_step > 5:
                # Complete the automation
                cursor.execute('''
                    UPDATE prior_auths 
                    SET status = 'completed', current_step = 5, step_details = ?, last_updated = ?
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

# Global database instance
db = PriorAuthDatabase()
