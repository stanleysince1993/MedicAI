import json
import os
import secrets
import string
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

from .models import (User, ClinicalRecord, PatientAccess, UserType, VitalSigns, TreatmentAdjustment, AdjustmentAuditEntry, CarePlanRevision, Notification, AdjustmentStatus, NotificationSeverity, Observation, Alert, AlertTimelineEntry, AlertStatus, AlertSeverity)


class SimpleDatabase:
    """Simple file-based database for MVP"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.users_file = os.path.join(data_dir, "users.json")
        self.records_file = os.path.join(data_dir, "clinical_records.json")
        self.access_file = os.path.join(data_dir, "patient_access.json")
        self.adjustments_file = os.path.join(data_dir, "adjustments.json")
        self.observations_file = os.path.join(data_dir, "observations.json")
        self.careplan_revisions_file = os.path.join(data_dir, "careplan_revisions.json")
        self.audit_log_file = os.path.join(data_dir, "audit_log.json")
        self.notifications_file = os.path.join(data_dir, "notifications.json")
        self.alerts_file = os.path.join(data_dir, "alerts.json")
        self.alert_events_file = os.path.join(data_dir, "alert_events.json")
        
        self._init_files()
    
    def _init_files(self):
        """Initialize empty JSON files if they don't exist"""
        for file_path in [self.users_file, self.records_file, self.access_file, self.adjustments_file, self.observations_file, self.careplan_revisions_file, self.audit_log_file, self.notifications_file, self.alerts_file, self.alert_events_file]:
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
    

    # Treatment adjustment operations
    def create_adjustment(self, adjustment: TreatmentAdjustment) -> TreatmentAdjustment:
        adjustments = self._load_json(self.adjustments_file)
        adjustments.append(adjustment.dict())
        self._save_json(self.adjustments_file, adjustments)
        for entry in adjustment.audit_trail:
            self._record_audit_event(entry)
        return adjustment

    def get_adjustment_by_id(self, adjustment_id: str) -> Optional[TreatmentAdjustment]:
        adjustments = self._load_json(self.adjustments_file)
        for item in adjustments:
            if item.get('id') == adjustment_id:
                return TreatmentAdjustment(**item)
        return None

    def list_patient_adjustments(self, patient_id: str) -> List[TreatmentAdjustment]:
        adjustments = self._load_json(self.adjustments_file)
        return [TreatmentAdjustment(**item) for item in adjustments if item.get('patient_id') == patient_id]

    def list_all_adjustments(self) -> List[TreatmentAdjustment]:
        adjustments = self._load_json(self.adjustments_file)
        return [TreatmentAdjustment(**item) for item in adjustments]

    def list_pending_adjustments(self) -> List[TreatmentAdjustment]:
        adjustments = self._load_json(self.adjustments_file)
        return [TreatmentAdjustment(**item) for item in adjustments if item.get('status') in {AdjustmentStatus.REQUESTED, AdjustmentStatus.UNDER_REVIEW}]

    def update_adjustment(self, adjustment: TreatmentAdjustment) -> TreatmentAdjustment:
        adjustments = self._load_json(self.adjustments_file)
        updated = False
        for idx, item in enumerate(adjustments):
            if item.get('id') == adjustment.id:
                adjustments[idx] = adjustment.dict()
                updated = True
                break
        if not updated:
            raise ValueError(f"Adjustment {adjustment.id} not found")
        self._save_json(self.adjustments_file, adjustments)
        if adjustment.audit_trail:
            self._record_audit_event(adjustment.audit_trail[-1])
        return adjustment

    def append_adjustment_audit(self, adjustment_id: str, entry: AdjustmentAuditEntry) -> Optional[TreatmentAdjustment]:
        adjustments = self._load_json(self.adjustments_file)
        updated_item = None
        for idx, item in enumerate(adjustments):
            if item.get('id') == adjustment_id:
                trail = item.setdefault('audit_trail', [])
                trail.append(entry.dict())
                adjustments[idx] = item
                updated_item = TreatmentAdjustment(**item)
                break
        if updated_item is not None:
            self._save_json(self.adjustments_file, adjustments)
            self._record_audit_event(entry)
        return updated_item

    # Observation operations
    def add_observations(self, observations: List[Observation]) -> List[Observation]:
        stored = self._load_json(self.observations_file)
        for observation in observations:
            stored.append(observation.dict())
        self._save_json(self.observations_file, stored)
        return observations

    def list_observations(self, patient_id: str, code: Optional[str] = None) -> List[Observation]:
        stored = self._load_json(self.observations_file)
        result: List[Observation] = []
        for item in stored:
            if item.get('patient_id') != patient_id:
                continue
            if code and item.get('code') != code:
                continue
            result.append(Observation(**item))
        result.sort(key=lambda obs: obs.effective_at, reverse=True)
        return result

    def get_last_observation(self, patient_id: str, code: str) -> Optional[Observation]:
        observations = self.list_observations(patient_id, code)
        return observations[0] if observations else None

    def get_recent_observations(self, patient_id: str, code: str, within_minutes: int) -> List[Observation]:
        cutoff = datetime.now() - timedelta(minutes=within_minutes)
        observations = self.list_observations(patient_id, code)
        return [obs for obs in observations if obs.effective_at >= cutoff]

    # Alert operations
    def create_alert(self, alert: Alert, entry: AlertTimelineEntry) -> Alert:
        alert.timeline.append(entry)
        alert.updated_at = datetime.now()
        return self.save_alert(alert, entry)

    def save_alert(self, alert: Alert, timeline_entry: Optional[AlertTimelineEntry] = None) -> Alert:
        alerts = self._load_json(self.alerts_file)
        updated = False
        alert_dict = alert.dict()
        for idx, item in enumerate(alerts):
            if item.get('id') == alert.id:
                alerts[idx] = alert_dict
                updated = True
                break
        if not updated:
            alerts.append(alert_dict)
        self._save_json(self.alerts_file, alerts)
        if timeline_entry is not None:
            self._record_alert_event(timeline_entry)
        return alert

    def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        alerts = self._load_json(self.alerts_file)
        for item in alerts:
            if item.get('id') == alert_id:
                return Alert(**item)
        return None

    def list_alerts_by_patient(self, patient_id: str, include_closed: bool = False) -> List[Alert]:
        alerts = self._load_json(self.alerts_file)
        result: List[Alert] = []
        for item in alerts:
            if item.get('patient_id') != patient_id:
                continue
            if not include_closed and item.get('status') == AlertStatus.CLOSED:
                continue
            result.append(Alert(**item))
        result.sort(key=lambda alert: alert.created_at, reverse=True)
        return result

    def list_active_alerts(self, patient_id: str) -> List[Alert]:
        alerts = self.list_alerts_by_patient(patient_id, include_closed=False)
        return [alert for alert in alerts if alert.status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)]

    def save_alert_with_entry(self, alert: Alert, entry: AlertTimelineEntry) -> Alert:
        alert.timeline.append(entry)
        alert.updated_at = datetime.now()
        return self.save_alert(alert, entry)

    def _record_alert_event(self, entry: AlertTimelineEntry):
        events = self._load_json(self.alert_events_file)
        events.append(entry.dict())
        self._save_json(self.alert_events_file, events)

    # Care plan revisions
    def create_careplan_revision(self, revision: CarePlanRevision) -> CarePlanRevision:
        revisions = self._load_json(self.careplan_revisions_file)
        revisions.append(revision.dict())
        self._save_json(self.careplan_revisions_file, revisions)
        return revision

    def list_careplan_revisions(self, patient_id: str) -> List[CarePlanRevision]:
        revisions = self._load_json(self.careplan_revisions_file)
        return [CarePlanRevision(**item) for item in revisions if item.get('patient_id') == patient_id]

    # Notifications
    def add_notification(self, notification: Notification) -> Notification:
        notifications = self._load_json(self.notifications_file)
        notifications.append(notification.dict())
        self._save_json(self.notifications_file, notifications)
        return notification

    def list_notifications(self, user_id: str) -> List[Notification]:
        notifications = self._load_json(self.notifications_file)
        return [Notification(**item) for item in notifications if item.get('user_id') == user_id]

    def _record_audit_event(self, entry: AdjustmentAuditEntry):
        audit_entries = self._load_json(self.audit_log_file)
        audit_entries.append(entry.dict())
        self._save_json(self.audit_log_file, audit_entries)

    def calculate_bmi(self, weight: float, height: float) -> float:
        """Calculate BMI from weight (kg) and height (cm)"""
        if height <= 0:
            return 0.0
        height_m = height / 100  # Convert cm to meters
        return round(weight / (height_m ** 2), 1)


# Global database instance
db = SimpleDatabase()
