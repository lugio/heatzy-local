# Documentation

← [Accueil](../README.md)

- [Guide utilisateur français](../README.fr.md)
- [Wi-Fi initial et ajout dans HA](pairing.md)
- [Protocole LAN et sémantique des datapoints](protocol.md)
- [Mesures LAN historiques du 20 octobre 2026](research/2026-10-20-lan-measurements.md) — archive, pas spécification actuelle
- [Logo et icônes locales](branding.md)
- [Préparer une release](releases.md)
- [Historique des versions](../CHANGELOG.md)
- [Contribuer](../CONTRIBUTING.md)
- [Sécurité](../SECURITY.md)

## Organisation

```text
custom_components/heatzy_local/  Intégration installable et traductions
  schemas/                       Schémas de datapoints par produit
tests/                           Régressions hors ligne
.github/                         Validation et modèles GitHub
docs/                            Guides et preuves historiques
CHANGELOG.md                     Versions et changements
```

Les rapports de travail privés, APK, captures complètes et sauvegardes HA restent hors du code installable. La publication ne contient pas les relevés privés ni l'historique de développement original.
