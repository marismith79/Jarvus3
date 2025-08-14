import sqlite3
from datetime import datetime
import threading
import json

class PriorAuthDatabase:
    def __init__(self):
        self._local = threading.local()
        self.init_db()
    
    def get_connection(self):
        """Get a database connection for the current thread"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(':memory:')
            self._init_db_for_thread()
        return self._local.connection
    
    def init_db(self):
        """Initialize the database schema and data"""
        # This will be called by the first thread that accesses the database
        pass
    
    def _init_db_for_thread(self):
        """Initialize the database for the current thread"""
        conn = self._local.connection
        cursor = conn.cursor()
        
        # Create prior authorization table with automation workflow fields
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
        
        # Insert mock data with automation workflow information
        mock_data = [
            # All Prior Auths (available for automation)
            (1, "John Smith", "MRN001", "1985-03-15", "Male", "Medicare Part B", "BRCA1/BRCA2 Genetic Testing", "81162", "Family history of breast cancer", "No prior treatment", "None", "2024-02-15", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-15", "2024-01-22", None, "Family history of breast cancer", "urgent", "Requires genetic counselor review - Medicare LCD", json.dumps([{"name": "Family History Form", "type": "document"}]), "2024-01-15 09:00:00"),
            (2, "Sarah Johnson", "MRN002", "1978-07-22", "Female", "Humana Medicare Advantage", "Lynch Syndrome Testing", "81292", "Family history of colorectal cancer", "Colonoscopy 2023", "Penicillin", "2024-02-20", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-16", "2024-01-25", None, "Family history of colorectal cancer", "routine", "Medicare Advantage prior auth required", json.dumps([{"name": "Genetic Counseling Note", "type": "document"}]), "2024-01-16 10:30:00"),
            (3, "Michael Brown", "MRN003", "1965-11-08", "Male", "UnitedHealthcare Medicare Advantage", "Comprehensive Tumor Profiling", "81455", "Metastatic lung cancer", "Chemotherapy cycles 1-3", "None", "2024-02-10", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-17", "2024-01-24", None, "Metastatic lung cancer - treatment selection", "urgent", "Requires oncology review - Medicare coverage", json.dumps([{"name": "Oncology Consultation", "type": "document"}, {"name": "Pathology Report", "type": "document"}]), "2024-01-17 14:15:00"),
            (4, "Emily Davis", "MRN004", "1992-04-30", "Female", "Aetna Medicare Advantage", "Hereditary Cancer Panel", "81432", "Multiple primary cancers", "Surgery 2023", "Latex", "2024-02-25", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-18", "2024-01-30", None, "Multiple primary cancers", "routine", "Medicare Advantage panel approval", json.dumps([{"name": "Cancer History Summary", "type": "document"}]), "2024-01-18 11:45:00"),
            (5, "David Wilson", "MRN005", "1958-12-14", "Male", "Kaiser Medicare Advantage", "Pharmacogenetic Testing", "81227", "Medication optimization", "Multiple medication trials", "Sulfa drugs", "2024-02-18", "pending", 1, json.dumps({"step1": {"status": "pending", "details": "Coverage determination not started"}}), "pending", "2024-01-19", "2024-01-28", None, "Medication optimization", "routine", "Medicare Advantage PGx testing criteria", json.dumps([{"name": "Medication List", "type": "document"}]), "2024-01-19 16:20:00"),
            
            # Running Prior Auths (being processed by agent)
            (6, "Lisa Anderson", "MRN006", "1973-09-05", "Female", "Medicare Part B", "FoundationOne CDx", "81455", "Advanced NSCLC", "Previous chemotherapy cycles", "None", "2024-02-12", "running", 3, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed for Medicare NCD 90.2"}, "step2": {"status": "completed", "details": "Requirements extracted successfully"}, "step3": {"status": "running", "details": "Screening EHR data completeness"}}), "running", "2024-01-14", "2024-01-21", "Jarvus Agent", "Advanced NSCLC - targeted therapy", "urgent", "Medicare NCD 90.2 coverage", json.dumps([{"name": "Oncology Progress Note", "type": "document"}, {"name": "Imaging Reports", "type": "document"}]), "2024-01-20 08:30:00"),
            (7, "Robert Taylor", "MRN007", "1947-06-18", "Male", "Anthem Medicare Advantage", "Guardant360 Liquid Biopsy", "81479", "Metastatic breast cancer", "Hormone therapy ongoing", "None", "2024-02-08", "running", 4, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "completed", "details": "Requirements extracted"}, "step3": {"status": "completed", "details": "Screening passed"}, "step4": {"status": "running", "details": "Extracting data from EHR"}}), "running", "2024-01-13", "2024-01-20", "Jarvus Agent", "Metastatic breast cancer monitoring", "urgent", "Medicare Advantage liquid biopsy approval", json.dumps([{"name": "Breast Cancer Staging", "type": "document"}, {"name": "Treatment Plan", "type": "document"}]), "2024-01-20 09:15:00"),
            (8, "Jennifer Garcia", "MRN008", "1988-02-11", "Female", "Cigna Medicare Advantage", "Caris Molecular Profiling", "81455", "Rare cancer diagnosis", "Surgery and radiation", "None", "2024-02-22", "running", 2, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "running", "details": "Extracting requirements from insurance portal"}}), "running", "2024-01-15", "2024-01-26", "Jarvus Agent", "Rare cancer diagnosis", "routine", "Medicare Advantage comprehensive profiling", json.dumps([{"name": "Pathology Report", "type": "document"}, {"name": "Surgical Report", "type": "document"}]), "2024-01-20 10:45:00"),
            
            # Pending Review (requires admin review)
            (9, "Thomas Martinez", "MRN009", "2010-03-25", "Male", "Medicare Part B", "MSK-IMPACT Panel", "81455", "Pediatric cancer diagnosis", "Initial diagnosis", "None", "2024-02-28", "review", 5, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "completed", "details": "Requirements extracted"}, "step3": {"status": "completed", "details": "Screening passed"}, "step4": {"status": "completed", "details": "Data extracted"}, "step5": {"status": "review", "details": "Form ready for human review"}}), "review", "2024-01-12", "2024-01-19", "Jarvus Agent", "Pediatric cancer diagnosis", "urgent", "Medicare pediatric coverage review", json.dumps([{"name": "Pediatric Oncology Note", "type": "document"}, {"name": "Family History", "type": "document"}]), "2024-01-20 12:00:00"),
            (10, "Amanda Rodriguez", "MRN010", "1961-08-07", "Female", "Blue Cross Medicare Advantage", "Tempus xT Panel", "81455", "Advanced solid tumor", "Multiple treatment lines", "None", "2024-02-15", "review", 5, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "completed", "details": "Requirements extracted"}, "step3": {"status": "completed", "details": "Screening passed"}, "step4": {"status": "completed", "details": "Data extracted"}, "step5": {"status": "review", "details": "Form ready for human review"}}), "review", "2024-01-11", "2024-01-18", "Jarvus Agent", "Advanced solid tumor", "urgent", "Medicare Advantage genomic profiling", json.dumps([{"name": "Tumor Board Notes", "type": "document"}, {"name": "Treatment History", "type": "document"}]), "2024-01-20 13:30:00"),
            (11, "Christopher Lee", "MRN011", "1975-12-03", "Male", "Medicare Part B", "Invitae Cancer Panel", "81432", "Hereditary cancer risk", "Family history only", "None", "2024-02-20", "review", 5, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "completed", "details": "Requirements extracted"}, "step3": {"status": "completed", "details": "Screening passed"}, "step4": {"status": "completed", "details": "Data extracted"}, "step5": {"status": "review", "details": "Form ready for human review"}}), "review", "2024-01-10", "2024-01-17", "Jarvus Agent", "Hereditary cancer risk", "urgent", "Medicare hereditary panel approval", json.dumps([{"name": "Genetic Counseling Note", "type": "document"}]), "2024-01-20 14:45:00"),
            
            # Feedback Required (agent needs staff input)
            (12, "Nicole White", "MRN012", "1995-11-19", "Female", "Medicare Part B", "Experimental Gene Therapy", "J9999", "Rare genetic disorder", "No standard treatment available", "None", "2024-03-01", "feedback", 2, json.dumps({"step1": {"status": "completed", "details": "Coverage unclear - experimental therapy"}, "step2": {"status": "feedback", "details": "Need clarification on experimental therapy criteria"}}), "feedback", "2024-01-09", "2024-01-16", "Jarvus Agent", "Rare genetic disorder", "urgent", "Medicare experimental therapy unclear", json.dumps([{"name": "Genetic Testing Results", "type": "document"}, {"name": "Research Protocol", "type": "document"}]), "2024-01-20 15:20:00"),
            (13, "Kevin Thompson", "MRN013", "1952-04-12", "Male", "Humana Medicare Advantage", "Out-of-Network Genetic Testing", "81292", "Specialist not in network", "Previous in-network attempts", "None", "2024-02-25", "feedback", 3, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed with network exception"}, "step2": {"status": "completed", "details": "Requirements extracted"}, "step3": {"status": "feedback", "details": "Need network exception documentation"}}), "feedback", "2024-01-08", "2024-01-15", "Jarvus Agent", "Specialist not in network", "routine", "Medicare Advantage network exception", json.dumps([{"name": "Network Exception Request", "type": "document"}]), "2024-01-20 16:10:00"),
            (14, "Rachel Clark", "MRN014", "1983-07-29", "Female", "Medicare Part B", "International Genetic Testing", "81432", "Rare genetic condition abroad", "International consultation", "None", "2024-02-18", "feedback", 1, json.dumps({"step1": {"status": "feedback", "details": "Need clarification on international coverage"}}), "feedback", "2024-01-07", "2024-01-14", "Jarvus Agent", "Rare genetic condition abroad", "urgent", "Medicare international coverage unclear", json.dumps([{"name": "International Consultation", "type": "document"}]), "2024-01-20 17:00:00"),
            (15, "Daniel Lewis", "MRN015", "1968-10-16", "Male", "Aetna Medicare Advantage", "Custom Genetic Panel", "81479", "Rare genetic syndrome", "Standard panels negative", "None", "2024-02-30", "feedback", 2, json.dumps({"step1": {"status": "completed", "details": "Coverage confirmed"}, "step2": {"status": "feedback", "details": "Need custom panel justification"}}), "feedback", "2024-01-06", "2024-01-13", "Jarvus Agent", "Rare genetic syndrome", "routine", "Medicare Advantage custom panel approval", json.dumps([{"name": "Previous Genetic Testing", "type": "document"}]), "2024-01-20 18:30:00")
        ]
        
        cursor.executemany('''
            INSERT INTO prior_auths VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', mock_data)
        
        conn.commit()
    
    def get_prior_auths_by_status(self, status):
        """Get prior authorizations by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'all':
            cursor.execute('SELECT * FROM prior_auths WHERE status = "pending" ORDER BY created_date ASC')
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
            'status_counts': status_counts,
            'provider_counts': provider_counts,
            'step_counts': step_counts,
            'total_count': sum(status_counts.values())
        }
    
    def start_automation(self, auth_id):
        """Start automation for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prior_auths 
            SET status = "running", automation_status = "running", assigned_to = "Jarvus Agent", last_updated = ? 
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
            SET status = "pending", automation_status = "paused", last_updated = ? 
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def update_step(self, auth_id, step_number, step_status, step_details):
        """Update the current step and its details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current step details
        cursor.execute('SELECT step_details FROM prior_auths WHERE id = ?', (auth_id,))
        result = cursor.fetchone()
        current_details = json.loads(result[0]) if result and result[0] else {}
        
        # Update step details
        current_details[f"step{step_number}"] = {
            "status": step_status,
            "details": step_details,
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Update database
        cursor.execute('''
            UPDATE prior_auths 
            SET current_step = ?, step_details = ?, last_updated = ? 
            WHERE id = ?
        ''', (step_number, json.dumps(current_details), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def approve_step(self, auth_id):
        """Approve current step and move to next"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current step
        cursor.execute('SELECT current_step FROM prior_auths WHERE id = ?', (auth_id,))
        result = cursor.fetchone()
        current_step = result[0] if result else 1
        
        # Move to next step or complete
        if current_step < 5:
            next_step = current_step + 1
            status = "running"
        else:
            next_step = 5
            status = "completed"
        
        cursor.execute('''
            UPDATE prior_auths 
            SET current_step = ?, status = ?, last_updated = ? 
            WHERE id = ?
        ''', (next_step, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def request_changes(self, auth_id, changes):
        """Request changes for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prior_auths 
            SET status = "feedback", notes = ?, last_updated = ? 
            WHERE id = ?
        ''', (f"Changes requested: {changes}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def provide_feedback(self, auth_id, feedback):
        """Provide feedback for a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prior_auths 
            SET status = "running", notes = ?, last_updated = ? 
            WHERE id = ?
        ''', (f"Feedback provided: {feedback}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def update_status(self, auth_id, new_status):
        """Update the status of a prior authorization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE prior_auths 
            SET status = ?, last_updated = ? 
            WHERE id = ?
        ''', (new_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auth_id))
        conn.commit()
        
        return True
    
    def close(self):
        """Close the database connection for the current thread"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')

# Global database instance
db = PriorAuthDatabase()
