import os
import json
import subprocess
import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from .config import get_settings
from .services.openai_service import OpenAIAnalyzer, FallbackAnalyzer
from .services.alert_engine import AlertEngine, basic_threshold_alerts
from .services.icd10_suggester import icd10_suggester
from .services.calculators import calculators, CalculatorError
from .services.observation_validator import (
    ObservationValidationError,
    validate_observation,
)
from .models import (
    User, ClinicalRecord, PatientAccess, UserType, VitalSigns,
    LoginRequest, RegisterRequest, ClinicalRecordRequest, SharePatientRequest,
    PatientRegistrationRequest, TreatmentAdjustment, AdjustmentCreatePayload,
    AdjustmentDecisionPayload, AdjustmentStatus, AdjustmentDecision,
    AdjustmentAuditEntry, CarePlanRevision, Notification, NotificationSeverity,
    ObservationBatchRequest, Observation, AlertStatusUpdate, AlertStatus
)
from .database import db
from .db.session import get_session
from .db.models import AlertORM, ObservationORM, PatientORM
from .auth import hash_password, verify_password, create_token, get_current_user, get_current_doctor, get_current_patient


class AnalyzeRequest(BaseModel):
    case_text: str = Field(..., min_length=10, description="Free-text clinical case description")


class DifferentialItem(BaseModel):
    condition: str
    probability: Optional[str] = None
    rationale: str


class TestSuggestion(BaseModel):
    name: str
    rationale: Optional[str] = None


class AnalyzeResponse(BaseModel):
    differentials: List[DifferentialItem]
    tests: List[TestSuggestion]
    notes: Optional[str] = None

class ICD10SuggestRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Clinical narration")
    review_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)



class TerminalRequest(BaseModel):
    command: str = Field(..., min_length=1, description="Command to execute")
    working_dir: Optional[str] = Field(None, description="Working directory for command execution")


class TerminalResponse(BaseModel):
    output: str
    error: str
    return_code: int
    command: str


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MedicAI - Clinical Assistant MVP", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Initialize analyzers
    openai_api_key = settings.openai_api_key
    model = settings.openai_model
    openai_enabled = bool(openai_api_key)

    openai_analyzer: Optional[OpenAIAnalyzer] = None
    if openai_enabled:
        openai_analyzer = OpenAIAnalyzer(api_key=openai_api_key, model=model)
    fallback_analyzer = FallbackAnalyzer()
    alerts_engine = AlertEngine()

    @app.post("/analyze", response_model=AnalyzeResponse)
    async def analyze_case(payload: AnalyzeRequest) -> Any:
        text = payload.case_text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Empty case text")

        # Try OpenAI first if configured; otherwise use fallback
        if openai_analyzer is not None:
            try:
                result = await openai_analyzer.analyze(text)
                return AnalyzeResponse(**result)
            except Exception as e:  # noqa: BLE001
                # Fall back gracefully
                result = await fallback_analyzer.analyze(text)
                return AnalyzeResponse(**result)
        else:
            result = await fallback_analyzer.analyze(text)
            return AnalyzeResponse(**result)

    # Serve frontend
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if os.path.isdir(frontend_dir):
        app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="ui")

        @app.get("/")
        async def root_redirect() -> RedirectResponse:  # type: ignore[override]
            # Prefer welcome page if present
            welcome_path = os.path.join(frontend_dir, "welcome.html")
            if os.path.exists(welcome_path):
                return RedirectResponse(url="/ui/welcome.html")
            return RedirectResponse(url="/ui/")
    else:
        @app.get("/")
        async def root() -> Dict[str, str]:  # type: ignore[override]
            return {
                "message": "MedicAI API is running",
                "try": "/docs, /health, POST /analyze, POST /terminal",
            }

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    # Authentication endpoints
    @app.post("/auth/register")
    async def register(payload: RegisterRequest) -> Dict[str, Any]:
        """Register a new user (doctor or patient)"""
        try:
            user = User(
                email=payload.email,
                password_hash=hash_password(payload.password),
                user_type=payload.user_type,
                full_name=payload.full_name,
                license_number=payload.license_number,
                specialization=payload.specialization,
                date_of_birth=payload.date_of_birth,
                phone=payload.phone
            )
            
            created_user = db.create_user(user)
            token = create_token(created_user.id, created_user.user_type)
            
            return {
                "message": "User registered successfully",
                "token": token,
                "user": {
                    "id": created_user.id,
                    "email": created_user.email,
                    "full_name": created_user.full_name,
                    "user_type": created_user.user_type
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/auth/login")
    async def login(payload: LoginRequest) -> Dict[str, Any]:
        """Login user"""
        user = db.get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        token = create_token(user.id, user.user_type)
        
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "user_type": user.user_type
            }
        }

    # Clinical record endpoints
    @app.post("/clinical-records")
    async def create_clinical_record(
        payload: ClinicalRecordRequest,
        current_user: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        """Create a new clinical record (doctors only)"""
        # Analyze the case using AI
        if openai_analyzer is not None:
            try:
                result = await openai_analyzer.analyze(payload.case_text)
            except Exception:
                result = await fallback_analyzer.analyze(payload.case_text)
        else:
            result = await fallback_analyzer.analyze(payload.case_text)
        
        # Create clinical record
        record = ClinicalRecord(
            patient_id=payload.case_text,  # In real app, this would be patient_id from request
            doctor_id=current_user.id,
            case_text=payload.case_text,
            differentials=result.get("differentials", []),
            tests=result.get("tests", []),
            notes=result.get("notes"),
            vital_signs=payload.vital_signs,
            symptoms=payload.symptoms
        )
        
        created_record = db.create_clinical_record(record)
        
        return {
            "message": "Clinical record created successfully",
            "record": {
                "id": created_record.id,
                "case_text": created_record.case_text,
                "differentials": created_record.differentials,
                "tests": created_record.tests,
                "notes": created_record.notes,
                "created_at": created_record.created_at
            }
        }

    @app.post("/patients/register")
    async def register_patient(
        patient_data: PatientRegistrationRequest,
        current_user: User = Depends(get_current_doctor)
    ):
        """Register a new patient with comprehensive clinical data"""
        try:
            # Calculate BMI if weight and height are provided
            bmi = None
            if patient_data.vital_signs.weight and patient_data.vital_signs.height:
                bmi = db.calculate_bmi(patient_data.vital_signs.weight, patient_data.vital_signs.height)
                patient_data.vital_signs.bmi = bmi
            
            # Create patient user
            patient = User(
                full_name=patient_data.full_name,
                email=f"patient_{patient_data.full_name.replace(' ', '_').lower()}@temp.com",  # Temporary email
                password_hash="",  # No password for code-based access
                user_type=UserType.PATIENT,
                date_of_birth=datetime.fromisoformat(patient_data.date_of_birth) if patient_data.date_of_birth else None,
                phone=patient_data.phone,
                emergency_contact=patient_data.emergency_contact
            )
            
            created_patient = db.create_user(patient)
            
            # Create comprehensive clinical record
            record = ClinicalRecord(
                patient_id=created_patient.id,
                doctor_id=current_user.id,
                case_text=patient_data.reason_for_visit or "Initial consultation",
                differentials=[],
                tests=[],
                notes="",
                vital_signs=patient_data.vital_signs,
                allergies=patient_data.allergies,
                current_medications=patient_data.current_medications,
                past_history=patient_data.past_history,
                family_history=patient_data.family_history,
                reason_for_visit=patient_data.reason_for_visit,
                physical_examination=patient_data.physical_examination,
                assessment=patient_data.assessment,
                diagnosis=patient_data.diagnosis,
                treatment_plan=patient_data.treatment_plan,
                follow_up=patient_data.follow_up
            )
            
            created_record = db.create_clinical_record(record)
            
            return {
                "message": "Patient registered successfully",
                "patient_code": created_patient.patient_code,
                "patient_name": created_patient.full_name,
                "record_id": created_record.id
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/clinical-records/my-patients")
    async def get_my_patients_records(
        current_user: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        """Get all clinical records for patients I have access to"""
        accesses = db.get_doctor_accesses(current_user.id)
        patient_ids = [access.patient_id for access in accesses]
        
        all_records = []
        for patient_id in patient_ids:
            records = db.get_patient_records(patient_id)
            all_records.extend(records)
        
        # Sort by creation date (newest first)
        all_records.sort(key=lambda x: x.created_at, reverse=True)
        
        return {
            "records": [
                {
                    "id": record.id,
                    "patient_id": record.patient_id,
                    "case_text": record.case_text,
                    "differentials": record.differentials,
                    "tests": record.tests,
                    "created_at": record.created_at
                }
                for record in all_records
            ]
        }

    @app.get("/clinical-records/my-history")
    async def get_my_history(
        current_user: User = Depends(get_current_patient)
    ) -> Dict[str, Any]:
        """Get my clinical history (patients only)"""
        records = db.get_patient_records(current_user.id)
        records.sort(key=lambda x: x.created_at, reverse=True)
        
        return {
            "records": [
                {
                    "id": record.id,
                    "doctor_id": record.doctor_id,
                    "case_text": record.case_text,
                    "differentials": record.differentials,
                    "tests": record.tests,
                    "created_at": record.created_at
                }
                for record in records
            ]
        }

    @app.get("/patients/lookup/{patient_code}")
    async def lookup_patient_by_code(patient_code: str) -> Dict[str, Any]:
        """Look up patient by code and return their clinical records"""
        patient = db.get_patient_by_code(patient_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        records = db.get_patient_records(patient.id)
        records.sort(key=lambda x: x.created_at, reverse=True)
        
        return {
            "patient": {
                "name": patient.full_name,
                "date_of_birth": patient.date_of_birth,
                "phone": patient.phone,
                "emergency_contact": patient.emergency_contact
            },
            "records": [
                {
                    "id": record.id,
                    "case_text": record.case_text,
                    "differentials": record.differentials,
                    "tests": record.tests,
                    "vital_signs": record.vital_signs,
                    "allergies": record.allergies,
                    "current_medications": record.current_medications,
                    "past_history": record.past_history,
                    "family_history": record.family_history,
                    "reason_for_visit": record.reason_for_visit,
                    "physical_examination": record.physical_examination,
                    "assessment": record.assessment,
                    "diagnosis": record.diagnosis,
                    "treatment_plan": record.treatment_plan,
                    "follow_up": record.follow_up,
                    "created_at": record.created_at
                }
                for record in records
            ]
        }

    @app.post("/patients/share")
    async def share_patient(
        payload: SharePatientRequest,
        current_user: User = Depends(get_current_patient)
    ) -> Dict[str, Any]:
        """Share patient records with a doctor"""
        if payload.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only share your own records"
            )
        
        doctor = db.get_user_by_email(payload.doctor_email)
        if not doctor or doctor.user_type != UserType.DOCTOR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found"
            )
        
        # Check if access already exists
        if db.has_patient_access(doctor.id, current_user.id):
            return {"message": "Doctor already has access to your records"}
        
        access = PatientAccess(
            patient_id=current_user.id,
            doctor_id=doctor.id,
            access_level=payload.access_level
        )
        
        db.grant_patient_access(access)
        
        return {
            "message": f"Access granted to Dr. {doctor.full_name}",
            "doctor": {
                "id": doctor.id,
                "name": doctor.full_name,
                "specialization": doctor.specialization
            }
        }


    @app.post("/adjustments", status_code=status.HTTP_201_CREATED)
    async def create_adjustment_request(
        payload: AdjustmentCreatePayload,
        current_patient: User = Depends(get_current_patient)
    ) -> Dict[str, Any]:
        if payload.patient_id != current_patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create adjustments for your own profile"
            )

        adjustment = TreatmentAdjustment(
            patient_id=current_patient.id,
            requested_by=current_patient.id,
            order_id=payload.order_id,
            field_path=payload.field_path,
            new_value=payload.new_value,
            reason=payload.reason,
        )

        audit_entry = AdjustmentAuditEntry(
            adjustment_id=adjustment.id,
            actor_id=current_patient.id,
            actor_role=current_patient.user_type,
            action="requested",
            notes=payload.reason,
        )
        adjustment.audit_trail.append(audit_entry)

        adjustment = db.create_adjustment(adjustment)

        return {"adjustment": adjustment.dict()}


    @app.get("/adjustments")
    async def list_adjustment_requests(
        status_filter: Optional[str] = None,
        patient_id: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        status_enum: Optional[AdjustmentStatus] = None
        if status_filter is not None:
            try:
                status_enum = AdjustmentStatus(status_filter)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter"
                ) from exc

        if current_user.user_type == UserType.PATIENT:
            if patient_id and patient_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Patients can only view their own adjustments"
                )
            adjustments = db.list_patient_adjustments(current_user.id)
        else:
            adjustments = db.list_all_adjustments()
            if patient_id:
                adjustments = [adj for adj in adjustments if adj.patient_id == patient_id]
            else:
                adjustments = [
                    adj for adj in adjustments
                    if adj.status in (AdjustmentStatus.REQUESTED, AdjustmentStatus.UNDER_REVIEW)
                ]

        if status_enum is not None:
            adjustments = [adj for adj in adjustments if adj.status == status_enum]

        return {"adjustments": [adj.dict() for adj in adjustments]}

    @app.post("/adjustments/{adjustment_id}/decision")
    async def decide_adjustment_request(
        adjustment_id: str,
        payload: AdjustmentDecisionPayload,
        current_doctor: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        adjustment = db.get_adjustment_by_id(adjustment_id)
        if adjustment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adjustment not found"
            )

        if adjustment.status not in (AdjustmentStatus.REQUESTED, AdjustmentStatus.UNDER_REVIEW):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment request has already been resolved"
            )

        adjustment.status = payload.status
        adjustment.decision = AdjustmentDecision(
            decided_by=current_doctor.id,
            status=payload.status,
            rationale=payload.rationale,
        )

        audit_entry = AdjustmentAuditEntry(
            adjustment_id=adjustment.id,
            actor_id=current_doctor.id,
            actor_role=current_doctor.user_type,
            action=f"decision:{payload.status.value}",
            notes=payload.rationale,
        )
        adjustment.audit_trail.append(audit_entry)

        adjustment = db.update_adjustment(adjustment)

        revision_dict: Optional[Dict[str, Any]] = None
        if payload.status == AdjustmentStatus.APPROVED:
            revision = CarePlanRevision(
                patient_id=adjustment.patient_id,
                order_id=adjustment.order_id,
                field_path=adjustment.field_path,
                value=adjustment.new_value,
                revised_from=adjustment.order_id,
                created_by=current_doctor.id,
            )
            db.create_careplan_revision(revision)
            revision_dict = revision.dict()

        severity = NotificationSeverity.INFO if payload.status == AdjustmentStatus.APPROVED else NotificationSeverity.WARNING
        notification = Notification(
            user_id=adjustment.patient_id,
            title="Solicitud de ajuste actualizada",
            message=(
                "Tu solicitud de ajuste fue aprobada. Ingresa a MedicAI para revisar los detalles."
                if payload.status == AdjustmentStatus.APPROVED
                else "Tu solicitud de ajuste fue rechazada. Ingresa a MedicAI para revisar los detalles."
            ),
            severity=severity,
            metadata={"adjustmentId": adjustment.id, "status": payload.status.value},
        )
        db.add_notification(notification)

        return {
            "adjustment": adjustment.dict(),
            "carePlanRevision": revision_dict,
            "notification": notification.dict(),
        }


    @app.post("/icd10/suggest")
    async def suggest_icd10_codes(
        payload: ICD10SuggestRequest,
        current_user: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        suggestions = icd10_suggester.suggest(
            payload.text,
            review_threshold=payload.review_threshold
        )
        return {"codes": suggestions}

    @app.get("/calculate")
    async def calculate_tool(
        tool: str,
        inputs: Optional[str] = None,
        current_user: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        try:
            parsed_inputs = json.loads(inputs) if inputs else {}
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="inputs must be valid JSON"
            ) from exc

        try:
            result = calculators.calculate(tool, parsed_inputs)
        except CalculatorError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc

        return result

    @app.post("/observations/batch", status_code=status.HTTP_202_ACCEPTED)
    async def ingest_observation_batch(
        payload: ObservationBatchRequest,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> Dict[str, Any]:
        if current_user.user_type == UserType.PATIENT and payload.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients can only submit observations for themselves"
            )
        if not payload.observations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one observation is required"
            )

        generated_alerts: List[Dict[str, str]] = []
        accepted = 0

        try:
            patient = session.get(PatientORM, payload.patient_id)
            if patient is None:
                patient = PatientORM(id=payload.patient_id)
                session.add(patient)

            for obs_input in payload.observations:
                normalized_code, numeric_value = validate_observation(
                    obs_input.code,
                    obs_input.unit,
                    obs_input.value,
                )

                observation_row = ObservationORM(
                    patient_id=payload.patient_id,
                    code=normalized_code,
                    unit=obs_input.unit.lower() if obs_input.unit else None,
                    value_text=str(obs_input.value),
                    value_numeric=numeric_value,
                    effective_at=obs_input.effective_at,
                    source=obs_input.source or "manual",
                )
                session.add(observation_row)
                accepted += 1

                for alert in basic_threshold_alerts(normalized_code, numeric_value):
                    alert_row = AlertORM(
                        patient_id=payload.patient_id,
                        code=normalized_code,
                        rule=alert["rule"],
                        severity=alert["severity"],
                        message=alert["message"],
                        observed_at=obs_input.effective_at,
                    )
                    session.add(alert_row)
                    generated_alerts.append(alert)

            session.commit()
        except ObservationValidationError as exc:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
        except Exception:
            session.rollback()
            raise

        return {"ingested": accepted, "generatedAlerts": generated_alerts}

    @app.post("/alerts/{alert_id}/status")
    async def update_alert_status(
        alert_id: str,
        payload: AlertStatusUpdate,
        current_user: User = Depends(get_current_doctor)
    ) -> Dict[str, Any]:
        alert = db.get_alert_by_id(alert_id)
        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

        try:
            updated = alerts_engine.transition_alert(
                alert,
                payload.status,
                actor_id=current_user.id,
                notes=payload.notes
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc

        return {"alert": updated.dict()}

    @app.get("/dashboard/{patient_id}")
    async def get_dashboard_summary(
        patient_id: str,
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        if current_user.user_type == UserType.PATIENT and patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients can only view their own dashboard"
            )

        patient = db.get_user_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        alerts_engine.evaluate_missing_data(patient_id)

        observations = db.list_observations(patient_id)
        last_vitals: Dict[str, Dict[str, Any]] = {}
        for obs in observations:
            if obs.code not in last_vitals:
                last_vitals[obs.code] = {
                    "value": obs.value,
                    "unit": obs.unit,
                    "timestamp": obs.effective_at,
                }

        series_map: Dict[str, List[Observation]] = {}
        for obs in observations:
            series_map.setdefault(obs.code, []).append(obs)

        timeseries: List[Dict[str, Any]] = []
        for code, series in series_map.items():
            recent = list(reversed(series[:10]))
            timeseries.append({
                "code": code,
                "points": [
                    {"t": item.effective_at, "v": item.value}
                    for item in recent
                ],
            })

        active_alerts = db.list_active_alerts(patient_id)
        alert_items = db.list_alerts_by_patient(patient_id, include_closed=False)
        alerts_payload = [
            {
                "id": alert.id,
                "code": alert.code,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "observedAt": alert.observed_at,
                "message": alert.context.get("message"),
                "acknowledgedAt": alert.acknowledged_at,
                "resolvedAt": alert.resolved_at,
                "closedAt": alert.closed_at,
            }
            for alert in alert_items
        ]

        careplan_active = bool(db.list_careplan_revisions(patient_id))

        return {
            "patientId": patient_id,
            "patientName": patient.full_name,
            "careplanActive": careplan_active,
            "activeAlerts": len(active_alerts),
            "alerts": alerts_payload,
            "lastVitals": last_vitals,
            "timeseries": timeseries,
            "adherenceRate": None,
        }

    @app.get("/notifications")
    async def list_notifications(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
        notifications = db.list_notifications(current_user.id)
        return {"notifications": [note.dict() for note in notifications]}

    @app.get("/doctors")
    async def get_doctors() -> Dict[str, Any]:
        """Get list of all doctors"""
        doctors = db.get_doctors()
        return {
            "doctors": [
                {
                    "id": doctor.id,
                    "full_name": doctor.full_name,
                    "specialization": doctor.specialization,
                    "license_number": doctor.license_number
                }
                for doctor in doctors
            ]
        }

    @app.post("/terminal", response_model=TerminalResponse)
    async def execute_command(payload: TerminalRequest) -> Any:
        """Execute terminal command with security restrictions"""
        command = payload.command.strip()
        working_dir = payload.working_dir or os.getcwd()
        
        # Security: Only allow safe commands for development
        allowed_commands = [
            "python", "pip", "uvicorn", "ls", "dir", "pwd", "cd", "cat", "type",
            "echo", "git", "npm", "node", "python3", "pip3"
        ]
        
        # Check if command starts with allowed command
        command_parts = command.split()
        if not command_parts or not any(command_parts[0].startswith(cmd) for cmd in allowed_commands):
            raise HTTPException(
                status_code=400, 
                detail=f"Command not allowed. Allowed commands: {', '.join(allowed_commands)}"
            )
        
        # Additional security: prevent dangerous operations
        dangerous_patterns = ["rm -rf", "del /s", "format", "shutdown", "reboot", "sudo", "su"]
        if any(pattern in command.lower() for pattern in dangerous_patterns):
            raise HTTPException(
                status_code=400, 
                detail="Dangerous command detected and blocked"
            )
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return TerminalResponse(
                output=stdout.decode('utf-8', errors='replace'),
                error=stderr.decode('utf-8', errors='replace'),
                return_code=process.returncode,
                command=command
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Command execution failed: {str(e)}"
            )

    return app


app = create_app()



