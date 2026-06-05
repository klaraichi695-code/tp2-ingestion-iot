# TP2 – Service d'Ingestion IoT
## Objectif

Construire un service d'ingestion IoT avec validation cumulative des données, sérialisation JSON et logging sécurisé.

---

## Prérequis

- Python 3.11+

---

## Installation

```bash
cd TPs/TP2_Ingestion_IoT
# Pas de dépendances externes (bibliothèque standard uniquement)
Exécution
bash
python main.py
Structure
text
TP2_Ingestion_IoT/
├── models.py              # Dataclasses (SensorReading, IngestResponse...)
├── validators.py          # Validateurs polymorphiques
├── main.py                # Orchestration + tests
├── data/
│   └── sample_readings.json
└── outputs/               # Résultats générés
Résultats
Indicateur	Valeur
Readings reçus	5
Acceptés	1
Rejetés	4
Status	partial
Fichiers générés : Aucun (sortie console + logs)

Anomalies détectées
Reading	Problème	Code erreur
#2	humidité = 150	OUT_OF_RANGE
#3	sensor_id vide	EMPTY_FIELD
#3	pompe ON, débit 0	CONSISTENCY_ERROR
#4	température = -60	OUT_OF_RANGE
#5	timestamp vide	EMPTY_FIELD
Validation cumulative
Tous les validateurs sont exécutés sur chaque reading. Le producteur reçoit toutes les erreurs en une seule réponse.

Validateur	Vérification
RequiredFieldsValidator	Présence et non-vacuité
RangeValidator	Plage numérique [-50,60], [0,100], [0,1], [0,50]
ConsistencyValidator	Pompe ON → débit > 0
Sécurité
mask_api_key() : masquage des clés API dans les logs ("****5678")

sanitize_log() : suppression \n, \r, \t (anti-injection)

api_key exclue de to_dict() (jamais sérialisée)

Sortie console
text
============================================================
  SERVICE D'INGESTION IoT — TP2
============================================================

--- REPONSE JSON ---
{
  "status": "partial",
  "accepted_count": 1,
  "rejected_count": 4,
  "errors": [...]
}

--- VERIFICATIONS ---
[OK] Cycle serialisation SensorReading
[OK] humidite 150 detectee
[OK] 2 erreurs detectees (vide + coherence)
[OK] temperature -60 detectee
[OK] mask_api_key
[OK] sanitize_log
[OK] api_key exclue
[OK] Resultat: 1 accepte, 4 rejetes

 TOUTES LES VALIDATIONS SONT PASSEES
Difficultés rencontrées
Validation cumulative : penser à collecter toutes les erreurs sans s'arrêter à la première

Masquage API key : bien différencier log (masqué) et sérialisation JSON (exclu)

Sanitization : prévenir les injections de logs via \n
