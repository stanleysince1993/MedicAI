import json
import os
import secrets
import string
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .models import User, ClinicalRecord, PatientAccess, UserType, VitalSigns


class SimpleDatabase:
    """Simple file-based database for MVP"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.users_file = os.path.join(data_dir, "users.json")
        self.records_file = os.path.join(data_dir, "clinical_records.json")
        self.access_file = os.path.join(data_dir, "patient_access.json")
        
        self._init_files()
    
    def _init_files(self):
        """Initialize empty JSON files if they don't exist"""
        for file_path in [self.users_file, self.records_file, self.access_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _load_json(self, file_path: str) -> List[dict]:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, file_path: str, data: List[dict]):
        """Save JSON data to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # User operations
    def generate_patient_code(self) -> str:
        """Generate a unique 8-character patient code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not self.get_patient_by_code(code):
                return code
    
    def create_user(self, user: User) -> User:
        """Create a new user"""
        users = self._load_json(self.users_file)
        
        # Check if email already exists
        if any(u.get('email') == user.email for u in users):
            raise ValueError("Email already exists")
        
        # Generate patient code for patients
        if user.user_type == UserType.PATIENT and not user.patient_code:
            user.patient_code = self.generate_patient_code()
        
        user_dict = user.dict()
        users.append(user_dict)
        self._save_json(self.users_file, users)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self._load_json(self.users_file)
        for user_dict in users:
            if user_dict.get('email') == email:
                return User(**user_dict)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self._load_json(self.users_file)
        for user_dict in users:
            if user_dict.get('id') == user_id:
                return User(**user_dict)
        return None
    
    def get_doctors(self) -> List[User]:
        """Get all doctors"""
        users = self._load_json(self.users_file)
        return [User(**u) for u in users if u.get('user_type') == UserType.DOCTOR]
    
    def get_patients(self) -> List[User]:
        """Get all patients"""
        users = self._load_json(self.users_file)
        return [User(**u) for u in users if u.get('user_type') == UserType.PATIENT]
    
    # Clinical record operations
    def create_clinical_record(self, record: ClinicalRecord) -> ClinicalRecord:
        """Create a new clinical record"""
        records = self._load_json(self.records_file)
        record_dict = record.dict()
        records.append(record_dict)
        self._save_json(self.records_file, records)
        return record
    
    def get_patient_records(self, patient_id: str) -> List[ClinicalRecord]:
        """Get all clinical records for a patient"""
        records = self._load_json(self.records_file)
        return [ClinicalRecord(**r) for r in records if r.get('patient_id') == patient_id]
    
    def get_doctor_records(self, doctor_id: str) -> List[ClinicalRecord]:
        """Get all clinical records created by a doctor"""
        records = self._load_json(self.records_file)
        return [ClinicalRecord(**r) for r in records if r.get('doctor_id') == doctor_id]
    
    def get_record_by_id(self, record_id: str) -> Optional[ClinicalRecord]:
        """Get clinical record by ID"""
        records = self._load_json(self.records_file)
        for record_dict in records:
            if record_dict.get('id') == record_id:
                return ClinicalRecord(**record_dict)
        return None
    
    # Patient access operations
    def grant_patient_access(self, access: PatientAccess) -> PatientAccess:
        """Grant a doctor access to a patient's records"""
        accesses = self._load_json(self.access_file)
        access_dict = access.dict()
        accesses.append(access_dict)
        self._save_json(self.access_file, accesses)
        return access
    
    def get_patient_accesses(self, patient_id: str) -> List[PatientAccess]:
        """Get all doctors who have access to a patient"""
        accesses = self._load_json(self.access_file)
        return [PatientAccess(**a) for a in accesses if a.get('patient_id') == patient_id and a.get('is_active')]
    
    def get_doctor_accesses(self, doctor_id: str) -> List[PatientAccess]:
        """Get all patients a doctor has access to"""
        accesses = self._load_json(self.access_file)
        return [PatientAccess(**a) for a in accesses if a.get('doctor_id') == doctor_id and a.get('is_active')]
    
    def has_patient_access(self, doctor_id: str, patient_id: str) -> bool:
        """Check if a doctor has access to a patient's records"""
        accesses = self._load_json(self.access_file)
        return any(
            a.get('doctor_id') == doctor_id and 
            a.get('patient_id') == patient_id and 
            a.get('is_active')
            for a in accesses
        )
    
    def get_patient_by_code(self, patient_code: str) -> Optional[User]:
        """Get patient by patient code"""
        users = self._load_json(self.users_file)
        for user_dict in users:
            if user_dict.get('patient_code') == patient_code and user_dict.get('user_type') == UserType.PATIENT:
                return User(**user_dict)
        return None
    
    def calculate_bmi(self, weight: float, height: float) -> float:
        """Calculate BMI from weight (kg) and height (cm)"""
        if height <= 0:
            return 0.0
        height_m = height / 100  # Convert cm to meters
        return round(weight / (height_m ** 2), 1)


# Global database instance
db = SimpleDatabase()
