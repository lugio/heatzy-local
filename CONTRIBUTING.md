# Contribuer

Commencez par les [limites connues](README.md#limites-connues-mesurées) et le [protocole](docs/protocol.md). Onyx est le seul modèle validé ; un champ de schéma ou un comportement sur une autre gamme ne prouve pas sa sémantique sur Onyx.

## Développement et tests

Les tests utilisent uniquement la bibliothèque standard Python :

```bash
python3 -m unittest discover -s tests -v
```

La recette actuelle utilise Python 3.14 et Home Assistant 2026.10.1. Hassfest s'exécute dans GitHub Actions. La validation HACS est exécutée sur ce dépôt public, sans exclusion de contrôle.

Pour un défaut de protocole, ajoutez d'abord une reproduction hors ligne. Conservez les identifiants d'entités et n'ajoutez aucune unité ou classe physique sans preuve. Séparez dans les comptes rendus mesures, documentation, déductions et inconnues.

## Essais sur matériel

Les tests hors ligne n'agissent sur aucun appareil. Une validation réelle doit préciser le modèle, les versions, l'état initial et le résultat relu. Sauvegardez avant toute écriture ; une réponse réseau ne remplace pas la relecture. N'incluez ni passcode, jeton, adresse personnelle ni capture non expurgée dans une issue ou un commit. Un essai ne doit pas couper un chauffage occupé sans autorisation explicite.

## Pull request

Décrivez le problème, le comportement obtenu et les vérifications réellement exécutées. Mettez à jour la documentation si la sémantique d'une entité change. Pour une livraison, suivez le [guide de release](docs/releases.md).
