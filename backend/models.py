import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
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


class AdjustmentStatus(str, Enum):
    REQUESTED = "requested"
    UNDER_REVIEW = "under-review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdjustmentDecision(BaseModel):
    decided_by: str
    decided_at: datetime = Field(default_factory=datetime.now)
    status: AdjustmentStatus
    rationale: Optional[str] = None


class AdjustmentAuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    adjustment_id: str
    actor_id: str
    actor_role: UserType
    action: str
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TreatmentAdjustment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    requested_by: str
    order_id: Optional[str] = None
    field_path: str
    new_value: str
    reason: str
    status: AdjustmentStatus = AdjustmentStatus.REQUESTED
    created_at: datetime = Field(default_factory=datetime.now)
    decision: Optional[AdjustmentDecision] = None
    audit_trail: List[AdjustmentAuditEntry] = Field(default_factory=list)


class AdjustmentCreatePayload(BaseModel):
    patient_id: str
    order_id: Optional[str] = None
    field_path: str
    new_value: str
    reason: str


class AdjustmentDecisionPayload(BaseModel):
    status: AdjustmentStatus
    rationale: Optional[str] = None

    @validator("status")
    def validate_status(cls, value: AdjustmentStatus) -> AdjustmentStatus:
        if value not in (AdjustmentStatus.APPROVED, AdjustmentStatus.REJECTED):
            raise ValueError("Decision status must be approved or rejected")
        return value


class CarePlanRevision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    order_id: Optional[str] = None
    field_path: str
    value: str
    revised_from: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str



class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    channel: str = "push"
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None



class ObservationInput(BaseModel):
    id: Optional[str] = None
    code: str
    value: Any
    unit: Optional[str] = None
    effective_at: datetime = Field(default_factory=datetime.now, alias="effectiveAt")
    source: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    code: str
    value: Any
    unit: Optional[str] = None
    effective_at: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = None


class ObservationBatchRequest(BaseModel):
    patient_id: str = Field(alias="patientId")
    observations: List[ObservationInput]

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AlertTimelineEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    status: AlertStatus
    actor_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    code: str
    value: Any
    unit: Optional[str] = None
    observed_at: datetime
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    closed_by: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[AlertTimelineEntry] = Field(default_factory=list)


class AlertStatusUpdate(BaseModel):
    status: AlertStatus
    notes: Optional[str] = None

    @validator("status")
    def validate_transition_status(cls, value: AlertStatus) -> AlertStatus:
        if value == AlertStatus.OPEN:
            raise ValueError("Cannot transition back to open")
        return value


