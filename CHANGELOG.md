# Historique des versions

## [1.0.2] — 2026-10-20

### Ajouté
- Première édition publique nettoyée et guide de connexion Wi-Fi initiale ; le provisioning sans application reste non validé.
- Logo original du projet et icônes PNG transparentes locales 256/512 px dans `brand/`, visibles sans CDN dans Home Assistant compatible.
- Présentation du projet dans le README et clarification du blocage HACS pour un dépôt privé.

### Compatibilité
- Aucune modification du protocole, des identifiants d'entités ni des consignes par rapport à 1.0.1.

## 1.0.1 — 2026-10-20 (version antérieure à la publication publique)

### Corrigé
- Authentification LAN sur trames complètes, même si TCP fragmente les réponses ou concatène des notifications.
- Fermeture des connexions après erreur ou annulation et remontée cohérente des erreurs réseau au coordinateur.
- HEAT conserve le preset d'un appareil déjà allumé ; les écritures sont sauvegardées puis vérifiées par relecture.

### Modifié
- `power_data` devient un diagnostic brut désactivé par défaut, sans unité ni classe de consommation. Les identifiants existants sont conservés.
- Version minimale déclarée alignée sur Home Assistant 2026.10.1, seule version recettée pour cette livraison ; les versions antérieures ne sont pas validées.

### Documentation et validation
- Consignes, programme, horloge et dérogation documentés avec leurs limites.
- Retrait des interprétations non prouvées sur la consommation, le programme et les redémarrages réseau.
- 24 tests hors ligne ; validation Hassfest ; recette courte de lecture et modes sur Onyx. La stabilité durable et l'ensemble des états vacances/présence ne sont pas certifiés par cette recette.
- Dépôt organisé, guides de contribution/sécurité, modèles GitHub et première release numérotée.

## 1.0.0 — développement initial

Première implémentation locale Onyx : climate, lectures des états, réglages, programme et actions locales. Le manifeste portait 1.0.0 mais aucun tag ni release GitHub n'avait été créé.

[1.0.2]: https://github.com/lugio/heatzy-local/releases/tag/v1.0.2
