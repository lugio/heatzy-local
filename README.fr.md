<p align="center"><img src="custom_components/heatzy_local/brand/icon@2x.png" width="160" alt="Logo Heatzy Local"></p>

# Heatzy (local) — intégration Home Assistant

Pilotez vos radiateurs **Heatzy** depuis Home Assistant **sans passer par le cloud Gizwits**.

L'intégration communique directement avec l'appareil sur le réseau local et vérifie
les écritures par relecture. Le cloud Gizwits n'est pas nécessaire à son fonctionnement.

**Version : [1.0.2](https://github.com/lugio/heatzy-local/releases/tag/v1.0.2)** ·
[Historique](CHANGELOG.md) · [Documentation](docs/README.md) ·
[Contribuer](CONTRIBUTING.md) · [Sécurité](SECURITY.md)

## Ce qu'elle apporte

| | |
|---|---|
| **Pilotage local** | confort, éco, hors-gel, arrêt — sans internet |
| **Diagnostic brut** | `power_data`, signification inconnue, désactivé par défaut ; aucune mesure de consommation validée |
| **Consignes réglables** | deux entités number, confort et éco, au dixième de degré |
| **Température interne** | la sonde de l'appareil — celle sur laquelle il régule |
| **Programme interne** | sept jours lus, 48 créneaux par jour ; action locale d’écriture |
| **Horloge** | champs jour/heure/minute rapportés et synchronisation manuelle ; fraîcheur non garantie |
| **Dérogation** | programme, vacances, automatique ; durée réelle réglable |
| **Aucune dépendance** | ni cloud, ni compte, ni jeton |

## Avant l'installation : Wi-Fi du radiateur

Le radiateur doit déjà être connecté au Wi-Fi. Cette intégration ne configure pas son SSID ni sa clé. Utilisez aujourd'hui le parcours d'ajout de l'application Heatzy, puis relevez son IP sur le routeur. Le [guide d'appairage](docs/pairing.md) distingue cette étape initiale de l'ajout local dans HA et détaille la piste ESPTouch expérimentale.

## Installation

### Compatibilité et préparation

Home Assistant **2026.10.1 minimum déclaré**, version sur laquelle la recette a été faite.
Les versions antérieures ne sont pas validées. Le radiateur doit déjà être connecté au Wi-Fi
et joignable sur le LAN ; la mise en réseau initiale sans l'application n'est pas validée.

### Par HACS

Ce dépôt peut être ajouté comme dépôt personnalisé HACS de catégorie Integration.
Il n'est pas déclaré comme intégré au catalogue HACS par défaut.
Pour la connexion Wi-Fi initiale, suivez d'abord le [guide d'appairage](docs/pairing.md).

1. HACS → Intégrations → menu ⋮ → **Dépôts personnalisés**
2. Ajoutez l'URL de ce dépôt, catégorie **Integration**
3. Installez « Heatzy (local) », puis redémarrez Home Assistant
4. **Paramètres → Appareils et services → Ajouter une intégration → Heatzy (local)**
5. Saisissez l'adresse IP du radiateur

### Manuellement

Copiez `custom_components/heatzy_local` dans le dossier `config/custom_components` de votre
installation, puis redémarrez.

## Matériel pris en charge

| Produit | `product_key` | État |
|---|---|---|
| Heatzy **Onyx** | `bb10d064f8de409db633b750faa22a52` | ✅ lecture et écriture vérifiées |

Les autres modèles ne sont pas validés. Un schéma est nécessaire pour les étudier, mais ne suffit pas à établir leur compatibilité :

```
curl -H "X-Gizwits-Application-Id: <app-id>" \
  "https://euapi.gizwits.com/app/datapoint?product_key=<clé>" \
  > custom_components/heatzy_local/schemas/<clé>.json
```

## Limites connues, mesurées

- **Quatre ordres seulement** sur l'Onyx. « Confort −1 » et « Confort −2 » figurent au schéma de la
  gamme, mais l'appareil masque la valeur sur deux bits : ils retombent sur confort et éco. Ils ne
  sont donc pas exposés.
- **Des indisponibilités temporaires ont été observées après écriture.** Elles ne prouvent
  pas un redémarrage systématique de la pile réseau. Le transport corrige aussi des défauts
  d'authentification TCP et de fermeture des sessions ; le délai prudent de relecture reste appliqué.
- **`power_data` reste non caractérisé.** Le schéma annonce une puissance sans unité ; les
  comparaisons avec un compteur indépendant ne permettent pas de l'utiliser comme des watts
  instantanés ni d'établir des Wh sur une fenêtre donnée. La donnée brute est un diagnostic
  désactivé par défaut, sans unité ni classe, exclu du tableau de bord Énergie.
- **Historique `power_cnt` non validé** : les essais ont observé un retour rapide à zéro,
  sans établir des valeurs historiques utilisables.
- **Le mode de détection de présence s'arme** (`derog_mode = 3`) mais **l'appareil ne dit pas ce
  qu'il voit** : aucun datapoint ne porte l'état de la détection.
- **La température interne n'est pas celle de la pièce.** C'est la sonde du radiateur, et le corps
  de l'appareil est chaud : un écart avec une sonde d’ambiance a été observé pendant les essais. L'intégration
  l'expose parce qu'elle explique le comportement du thermostat, mais ne l'utilisez pas comme
  température ambiante — aucune compensation automatique n’est appliquée.
  Elle se lit sur `cur_tempL` **seul** ; composer les deux octets donne 75 °C pour une pièce à 20.
- **Pilotage serveur et programme sont deux réglages distincts.** Le schéma décrit
  `timer_switch=1` comme pilotage serveur et `0` comme exécution appareil. L'APK
  Onyx arme aussi le programme par `derog_mode=1`. Le timer seul à0 n'a pas suffi
  à imposer l'éco sur les dernières mesures (dérogation0, confort maintenu).
  Le « Créneau prévu » est le planning calculé ; le « Mode effectif » est lu sur
  l'appareil. Ne pas confondre les deux.
- **Un signal Wi-Fi faible peut perturber les échanges.** Le correctif du transport TCP
  ne remplace pas une liaison réseau fiable.

## Dérogation Onyx

Le sélecteur expose les modes de l'Onyx confirmés dans son application :
désactivé (0), programme (1), vacances (2), automatique (3). Le mode automatique
arme la détection ; **aucun état de présence n'est remonté**. Les codes 4 et 5
permis par le schéma ne sont pas documentés et ne sont pas proposés en écriture.

Le nombre « Durée dérogation » lit et écrit le champ réel 0..255. En vacances,
l'application le traite en jours (son interface propose 1..30 jours). Dans les
autres modes, l'unité n'est pas établie et aucune unité n'est attribuée.
Le champ `com_temp` est un code de correction thermique, pas une mesure Wi-Fi.
Il reste brut car certaines valeurs reçues sont hors plage du dialogue officiel.

## Programme hebdomadaire local

Le capteur « Programme » expose `jours`, un dictionnaire JSON : clés `1` à `7`
(lundi à dimanche), chacune avec 48 valeurs `cft`, `eco`, `fro` ou `stop`,
de 00h00 à 23h30 par demi-heure. Un jour incomplet vaut `null`.

L'action `heatzy_local.ecrire_programme` reçoit `entity_id`, `jour` (0 pour tous)
et `ordres` (exactement 48 valeurs). Exemple copiant le lundi sur les sept jours :

```yaml
action: heatzy_local.ecrire_programme
data:
  entity_id: climate.mon_radiateur
  jour: 0
  ordres: "{{ state_attr('sensor.mon_radiateur_programme', 'jours')['1'] }}"
```

Vérifiez l'identifiant réel du capteur dans HA. Chaque action sauvegarde le
programme précédent et vérifie les 12 ou 84 octets après 12 secondes. Elle ne
change ni le timer serveur, ni la dérogation, ni les autres jours si un seul jour
est ciblé. Le programme tourne sur l'horloge **de l'appareil**.

## Horloge locale

Le capteur « Horloge interne » expose aussi les attributs `week`, `hour`,
`minute` et la date de lecture `_lu_a`. Des nombres permettent de régler ces
champs bruts selon le schéma ; `week=1` correspond au lundi et `7` au dimanche.
La valeur 0 permise par le schéma n'a pas de jour établi.

Le bouton « Mettre à l’heure » ou l'action `heatzy_local.mettre_a_l_heure`
synchronise les trois champs avec le fuseau configuré dans Home Assistant :

```yaml
action: heatzy_local.mettre_a_l_heure
data:
  entity_id: climate.mon_radiateur
```

La synchronisation est manuelle. La relecture accepte l'avancement naturel
d'une minute pendant les 12 secondes d'attente, y compris le passage au lundi.
Un décalage ponctuel ne prouve pas une dérive quotidienne. La valeur est celle
rapportée par le radiateur, pas une horloge reconstruite par HA. Après une remise
à l'heure confirmée, un retard de plusieurs minutes a réapparu dans les relevés ;
une dérive réelle et un rafraîchissement lent de ce champ ne sont pas encore
distingués. Aucune resynchronisation périodique automatique n'est activée.

## Consignes et écritures confirmées

Les deux entités `number` lisent les consignes réelles. Les bornes de représentation
proviennent des octets du schéma Onyx : 0..51,1 °C par 0,1 °C. Elles ne garantissent
pas l'acceptation de toute cette plage par le thermostat. L'application officielle
limite son interface à 7..30 °C par 0,5 °C ; aucun réglage extrême n'a été essayé.
Aucune compensation de sonde n'est appliquée automatiquement.

Chaque écriture est sérialisée avec les lectures, précédée d'une sauvegarde de
l'état complet dans `config/heatzy_local_backups/` (fichiers privés), puis suivie
d'une attente de 12 secondes et d'une relecture. Un accusé ne suffit pas : si la
valeur relue diffère, l'action signale une erreur. Ces sauvegardes peuvent être
archivées ou purgées par l'administrateur ; aucune purge automatique n'est faite.

## Automatisations

`climate.set_hvac_mode` avec `heat` conserve le preset d'un appareil déjà allumé,
sans écriture réseau. Pour choisir une allure, utilisez `climate.set_preset_mode`.
Depuis l'arrêt, `heat` rallume en confort si aucun preset actif n'est disponible.

Un déclencheur `state` sans filtre réagit aussi aux changements d'attributs.
Pour un capteur dont seul l'état doit déclencher le chauffage, ajoutez `to: null` :

```yaml
triggers:
  - trigger: state
    entity_id: sensor.mode_energie
    to: null
```

Cela évite de renvoyer des commandes à chaque variation d'un attribut de mesure.

## Le protocole

Documenté dans [le guide du protocole](docs/protocol.md). Il a été établi par rétro-conception :
décompilation de l'application Android officielle, sondage de l'appareil réel, et schéma des
datapoints publié par l'API Gizwits.

La partie **écriture** s'appuie sur la spécification de
[`markosharknz1/ha-jebao-pumps`](https://github.com/markosharknz1/ha-jebao-pumps), qui documente le
même protocole GAgent pour d'autres appareils — avec tous mes remerciements.

## Licence

MIT.


## Mise à jour et désinstallation

Pour mettre à jour manuellement, sauvegardez le dossier de l'intégration, remplacez-le
par celui de la release et redémarrez Home Assistant. Vérifiez ensuite les entités et
les réglages des appareils. Les identifiants existants restent conservés par cette version.

Pour désinstaller, retirez les entrées Heatzy (local) dans les appareils et services,
puis supprimez `custom_components/heatzy_local` et redémarrez HA. Les sauvegardes privées
`config/heatzy_local_backups/` ne sont pas supprimées automatiquement.
