# 📑 Rapport d'état : Modernisation de EmailHarvester (TI-11)

Ce document résume les travaux effectués, la configuration actuelle et les points restants pour finaliser la modernisation de l'outil.

## 🎯 Objectif Global
Transformer le moteur de résilience d'origine pour éliminer les blocages applicatifs (hangs), renforcer la furtivité via le réseau TOR, et aligner le code sur les standards modernes (Pydantic, .env, isolation des threads).

## ✅ Réalisations effectuées (Terminées)

### 1. Refonte du ResilienceManager ([src/resilience.py](file:///opt/yaovi/src/email-harvester/src/resilience.py))
*   **Centralisation de l'état** : L'état des IP (USING, BLACKLISTED, QUARANTINE) est partagé entre tous les moteurs de recherche.
*   **Élimination des goulots d'étranglement** : Les opérations lentes (`time.sleep`) ont été sorties des verrouillages ([lock](file:///opt/yaovi/src/email-harvester/src/resilience.py#240-273)) pour permettre un parallélisme réel.
*   **Rotation intelligente TOR** : Déclenchement automatique d'un changement d'identité en cas de code `403`, `429` ou détection de bot.

### 2. Sonde de Connectivité ("Canary") ([src/core.py](file:///opt/yaovi/src/email-harvester/src/core.py))
*   **Fiabilisation de la sonde** : Remplacement de l'URL de test (auparavant Google) par `https://check.torproject.org/api/ip`. Cela élimine les faux positifs de "Structural Block" causés par les captchas Google sur le réseau TOR.

### 3. Architecture & Configuration
*   **Schéma Pydantic** : Utilisation d'une classe [Settings](file:///opt/yaovi/src/email-harvester/src/core.py#258-281) rigoureuse pour valider les paramètres.
*   **Configuration Stricte via [.env](file:///opt/yaovi/src/email-harvester/.env)** : L'application dépend désormais d'un fichier [.env](file:///opt/yaovi/src/email-harvester/.env) à la racine (préfixe `EH_`). Si le fichier ou une variable obligatoire (`EH_TIMEOUT`, `EH_TOR_PORT`, etc.) est absent, l'application refuse de démarrer.
*   **Gestion UX** : Capture propre du `Ctrl+C` et affichage de l'index de batch (ex: `@ Batch 150`) dans le tableau de bord CLI.

## 🚧 État Actuel & Points Critiques à traiter

### 1. Automatisation du Nom de Fichier
*   **Comportement attendu** : Le script doit utiliser automatiquement le domaine cible pour nommer le fichier de sortie (ex: `payoneer.com.txt`) s'il n'est pas spécifié manuellement via `-s`.
*   **Prochaines étapes** : Modifier [src/cli.py](file:///opt/yaovi/src/email-harvester/src/cli.py) pour implémenter cette règle de nommage.

### 2. Pauses "Human-like" Aléatoire (Dynamisme)
*   **Problème** : Certaines pauses sont encore fixées en dur dans le code (ex: `time.sleep(5.0)` dans [resilience.py](file:///opt/yaovi/src/email-harvester/src/resilience.py) ou des valeurs fixes de jitter dans [cli.py](file:///opt/yaovi/src/email-harvester/src/cli.py)).
*   **Attente** : Ces valeurs doivent être des plages aléatoires (min/max) définies dans un fichier de configuration (ex: `stealth.yaml`) et lues dynamiquement.

### 3. Validation de Récolte Massive
*   **Prochain Test** : Valider la robustesse sur une limite élevée (ex: 2000 résultats) pour confirmer que la rotation d'IP permet de traverser les filtres de DuckDuckGo sur la durée.

## 🛠️ Configuration Environnementale ([.env](file:///opt/yaovi/src/email-harvester/.env))
Le fichier [.env](file:///opt/yaovi/src/email-harvester/.env) contient actuellement les clés suivantes :
*   `EH_USER_AGENT_PLATFORM`, `EH_TOR_HOST`, `EH_TOR_PORT`, `EH_TOR_CONTROL_PORT`, `EH_TOR_CONTROL_PASSWORD`, `EH_TIMEOUT`.

---
*Ce rapport peut être utilisé comme contexte direct pour l'agent suivant afin de reprendre les corrections sur le nom de fichier et les pauses dynamiques.*
