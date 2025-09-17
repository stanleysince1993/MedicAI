import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class UserType(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    user_type: UserType
    full_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    
    # Doctor specific fields
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    
    # Patient specific fields
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    patient_code: Optional[str] = None  # Unique code for patient portal access


class VitalSigns(BaseModel):
    heart_rate: Optional[int] = None  # bpm
    blood_pressure_systolic: Optional[int] = None  # mmHg
    blood_pressure_diastolic: Optional[int] = None  # mmHg
    respiratory_rate: Optional[int] = None  # breaths per minute
    temperature: Optional[float] = None  # °C
    oxygen_saturation: Optional[int] = None  # %
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm
    bmi: Optional[float] = None  # calculated
    blood_glucose: Optional[float] = None  # mg/dL
    waist_circumference: Optional[float] = None  # cm
    pain_scale: Optional[int] = None  # 0-10

class ClinicalRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    case_text: str
    differentials: List[dict]
    tests: List[dict]
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Comprehensive clinical data
    vital_signs: Optional[VitalSigns] = None
    symptoms: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    past_history: Optional[str] = None
    family_history: Optional[str] = None
    reason_for_visit: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    follow_up: Optional[str] = None


class PatientAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    granted_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    access_level: str = "read"  # read, write


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    user_type: UserType
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = None


class ClinicalRecordRequest(BaseModel):
    case_text: str
    vital_signs: Optional[VitalSigns] = None
    symptoms: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    past_history: Optional[str] = None
    family_history: Optional[str] = None
    reason_for_visit: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    follow_up: Optional[str] = None

class PatientRegistrationRequest(BaseModel):
    full_name: str
    date_of_birth: str
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    vital_signs: VitalSigns
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    past_history: Optional[str] = None
    family_history: Optional[str] = None
    reason_for_visit: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    follow_up: Optional[str] = None


class SharePatientRequest(BaseModel):
    patient_id: str
    doctor_email: str
    access_level: str = "read"
