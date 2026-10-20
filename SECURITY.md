# Sécurité

La branche principale et la dernière release reçoivent les correctifs ; aucune branche ancienne n'est maintenue séparément.

## Signaler une vulnérabilité

Utilisez le [signalement privé GitHub](https://github.com/lugio/heatzy-local/security/advisories/new). Si ce formulaire n'est pas accessible, contactez le mainteneur par un canal privé convenu. Ne publiez pas de vulnérabilité exploitable, de passcode Gizwits, de jeton ou de capture contenant des données personnelles dans une issue ordinaire.

## Périmètre

L'intégration communique directement avec les radiateurs sur le LAN. Elle ne garantit pas la sécurité du micrologiciel Gizwits ni le chiffrement du protocole local. Réservez cet accès à un réseau de confiance.

Les sauvegardes d'état créées dans `config/heatzy_local_backups/` sont privées et ne doivent pas être jointes sans examen. N'ouvrez pas les ports du radiateur sur Internet pour utiliser cette intégration.
