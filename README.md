# TP2 – Service d'Ingestion IoT

## Description

Service d'ingestion de données IoT pour capteurs météo et irrigation. Il reçoit des mesures, les valide, les structure et produit des réponses JSON avec un reporting complet des erreurs.

---

## Fonctionnalités

-  Validation cumulative des données entrantes
-  Masquage sécurisé des clés API dans les logs
-  Protection contre les injections de logs
-  Sérialisation JSON avec exclusion automatique des secrets
-  Architecture polymorphique pour les validateurs
-  10 assertions de vérification automatiques

---

## Structure du projet
