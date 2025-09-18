from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class PatientORM(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    given_name: Mapped[str | None] = mapped_column(String(120))
    family_name: Mapped[str | None] = mapped_column(String(120))
    gender: Mapped[str | None] = mapped_column(String(32))
    birth_date: Mapped[str | None] = mapped_column(String(32))
    contact: Mapped[dict | None] = mapped_column(JSON)

    encounters: Mapped[list["EncounterORM"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    observations: Mapped[list["ObservationORM"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    alerts: Mapped[list["AlertORM"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class EncounterORM(Base):
    __tablename__ = "encounters"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

    patient: Mapped[PatientORM] = relationship(back_populates="encounters")


class TreatmentAdjustmentORM(Base):
    __tablename__ = "treatment_adjustments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id"), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(64))
    field_path: Mapped[str] = mapped_column(String(255), nullable=False)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient: Mapped[PatientORM] = relationship()
    decision: Mapped["AdjustmentDecisionORM" | None] = relationship(back_populates="adjustment", uselist=False, cascade="all, delete-orphan")
    audit_trail: Mapped[list["AdjustmentAuditEntryORM"]] = relationship(back_populates="adjustment", cascade="all, delete-orphan")


class AdjustmentDecisionORM(Base):
    __tablename__ = "adjustment_decisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    adjustment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("treatment_adjustments.id"), nullable=False, unique=True)
    decided_by: Mapped[str] = mapped_column(String(64), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)

    adjustment: Mapped[TreatmentAdjustmentORM] = relationship(back_populates="decision")


class AdjustmentAuditEntryORM(Base):
    __tablename__ = "adjustment_audit_entries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    adjustment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("treatment_adjustments.id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    adjustment: Mapped[TreatmentAdjustmentORM] = relationship(back_populates="audit_trail")


class ObservationORM(Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    unit: Mapped[str | None] = mapped_column(String(32))
    value_text: Mapped[str] = mapped_column(String(128), nullable=False)
    value_numeric: Mapped[float | None] = mapped_column(Float)
    effective_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient: Mapped[PatientORM] = relationship(back_populates="observations")


class AlertORM(Base):
    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    message: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient: Mapped[PatientORM] = relationship(back_populates="alerts")


__all__ = [
    "PatientORM",
    "EncounterORM",
    "ObservationORM",
    "AlertORM",
    "TreatmentAdjustmentORM",
    "AdjustmentDecisionORM",
    "AdjustmentAuditEntryORM",
]
