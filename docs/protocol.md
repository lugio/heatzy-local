← [Documentation](README.md) · [Accueil](../README.md)

# Protocole LAN Gizwits GAgent — ce qui a été établi

Rétro-conception menée les 19 et 20 octobre 2026 sur un **Heatzy Onyx**
(`product_key` `bb10d064f8de409db633b750faa22a52`). Tout ce qui suit est **vérifié sur le
matériel**, sauf mention contraire.

## Transport

| | |
|---|---|
| **UDP 12414** | découverte — l'appareil répond depuis sa propre adresse |
| **TCP 12416** | session de lecture et de contrôle |

## Trame

```
00 00 00 03 | longueur (varint LEB128) | flag (1 o) | commande (2 o, gros-boutiste) | charge
```

La longueur couvre tout ce qui suit le champ de longueur. Le flag vaut `00` sur toutes les
requêtes observées.

## Commandes

| Commande | Sens | Rôle |
|---|---|---|
| `0x0003` / `0x0004` | UDP | découverte |
| `0x0006` / `0x0007` | TCP | demande et réponse du passcode |
| `0x0008` / `0x0009` | TCP | login — dernier octet `00` = succès |
| `0x0090` / `0x0091` | TCP | **lecture** de l'état |
| `0x0093` / `0x0094` | TCP | **écriture** |

**Le passcode s'obtient sans aucune authentification** : quiconque est sur le réseau local peut
le demander. C'est une caractéristique du protocole, pas un défaut de cette intégration — isolez
vos objets connectés sur un VLAN dédié.

## Séquence

1. TCP sur `12416`
2. `0x0006` → l'appareil renvoie `0x0007` avec `[longueur 2 o][passcode]`
3. `0x0008` avec `[longueur 2 o][passcode]` → `0x0009`, dernier octet `00`
4. Lecture : `0x0090` + un octet `0x02` → `0x0091` + `[action 1 o][103 o de données]`

Après le login, l'appareil envoie spontanément des trames `0x0093` à chaque changement d'état.

## Écriture

```
0x0093 | <numéro de séquence, 4 o> | 0x01 | <attrFlags> | <attrVals>
```

- **`attrFlags`** : un bit par attribut inscriptible, poids faible d'abord
  (`octet = id // 8`, `bit = id % 8`), **puis le tampon entier est inversé octet par octet**.
- **`attrVals`** : la zone complète des attributs inscriptibles. Seuls les octets marqués
  comptent ; les autres sont à zéro.
- Pour un attribut en bits :
  ```
  octet_destination = byte_offset - ((bit_offset + i) >> 3) + ((bits_inscriptibles - 1) >> 3)
  bit_destination   = (bit_offset + i) & 7
  ```

Cette partie provient de la spécification de
[`markosharknz1/ha-jebao-pumps`](https://github.com/markosharknz1/ha-jebao-pumps), tracée par
décompilation de `transDatasToP0Data` et confirmée contre des trames capturées.

⚠️ **L'accusé `0x0094` n'est pas un indicateur de succès.** Il est identique sur une écriture
appliquée et sur une écriture ignorée. **Toujours relire l'état après avoir écrit.**

## Schéma des datapoints

Publié par l'API Gizwits, en accès libre :

```
GET https://euapi.gizwits.com/app/datapoint?product_key=<clé>
    X-Gizwits-Application-Id: <identifiant d'application>
```

Pour l'Onyx : 104 datapoints, 103 octets, `protocolType` `standard`,
`packetVersion` `0x00000004`.

| datapoint | position |
|---|---|
| `on_off` | octet 0, bit 0 |
| `mode` | octet 0, bits 1-3 — `0=cft 1=eco 2=fro 3=stop 4=cft1 5=cft2` |
| `cft_tempL` / `cft_tempH` | octets 1 et 2 |
| `eco_tempL` / `eco_tempH` | octets 3 et 4 |
| `hour` / `minute` | octets 9 et 10 |
| `p1_data1` … `p7_data12` | octets 11 à 94 — 7 jours × 48 créneaux de 30 min, **2 bits par créneau** |
| `power_dataL` / `power_dataH` | octets 97 et 98 |
| `derog_mode` / `derog_time` | octets 96 et 102 |

## Pièges, tous rencontrés

- **`on_off` et `mode` partagent l'octet 0.** Écrire le mode sans armer aussi le drapeau d'`on_off`
  remet l'appareil à l'arrêt.
- **L'Onyx n'accepte que quatre ordres.** Il masque la valeur du mode sur deux bits : `cft1` (4)
  retombe sur `cft` (0) et `cft2` (5) sur `eco` (1).
- **Des refus temporaires de connexion ont suivi certaines écritures.** Leur cause exacte
  n'est pas établie ; le firmware de référence ne documente pas un reset à chaque écriture.
- **La température mesurée n'est pas décodée de façon fiable.** `cur_tempH * 256 + cur_tempL`
  donne un résultat cohérent sur un appareil et aberrant sur un autre. La valeur historique
  cur_tempL/10 et les octets bruts sont exposés avec cette limite explicite.
- **Écrire sur `0x0090` ne produit aucune erreur.** L'appareil accuse réception et ignore.
  Neuf formats ont été essayés sur ce canal avant de comprendre que l'écriture passe par `0x0093`.

## `power_data` : grandeur non caractérisée

Le schéma le nomme puissance (功率) sans unité ; l'APK Onyx compose les deux octets
sans conversion, mais sa vue ne présente pas cette donnée. Les essais avec un compteur
indépendant ne justifient pas une lecture en watts instantanés : la donnée peut valoir
plusieurs centaines alors que la puissance mesurée reste proche de la veille.
Une baisse puis une hausse observées excluent aussi un simple cumul monotone sur cet
intervalle. La phase de chauffe n'a pas pu être corrélée complètement, à cause d'une
indisponibilité de communication : aucune unité, moyenne ou fenêtre ne peut être conclue.

L'ancienne hypothèse Wh sur24h n'est donc pas une spécification. Le champ reste un
**diagnostic désactivé par défaut, sans unité ni device_class**. Un compteur électrique
indépendant doit fournir la consommation réelle ; ce champ ne doit pas alimenter Énergie.

## `power_cnt` ne donne pas d'historique

La description du schéma annonce « 0 temps réel · 1 vingt-quatre heures · 2 sept jours ·
3 un mois · 4 six mois ». **Mesuré : c'est faux, ou du moins inopérant en local.** Écrire 1, 2, 3
puis 4 laisse `power_data` inchangé. Les notifications portent brièvement la valeur écrite —
`power_cnt=3` puis `=4`, revenus à 0 en une cinquantaine de millisecondes — donc le champ est une
**commande fugitive** remise à zéro par le micrologiciel, pas un sélecteur persistant.

## `derog_mode` et la détection de présence

`derog_mode` vaut, selon le schéma : « 0 désactivé · 1 minuterie · 2 voyage · 3 AUTO (感应模式,
mode détection) ». **Écrire 3 est accepté et persiste.** En revanche **aucun datapoint ne remonte
l'état de la détection** : on peut armer le mode présence, on ne peut pas savoir ce qu'il voit.

## Les notifications ont leur propre format

Une notification `0x0093` ne se décode pas comme une réponse `0x0091`. Sa charge fait 132 octets :

```
4 octets | longueur du DID (2 o, = 22) | DID (22 o) | action 0x04 | 103 octets d'état
```

Décoder une notification à la position d'une réponse de lecture donne des valeurs fantaisistes :
c'est ainsi qu'une « puissance » de 21845 W (0x5555) a été publiée dans Home Assistant.

## Le programme hebdomadaire : lu ET écrit

Les 84 datapoints `p1_data1` … `p7_data12` portent un programme de 7 jours. Chaque octet code
**quatre créneaux de 30 minutes, 2 bits par créneau, poids faible en premier** — donc seulement
quatre ordres possibles : `0=cft 1=eco 2=fro 3=stop`.

```
creneau = heure * 2 + (1 si minute >= 30)        # 0 a 47
octet   = p<jour>_data<creneau // 4 + 1>          # jour de 1 a 7, selon le datapoint `week`
ordre   = (octet >> ((creneau % 4) * 2)) & 3
```

Vérifié par écriture le 2026-10-20 : les 84 valeurs écrites en une trame `0x0093`, relues et
conformes sur les sept jours. Un programme entièrement en `eco` donne `0x55` sur les douze octets,
ce qui a servi de contrôle au décodage.

**L'appareil utilise SA propre horloge** (`week`, `hour`, `minute`), pas celle du serveur. Si elle
dérive, le programme se décale.

## `timer_switch` et activation du programme

Le schéma décrit1 comme contrôle serveur et0 comme exécution appareil. Cela ne suffit
pas à prouver le comportement du programme : un appareil est resté en confort avec0
alors que son créneau prévu demandait éco. L'APK Onyx n'utilise pas ce champ dans son
modèle ; il active PROG par `derog_mode=1`.

On ne peut donc pas attribuer tout retour de preset à `timer_switch=0`. Les changements
observés peuvent aussi venir du programme, du mode automatique ou d'un autre contrôleur ;
une corrélation est nécessaire avant de choisir une cause.

## Méthode

1. Décompilation de l'APK `com.gizwits.heatzy` 8.2.6 — classe `Onyx`, 19 champs, et la méthode
   `covertModeToData` qui révèle l'encodage du planning sur 2 bits.
2. Sondage de l'appareil réel : découverte, passcode, session, lecture.
3. Validation croisée : l'horloge interne du radiateur avançait de dix minutes entre deux
   captures, à la minute près.
4. Récupération du schéma officiel des datapoints.
5. Écriture, après trois corrections : la bonne commande, le numéro de séquence, et la zone
   complète de valeurs.


## Consignes réglables et transactions — mission 3

**Documenté par le schéma produit livré** : cft/eco sont deux paires L0..255 et
H0..1, ratio1/addition0 ; représentation `(256H+L)/10`, soit0..51,1 par0,1°C.
**Documenté par APK8.2.6** (SHA256
`436993c7664328ad9a3a7ff80454b6567e7e61551f78f1d84146df5019a7138a`),
`TmpModifyDialog` borne son interface à7..30 par0,5, avec contrainte confort/eco.
Les limites d'interface ne constituent pas une mesure des limites du micrologiciel.

Les commandes HA utilisent désormais une transaction : lecture préalable,
sauvegarde persistante, écriture, attente12s, lecture et comparaison de chaque
champ. Le verrou par appareil protège aussi les sondages. Aucune relecture
immédiate ni publication optimiste de la valeur demandée.


## Horloge — source APK et méthode de vérification

**Documenté statiquement** : dans l'APK8.2.6 (SHA256 ci-dessus), `Onyx.setTimingData`
écrit week/hour/minute, avec `((Calendar.DAY_OF_WEEK+5)%7)+1` : lundi1..dimanche7.
Preuve REA `ev_bae7987ecec5fcb69039f38a0df4178e961d00955f8f0b0a5d264a9b058e1687`.
Le schéma autorise0..7,0..23,0..59 ; la signification de week0 n'est pas établie.
L'heure source est le fuseau local HA, calculée dans le verrou juste avant
sauvegarde et émission, pas à la mise en file de la commande.
Le contrôle compare les minutes dans la semaine, avec tolérance d'avancement
0..1minute pendant l'attente ; aucun recul n'est pris pour une confirmation.
Les relevés antérieurs sous martèlement ne permettent pas de déduire une
« dérive par jour ». Une observation prolongée est nécessaire pour cela.


## Corrections de sémantique — sources mission 3

Source APK Onyx8.2.6, SHA256
`436993c7664328ad9a3a7ff80454b6567e7e61551f78f1d84146df5019a7138a`,
classes `Onyx`, `OnyxViewHolder`, `VACDaysDialog`, `TmpModifyDialog` analysées
statiquement par REA6.5.0, sans installation ni exécution de l'application :

- `derog_mode=1` est **PROG**,2 **VAC**,3 **AU** ; le programme est armé via1.
  La description générique « minuterie » ne doit pas devenir un boost Onyx.
  Preuve `ev_bdd049d36bfa08abdf14fb036229540c1c80c4c83ce01cd5f973822eb1bd795a`.
- La durée de vacances est transmise en **jours**, dialogue1..30 ; le schéma
  permet0..255 et ne précise pas d'unité dans les autres modes.
  Preuve `ev_e79b205460a544cbc3291baa005f64aa377ffa8dfb2594875a33218c296655fb`.
- `com_temp` n'est **pas une qualité Wi-Fi** : `getRectifyTmp` rend brut-5,
  `setPlugTmp` écrit correction+5, UI-5..+5. Le brut63 reçu sur un appareil ne
  cadre pas avec cette UI ; il reste brut et n'est pas rendu réglable tant
  que cette anomalie d'encodage manque. Le schéma le marque bien inscriptible.
- `powReset` écrit power_cnt5, mais son effet réel n'a pas été testé. Aucun
  historique ni reset n'est ajouté sur cette seule preuve statique.
- `getPow` compose H/L ; ni unité ni fenêtre Onyx établies dans les vues
  examinées. Ne pas convertir en Wh, kWh ou W sans preuve supplémentaire.
- `getCurTemp` dans l'APK compose H/L, contrairement au décodage matériel retenu
  pour ces captures (H aberrant sur un appareil). Les octets bruts sont exposés
  en attribut ; ce désaccord n'est pas une nouvelle preuve de température.

Le [schéma officiel public](https://gizwits-docs.github.io/zh-cn/Cloud/openapi_apps.html)
a été revérifié le20/10/2026 via `euapi.gizwits.com/app/datapoint` : JSON identique
au fichier livré, version4 ; pas d'autre version publique documentée trouvée.
Le [firmware de référence](https://github.com/gizwits/Gizwits-GAgent/tree/72d2db0)
et la [documentation officielle miroir](https://gizwits-docs.github.io/en-us/DeviceDev/GAgent.html)
ne prouvent pas un redémarrage systématique après écriture. Le délai12s reste
une précaution issue des mesures sur nos Onyx, pas une promesse du protocole.

Le [code cyr-ius](https://github.com/cyr-ius/hass-heatzy/tree/1118010), étudié en
entier, réserve son capteur de présence inféré au Pilote Pro. Ses préférences de
durée restaurées ne remplacent pas une lecture de `derog_time` sur Onyx.


Les relectures après synchronisation ont montré que les champs d'horloge peuvent rester en retard. Leur rafraîchissement n'est pas établi : cela ne prouve pas une dérive RTC. L'activation du programme Onyx utilise derog_mode=1 dans l'APK ; timer_switch seul n'établit pas son état actif. Les retours spontanés de preset restent à corréler avec une source de commande avant d'en choisir la cause.

## Robustesse du transport TCP

Le challenge0007 et le résultat0009 sont lus avec le même décodeur de trames complètes
que les relevés. TCP peut fragmenter une réponse ou concaténer une notification : ni un
unique read(), ni le dernier octet du tampon ne constituent une validation de login.
La longueur du challenge doit correspondre à ses octets et le résultat de login doit
être un unique octet nul. Une erreur ou annulation ferme la session déjà ouverte ; les
erreurs réseau remontent au coordinateur comme ErreurHeatzy.

Référence : [GAgent lantcp.c](https://github.com/gizwits/Gizwits-GAgent/blob/72d2db0/gagent/lan/src/lantcp.c),
Lan_handlePasscode et Lan_handleLogin. Le code de référence prévoit8clients et un délai
d'inactivité14secondes en station ; cela ne prouve pas les mêmes limites sur Onyx.
Régressions simulées sans appareil dans tests/test_gizwits_transport.py.
