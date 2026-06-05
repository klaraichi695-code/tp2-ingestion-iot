"""main.py — Service d'ingestion IoT - Point d'entrée principal."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from models import SensorReading, IngestResponse, ValidationError
from validators import (
    Validator, RequiredFieldsValidator, RangeValidator,
    ConsistencyValidator, run_validators
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ingestion")


def sanitize_log(value: str, max_len: int = 200) -> str:
    """Nettoie une chaîne pour éviter les injections de logs."""
    cleaned = value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "...[TRONQUE]"
    return cleaned


def mask_api_key(key: str) -> str:
    """Masque une clé API pour les logs."""
    if len(key) >= 8:
        return "****" + key[-4:]
    return "****"


# Liste des validateurs
VALIDATORS: List[Validator] = [
    RequiredFieldsValidator(["timestamp", "site_id", "sensor_id"]),
    RangeValidator("temperature_c", -50.0, 60.0),
    RangeValidator("humidity_pct", 0.0, 100.0),
    RangeValidator("soil_moisture", 0.0, 1.0),
    RangeValidator("irrigation_l_min", 0.0, 50.0),
    ConsistencyValidator(),
]


# Données de test
SAMPLE_READINGS = [
    # 1 - Valide
    {"timestamp": "2026-02-16T08:00:00Z", "site_id": "site-alpha", "sensor_id": "sensor-01",
     "temperature_c": 22.5, "humidity_pct": 65.0, "soil_moisture": 0.42,
     "pump_status": "off", "irrigation_l_min": 0.0},
    # 2 - Humidité hors bornes
    {"timestamp": "2026-02-16T08:05:00Z", "site_id": "site-alpha", "sensor_id": "sensor-02",
     "temperature_c": 23.1, "humidity_pct": 150.0, "soil_moisture": 0.38,
     "pump_status": "off", "irrigation_l_min": 0.0},
    # 3 - sensor_id vide + pompe ON sans débit
    {"timestamp": "2026-02-16T08:10:00Z", "site_id": "site-beta", "sensor_id": "",
     "temperature_c": 19.8, "humidity_pct": 70.2, "soil_moisture": 0.55,
     "pump_status": "on", "irrigation_l_min": 0.0},
    # 4 - Température hors bornes
    {"timestamp": "2026-02-16T08:15:00Z", "site_id": "site-beta", "sensor_id": "sensor-04",
     "temperature_c": -60.0, "humidity_pct": 72.0, "soil_moisture": 0.60,
     "pump_status": "on", "irrigation_l_min": 3.5},
    # 5 - timestamp vide
    {"timestamp": "", "site_id": "site-gamma", "sensor_id": "sensor-05",
     "temperature_c": 25.0, "humidity_pct": 55.0, "soil_moisture": None,
     "pump_status": "off", "irrigation_l_min": 0.0},
]


def process_ingestion(raw_readings: List[dict], api_key: str) -> IngestResponse:
    """Traite une requête d'ingestion."""
    request_id = str(uuid.uuid4())
    logger.info("Requête | id=%s | api_key=%s | nb=%d",
                request_id, mask_api_key(api_key), len(raw_readings))
    
    accepted = []
    all_errors = []
    
    for i, raw in enumerate(raw_readings):
        sensor_id = sanitize_log(str(raw.get("sensor_id", "?")))
        
        errors = run_validators(raw, VALIDATORS)
        
        if errors:
            logger.warning("Reading #%d (sensor=%s) : %d erreur(s)", i, sensor_id, len(errors))
            for err in errors:
                logger.warning("  -> [%s] %s", err.code, err.message)
                all_errors.append(err)
        else:
            try:
                reading = SensorReading.from_dict(raw)
                accepted.append(reading)
                logger.info("Reading #%d (sensor=%s) : ACCEPTE", i, sensor_id)
            except (ValueError, TypeError) as e:
                err = ValidationError("__construction__", "BUILD_ERROR", str(e))
                all_errors.append(err)
                logger.warning("Reading #%d (sensor=%s) : REJETE construction: %s", i, sensor_id, e)
    
    rejected = len(raw_readings) - len(accepted)
    
    if rejected == 0:
        status = "ok"
    elif len(accepted) > 0:
        status = "partial"
    else:
        status = "error"
    
    response = IngestResponse(
        status=status,
        accepted_count=len(accepted),
        rejected_count=rejected,
        errors=all_errors
    )
    
    logger.info("Reponse | status=%s | accepted=%d | rejected=%d",
                status, len(accepted), rejected)
    return response


if __name__ == "__main__":
    print("=" * 60)
    print("SERVICE D'INGESTION IoT - TP2")
    print("=" * 60)
    
    result = process_ingestion(SAMPLE_READINGS, api_key="sk-secret-key-12345678")
    
    print("\n--- REPONSE JSON ---")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    
    # ========== VALIDATIONS ==========
    print("\n--- VERIFICATIONS ---")
    
    # 1. Sérialisation SensorReading
    valid_data = SAMPLE_READINGS[0]
    r1 = SensorReading.from_dict(valid_data)
    r2 = SensorReading.from_dict(r1.to_dict())
    assert r1 == r2
    print("[OK] Cycle serialisation SensorReading")
    
    # 2. Cycle JSON complet
    r3 = SensorReading.from_dict(json.loads(json.dumps(r1.to_dict())))
    assert r1 == r3
    print("[OK] Cycle JSON complet")
    
    # 3. sensor_id vide → ValueError
    try:
        SensorReading.from_dict({
            "timestamp": "t", "site_id": "s", "sensor_id": "",
            "temperature_c": 20, "humidity_pct": 50
        })
        assert False
    except ValueError:
        print("[OK] sensor_id vide detecte")
    
    # 4. humidite 150 → OUT_OF_RANGE
    errors = run_validators(SAMPLE_READINGS[1], VALIDATORS)
    assert any(e.code == "OUT_OF_RANGE" and e.field == "humidity_pct" for e in errors)
    print("[OK] humidite 150 detectee")
    
    # 5. sensor_id vide + incohérence pompe
    errors = run_validators(SAMPLE_READINGS[2], VALIDATORS)
    assert any(e.code == "EMPTY_FIELD" for e in errors)
    assert any(e.code == "CONSISTENCY_ERROR" for e in errors)
    print("[OK] 2 erreurs detectees (vide + coherence)")
    
    # 6. temperature -60 → OUT_OF_RANGE
    errors = run_validators(SAMPLE_READINGS[3], VALIDATORS)
    assert any(e.code == "OUT_OF_RANGE" and e.field == "temperature_c" for e in errors)
    print("[OK] temperature -60 detectee")
    
    # 7. Masquage API key
    assert mask_api_key("sk-abcdef1234") == "****1234"
    assert mask_api_key("short") == "****"
    print("[OK] mask_api_key")
    
    # 8. Sanitization
    malicious = "sensor-01\nERROR: hacked"
    assert "\n" not in sanitize_log(malicious)
    print("[OK] sanitize_log")
    
    # 9. api_key exclue des dictionnaires
    from models import IngestRequest
    req = IngestRequest(request_id="id", api_key="secret", readings=[r1])
    assert "api_key" not in req.to_dict()
    print("[OK] api_key exclue")
    
    # 10. Résultat global
    assert result.accepted_count == 1
    assert result.rejected_count == 4
    assert result.status == "partial"
    print("[OK] Resultat: 1 accepte, 4 rejetes, status=partial")
    
    print("\n" + "=" * 60)
    print("✅ TOUTES LES VALIDATIONS SONT PASSEES")
    print("=" * 60)