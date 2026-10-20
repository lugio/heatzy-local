# Validation LAN — résumé public

← [Documentation](../README.md)

Ce résumé ne contient ni nom d'appareil personnel, ni adresse réseau, ni identifiant matériel, ni capture privée.

## Vérifié

- Les réponses de lecture et les notifications utilisent des enveloppes différentes ; le décodeur doit reconnaître leur commande et leur longueur.
- Une réponse TCP peut être fragmentée ou concaténée avec une notification : les tests hors ligne couvrent ces cas.
- Les écritures de mode, consignes, horloge, dérogation et programme ont fait l'objet de relectures sur Onyx ; un accusé seul n'est pas une confirmation d'état.
- Une recette courte de modes a confirmé confort maintenu puis restauration d'éco, sans changer les consignes.

## Non établi

L'unité de power_data, la fenêtre ou le calcul d'un éventuel historique, la précision de l'horloge rapportée et l'état de présence réel ne sont pas établis. Les relevés ne justifient donc aucun compteur d'énergie calculé à partir de power_data.

Les rapports de travail et captures brutes ne sont pas distribués. Les descriptions actuelles et leurs limites figurent dans le [protocole](../protocol.md), le [guide utilisateur](../../README.fr.md) et les tests du dépôt.
