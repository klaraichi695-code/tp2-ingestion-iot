"""models.py — Contrats de données pour le service d'ingestion IoT."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ValidationError:
    """Erreur de validation structurée."""
    field: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"field": self.field, "code": self.code, "message": self.message}


@dataclass
class SensorReading:
    """Mesure d'un capteur IoT."""
    timestamp: str
    site_id: str
    sensor_id: str
    temperature_c: float
    humidity_pct: float
    soil_moisture: Optional[float] = None
    pump_status: str = "off"
    irrigation_l_min: float = 0.0

    def __post_init__(self):
        if not self.sensor_id or not self.sensor_id.strip():
            raise ValueError("sensor_id est obligatoire et ne peut pas être vide")

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "site_id": self.site_id,
            "sensor_id": self.sensor_id,
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "soil_moisture": self.soil_moisture,
            "pump_status": self.pump_status,
            "irrigation_l_min": self.irrigation_l_min,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SensorReading":
        return cls(
            timestamp=str(data.get("timestamp", "")),
            site_id=str(data.get("site_id", "")),
            sensor_id=str(data.get("sensor_id", "")),
            temperature_c=float(data.get("temperature_c", 0.0)),
            humidity_pct=float(data.get("humidity_pct", 0.0)),
            soil_moisture=float(data["soil_moisture"]) if data.get("soil_moisture") is not None else None,
            pump_status=str(data.get("pump_status", "off")).lower(),
            irrigation_l_min=float(data.get("irrigation_l_min", 0.0)),
        )


@dataclass
class IngestRequest:
    """Requête d'ingestion."""
    request_id: str
    api_key: str
    readings: List[SensorReading] = field(default_factory=list)
    sent_at: str = ""

    def to_dict(self) -> dict:
        # L'api_key est volontairement exclue
        return {
            "request_id": self.request_id,
            "sent_at": self.sent_at,
            "readings": [r.to_dict() for r in self.readings],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IngestRequest":
        readings = [SensorReading.from_dict(r) for r in data.get("readings", [])]
        return cls(
            request_id=str(data.get("request_id", "")),
            api_key=str(data.get("api_key", "")),
            readings=readings,
            sent_at=str(data.get("sent_at", "")),
        )


@dataclass
class IngestResponse:
    """Réponse du service d'ingestion."""
    status: str
    accepted_count: int = 0
    rejected_count: int = 0
    errors: List[ValidationError] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "errors": [e.to_dict() for e in self.errors],
        }