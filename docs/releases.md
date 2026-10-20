# Préparer une release

← [Documentation](README.md)

1. Vérifier un arbre de travail propre, relire le diff et exécuter `python3 -m unittest discover -s tests -v`.
2. Mettre à jour `custom_components/heatzy_local/manifest.json` et `CHANGELOG.md` avec le même numéro. Documenter toute nouvelle exigence de compatibilité.
3. Pousser le commit avec l'auteur du projet et attendre la validation GitHub Actions. Les contrôles HACS et Hassfest doivent réussir sans exclusion.
4. Créer un tag annoté `vX.Y.Z` sur ce commit, puis le pousser. Ne jamais déplacer un tag publié pour remplacer discrètement son contenu.
5. Créer la release GitHub sur ce tag avec les changements, limites et résultats de tests. Fournir une archive ne contenant que le dossier `heatzy_local/` et son contenu installable, sans cache, jeton, sauvegarde ni rapport privé, et son SHA256.
6. Vérifier la version à l'intérieur de l'archive et le lien tag/commit/release. Le numéro d'une release n'est pas la version du firmware du radiateur.
7. Installer cette même version dans HA après sauvegarde et charger le manifeste au redémarrage. Vérifier disponibilité et conservation des réglages, sans imposer un état de chauffe.

Le dépôt public ne reçoit que du contenu examiné et nettoyé. Ne jamais y pousser un historique privé ou une capture brute.
