from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models import (
    Observation,
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertTimelineEntry,
)
from ..database import db


class AlertEngine:
    """Rule-based alert evaluation for physiological observations."""

    THRESHOLD_RULES = [
        {
            "rule": "low_spo2",
            "code": "spo2",
            "operator": "lt",
            "value": 88.0,
            "severity": AlertSeverity.CRITICAL,
            "message": "SpO2 por debajo de 88%",
        },
        {
            "rule": "low_glucose",
            "code": "glucose",
            "operator": "lt",
            "value": 54.0,
            "severity": AlertSeverity.CRITICAL,
            "message": "Glucosa por debajo de 54 mg/dL",
        },
    ]

    HEART_RATE_CODES = {"heart_rate", "hr"}
    MISSING_DATA_RULE_ID = "missing_data"

    ALLOWED_TRANSITIONS = {
        AlertStatus.OPEN: {AlertStatus.ACKNOWLEDGED},
        AlertStatus.ACKNOWLEDGED: {AlertStatus.RESOLVED},
        AlertStatus.RESOLVED: {AlertStatus.CLOSED},
    }

    def __init__(self):
        self.db = db

    def process_observations(self, patient_id: str, observations: List[Observation]) -> List[Alert]:
        if not observations:
            return []

        # Persist observations
        self.db.add_observations(observations)

        generated: List[Alert] = []
        for observation in observations:
            observation.code = observation.code.lower()
            generated.extend(self._evaluate_threshold_rules(observation))
            delta_alert = self._evaluate_delta_rule(observation)
            if delta_alert:
                generated.append(delta_alert)

        # Any new data resolves missing-data alerts automatically
        self._resolve_missing_data_alert(patient_id)
        return [alert for alert in generated if alert is not None]

    def evaluate_missing_data(self, patient_id: str) -> Optional[Alert]:
        if not self.db.list_careplan_revisions(patient_id):
            return None

        observations = self.db.list_observations(patient_id)
        if not observations:
            return None

        latest = observations[0]
        if datetime.now() - latest.effective_at < timedelta(hours=12):
            return None

        if self._find_active_alert(patient_id, self.MISSING_DATA_RULE_ID):
            return None

        context = {
            "rule": self.MISSING_DATA_RULE_ID,
            "message": "Sin observaciones en mas de 12 horas",
            "lastObservationAt": latest.effective_at.isoformat(),
        }
        alert = Alert(
            patient_id=patient_id,
            code="missing-data",
            value=0,
            unit=None,
            observed_at=latest.effective_at,
            severity=AlertSeverity.INFO,
            context=context,
        )
        entry = AlertTimelineEntry(
            alert_id=alert.id,
            status=AlertStatus.OPEN,
            notes=context["message"],
        )
        return self.db.create_alert(alert, entry)

    def transition_alert(
        self,
        alert: Alert,
        new_status: AlertStatus,
        actor_id: Optional[str],
        notes: Optional[str] = None,
        *,
        force: bool = False,
    ) -> Alert:
        if not force:
            allowed = self.ALLOWED_TRANSITIONS.get(alert.status, set())
            if new_status not in allowed:
                raise ValueError(f"Transition {alert.status.value} -> {new_status.value} no permitida")

        now = datetime.now()
        if new_status == AlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = now
            alert.acknowledged_by = actor_id
            alert.context["time_to_ack_seconds"] = (now - alert.created_at).total_seconds()
        elif new_status == AlertStatus.RESOLVED:
            reference = alert.acknowledged_at or alert.created_at
            alert.resolved_at = now
            alert.resolved_by = actor_id
            if reference:
                alert.context["time_to_resolve_seconds"] = (now - reference).total_seconds()
        elif new_status == AlertStatus.CLOSED:
            alert.closed_at = now
            alert.closed_by = actor_id
            alert.context["time_to_close_seconds"] = (now - alert.created_at).total_seconds()

        alert.status = new_status
        entry = AlertTimelineEntry(
            alert_id=alert.id,
            status=new_status,
            actor_id=actor_id,
            notes=notes,
        )
        return self.db.save_alert_with_entry(alert, entry)

    def _evaluate_threshold_rules(self, observation: Observation) -> List[Alert]:
        generated: List[Alert] = []
        value = self._to_float(observation.value)
        if value is None:
            return generated

        for rule in self.THRESHOLD_RULES:
            if observation.code != rule["code"]:
                continue
            if rule["operator"] == "lt" and value < rule["value"]:
                alert = self._raise_alert(
                    observation,
                    rule_id=rule["rule"],
                    severity=rule["severity"],
                    message=rule["message"],
                    extras={"threshold": rule["value"]},
                )
                if alert:
                    generated.append(alert)
        return generated

    def _evaluate_delta_rule(self, observation: Observation) -> Optional[Alert]:
        normalized_code = observation.code.lower()
        if normalized_code not in self.HEART_RATE_CODES:
            return None

        current_value = self._to_float(observation.value)
        if current_value is None:
            return None

        recent = self.db.get_recent_observations(observation.patient_id, normalized_code, within_minutes=10)
        previous = None
        for candidate in recent:
            if candidate.effective_at < observation.effective_at:
                previous = candidate
                break
        if not previous:
            return None

        previous_value = self._to_float(previous.value)
        if previous_value is None:
            return None

        delta = current_value - previous_value
        if delta <= 40:
            return None

        rule_id = "hr_delta_spike"
        message = f"Incremento de {delta:.1f} bpm en menos de 10 minutos"
        return self._raise_alert(
            observation,
            rule_id=rule_id,
            severity=AlertSeverity.WARNING,
            message=message,
            extras={
                "delta": delta,
                "baseline": previous_value,
                "baseline_at": previous.effective_at.isoformat(),
            },
        )

    def _resolve_missing_data_alert(self, patient_id: str) -> Optional[Alert]:
        active = self._find_active_alert(patient_id, self.MISSING_DATA_RULE_ID)
        if not active:
            return None

        try:
            alert = self.transition_alert(active, AlertStatus.ACKNOWLEDGED, actor_id="system", notes="Datos retomados", force=True)
            alert = self.transition_alert(alert, AlertStatus.RESOLVED, actor_id="system", notes="Resolucion automatica", force=True)
            alert = self.transition_alert(alert, AlertStatus.CLOSED, actor_id="system", notes="Cierre automatico", force=True)
            return alert
        except ValueError:
            return None

    def _raise_alert(
        self,
        observation: Observation,
        *,
        rule_id: str,
        severity: AlertSeverity,
        message: str,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Optional[Alert]:
        if self._find_active_alert(observation.patient_id, rule_id):
            return None

        context: Dict[str, Any] = {"rule": rule_id, "message": message}
        if extras:
            context.update(extras)

        numeric_value = self._to_float(observation.value)
        alert = Alert(
            patient_id=observation.patient_id,
            code=observation.code,
            value=numeric_value if numeric_value is not None else observation.value,
            unit=observation.unit,
            observed_at=observation.effective_at,
            severity=severity,
            context=context,
        )
        entry = AlertTimelineEntry(
            alert_id=alert.id,
            status=AlertStatus.OPEN,
            notes=message,
        )
        return self.db.create_alert(alert, entry)

    def _find_active_alert(self, patient_id: str, rule_id: str) -> Optional[Alert]:
        for alert in self.db.list_active_alerts(patient_id):
            if alert.context.get("rule") == rule_id:
                return alert
        return None

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None


alert_engine = AlertEngine()
def basic_threshold_alerts(code: str, numeric_value: Optional[float]) -> List[Dict[str, str]]:
    """Evaluate simple threshold-based alerts for a single observation."""
    if numeric_value is None:
        return []

    normalized = code.lower()
    alerts: List[Dict[str, str]] = []

    if normalized in {"spo2", "oxygen_saturation"} and numeric_value < 88:
        alerts.append({
            "rule": "low_spo2",
            "severity": "critical",
            "message": "SpO2 below 88%",
        })

    if normalized == "glucose" and numeric_value < 54:
        alerts.append({
            "rule": "low_glucose",
            "severity": "critical",
            "message": "Glucose below 54 mg/dL",
        })

    return alerts
