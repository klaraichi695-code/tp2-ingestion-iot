"""validators.py — Système de validation polymorphique."""

from typing import List
from models import ValidationError


class Validator:
    """Classe de base abstraite pour les validateurs."""
    
    def validate(self, data: dict) -> List[ValidationError]:
        raise NotImplementedError


class RequiredFieldsValidator(Validator):
    """Vérifie la présence et non-vacuité des champs obligatoires."""
    
    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields
    
    def validate(self, data: dict) -> List[ValidationError]:
        errors = []
        for field in self.required_fields:
            value = data.get(field)
            if value is None:
                errors.append(ValidationError(
                    field=field,
                    code="MISSING_FIELD",
                    message=f"Le champ '{field}' est obligatoire mais absent."
                ))
            elif isinstance(value, str) and not value.strip():
                errors.append(ValidationError(
                    field=field,
                    code="EMPTY_FIELD",
                    message=f"Le champ '{field}' est obligatoire mais vide."
                ))
        return errors


class RangeValidator(Validator):
    """Vérifie qu'une valeur numérique est dans une plage."""
    
    def __init__(self, field_name: str, min_val: float, max_val: float):
        self.field_name = field_name
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, data: dict) -> List[ValidationError]:
        errors = []
        value = data.get(self.field_name)
        
        if value is None:
            return errors
        
        try:
            num_val = float(value)
        except (TypeError, ValueError):
            errors.append(ValidationError(
                field=self.field_name,
                code="INVALID_TYPE",
                message=f"'{self.field_name}' doit être numérique, reçu: {repr(value)}"
            ))
            return errors
        
        if not (self.min_val <= num_val <= self.max_val):
            errors.append(ValidationError(
                field=self.field_name,
                code="OUT_OF_RANGE",
                message=f"'{self.field_name}' = {num_val} hors plage [{self.min_val}, {self.max_val}]"
            ))
        return errors


class ConsistencyValidator(Validator):
    """Vérifie la cohérence pomme/débit."""
    
    def validate(self, data: dict) -> List[ValidationError]:
        errors = []
        pump = str(data.get("pump_status", "")).lower()
        
        try:
            flow = float(data.get("irrigation_l_min", 0.0))
        except (TypeError, ValueError):
            return errors
        
        if pump == "on" and flow <= 0.0:
            errors.append(ValidationError(
                field="irrigation_l_min",
                code="CONSISTENCY_ERROR",
                message="pump_status='on' mais irrigation_l_min <= 0 : pompe allumée sans débit mesuré"
            ))
        return errors


def run_validators(data: dict, validators: List[Validator]) -> List[ValidationError]:
    """Exécute tous les validateurs et agrège les erreurs."""
    all_errors = []
    for validator in validators:
        all_errors.extend(validator.validate(data))
    return all_errors