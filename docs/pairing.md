# Wi-Fi initial et ajout dans Home Assistant

← [Accueil](../README.md) · [Guide français](../README.fr.md)

## Deux étapes différentes

1. **Provisionner le Wi-Fi** : apprendre au radiateur le SSID et le mot de passe du réseau domestique. Cette fonction n'est pas implémentée par Heatzy Local.
2. **Ajouter le radiateur dans HA** : une fois connecté au réseau, saisir son adresse IP dans Heatzy Local. Cette communication et les commandes suivantes se font sur le LAN, sans identifiant de compte Gizwits.

**Oui : actuellement il faut d'abord connecter le radiateur au Wi-Fi.** La méthode utilisateur documentée ici passe par l'application officielle Heatzy. Le fonctionnement quotidien de cette intégration n'utilise ensuite pas le cloud. Cela ne signifie pas que tout le parcours initial est déjà réalisable hors cloud.

## Méthode actuelle

### 1. Préparer le réseau et le téléphone

- Utiliser un réseau Wi-Fi 2,4 GHz compatible avec le radiateur.
- Connecter le téléphone à ce réseau et ouvrir l'application Heatzy ; utiliser son parcours d'ajout normal et son compte si demandé.
- Saisir les identifiants Wi-Fi uniquement dans l'application. Ne pas les publier dans une issue ou une capture.

### 2. Mettre l'Onyx en recherche de connexion

Les instructions intégrées à l'application Android officielle 8.2.6 indiquent, pour l'Onyx : partir de l'appareil/écran éteint, maintenir l'icône ON/OFF pendant 3 secondes, puis constater l'allumage de l'écran et le mode de recherche de connexion. Suivre ensuite le bouton d'ajout `+` et les instructions affichées par l'application.

Cette séquence est **documentée par les ressources de l'application, pas recettée matériellement dans ce projet**. L'instruction française parle d'appareil éteint et l'anglaise d'écran éteint ; ne pas inventer une procédure de réinitialisation usine. Si l'affichage ou les instructions de votre révision diffèrent, utiliser sa notice et les instructions de l'application. Le projet n'a pas établi de geste distinct activant SoftAP sur Onyx.

Un radiateur déjà connecté et joignable n'a pas besoin d'être réappairé pour utiliser l'intégration locale.

### 3. Confirmer la connexion Wi-Fi

- Attendre la fin du parcours de configuration de l'application.
- Retrouver le radiateur dans la liste des clients DHCP du routeur et relever son adresse IP actuelle.
- Une réservation DHCP est recommandée pour que cette adresse reste stable.
- Vérifier que Home Assistant peut joindre le radiateur : découverte UDP 12414 et contrôle TCP 12416 sont utilisés. Un réseau invité isolé ou un filtrage entre VLAN peut bloquer ces échanges même si l'application cloud fonctionne.

### 4. Ajouter Heatzy Local

1. Installer l'intégration par HACS ou manuellement, puis redémarrer HA.
2. Paramètres → Appareils et services → Ajouter une intégration → **Heatzy (local)**.
3. Entrer l'adresse IP obtenue sur le routeur.
4. Vérifier les états réels et les consignes. Aucun compte ou jeton Gizwits n'est demandé par ce flux HA.

## En cas de problème

| Symptôme | Contrôle utile |
|---|---|
| L'application n'arrive pas à connecter le radiateur | Vérifier le Wi-Fi 2,4 GHz et le mode de recherche propre au modèle ; ce n'est pas encore un problème de l'intégration HA |
| L'application fonctionne mais HA ne découvre rien | Vérifier l'IP, les ports locaux et l'isolation du réseau |
| HA fonctionnait puis perd la connexion | Vérifier DHCP, qualité radio et disponibilité locale ; ne pas réinitialiser systématiquement le radiateur |
| Un autre modèle ne fonctionne pas | Onyx est le seul modèle validé ; un schéma similaire ne garantit pas sa compatibilité |

## Recherche : vers un appairage sans application

### Ce que l'analyse statique établit

L'APK officiel 8.2.6 utilise le parcours générique suivant lorsqu'aucun nom Bluetooth n'est sélectionné : ajout d'appareil → déploiement Gizwits AirLink avec type GizGAgentESP → ESPTouch. La présence d'une bibliothèque ESPTouch n'est donc pas la seule preuve : les appels entre ces couches ont été suivis. Un parcours BLE distinct existe lorsqu'un nom Bluetooth est fourni.

La même application embarque aussi SoftApConfig, qui émet des trames UDP broadcast vers le port 12414. **Ce n'est pas le parcours AirLink précédent** et sa présence dans le SDK ne prouve pas que l'Onyx expose un point d'accès utilisable.

### Ce que la référence GAgent documente

En SoftAP, la commande UDP 0001 peut transporter deux longueurs uint16 big-endian suivies du SSID et de la clé, exprimées en octets. Dans la version de référence examinée, l'ACK 0002 peut être envoyé même si la configuration est refusée : il faut vérifier l'association réelle au réseau et une lecture LAN, pas seulement l'accusé.

Ces échanges sont une piste de développement, **pas une procédure Onyx sans cloud validée**. Les adresses/AP par défaut du SDK ne doivent pas être présentés comme ceux de tous les Onyx. La première activation d'un appareil vierge et l'obtention de son identifiant peuvent également dépendre du parcours cloud ; ce point reste à tester.

### Ce qu'il reste à démontrer

- La variante ESPTouch et la procédure exacte acceptées par le firmware Onyx visé.
- L'existence et l'activation d'un éventuel mode SoftAP sur cet appareil.
- Le retour sur le réseau cible, l'identité locale et la lecture des états après configuration.
- Le cas d'un appareil vierge, pour distinguer configuration Wi-Fi et enregistrement cloud initial.

Aucune commande de provisioning n'est distribuée comme fonctionnalité prise en charge pour l'instant. Aucun appareil en usage n'a été réinitialisé pour cette recherche.

## Sources et limites

- Application Android officielle `com.gizwits.heatzy`, version 8.2.6 / code 137, SHA256 `436993c7664328ad9a3a7ff80454b6567e7e61551f78f1d84146df5019a7138a` : analyse statique des ressources Onyx et des chemins d'ajout, sans exécution ni capture de compte. L'APK et les décompilations ne sont pas redistribués.
- [Documentation Gizwits Android](https://gizwits-docs.github.io/en-us/AppDev/AndroidSDKA2.html) : modes d'onboarding et différence entre configuration et enregistrement.
- [GAgent UDP de référence](https://github.com/gizwits/Gizwits-GAgent/blob/72d2db0/gagent/lan/src/lanudp.c) : Lan_udpOnBoarding et dispatch UDP.
- [GAgent HTTP de référence](https://github.com/gizwits/Gizwits-GAgent/blob/72d2db0/gagent/lan/src/webconfig.c) : autre voie du SDK, pas preuve de disponibilité Onyx.
- [Documentation Espressif SmartConfig](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_smartconfig.html) : variantes ESPTouch/ESPTouchv2, à ne pas confondre.

Les sources génériques décrivent leurs propres versions ; elles ne remplacent pas une recette sur le matériel Onyx.
