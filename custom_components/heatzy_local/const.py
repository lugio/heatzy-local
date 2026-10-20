"""Constantes de l'integration Heatzy local."""
from __future__ import annotations

DOMAIN = "heatzy_local"

CONF_HOST = "host"
CONF_NOM = "nom"

PORT_DECOUVERTE = 12414
PORT_CONTROLE = 12416
ENTETE = b"\x00\x00\x00\x03"

# commandes du protocole Gizwits GAgent, etablies par retro-conception
CMD_DECOUVERTE = 0x0003
CMD_PASSCODE = 0x0006
CMD_LOGIN = 0x0008
CMD_LECTURE = 0x0090
CMD_CONTROLE = 0x0093
ACTION_LECTURE = 0x02
ACTION_ECRITURE = 0x01

DELAI_RESEAU = 8.0
PERIODE_RELEVE = 30

# Ce modele n'accepte que quatre ordres fil pilote : l'appareil masque la
# valeur sur 2 bits, donc cft1 (4) et cft2 (5) retombent sur cft et eco.
# Verifie par ecriture et relecture le 2026-10-20.
MODE_VERS_PRESET = {"cft": "comfort", "eco": "eco", "fro": "away"}
PRESET_VERS_MODE = {v: k for k, v in MODE_VERS_PRESET.items()}
MODE_ARRET = "stop"

# cur_mode est le mode REELLEMENT applique par l'appareil, indexe sur le meme
# enumere que mode. Il peut differer de la consigne quand un programme horaire
# ou une derogation agit. La valeur est conservée telle que rapportée.
MODES_ORDRE = ["cft", "eco", "fro", "stop", "cft1", "cft2"]

# Onyx, APK officiel : 0 = désactivé, 1 = programme, 2 = vacances, 3 = auto.
# Ces codes n'établissent pas un état de présence réellement détectée.
DEROGATION_AUCUNE = 0

# Programme hebdomadaire interne : p1_data1 .. p7_data12, soit 7 jours de
# 12 octets, 4 creneaux de 30 min par octet, 2 bits par creneau, poids faible
# en premier. Les 2 bits ne codent donc que quatre ordres.
MODES_PROGRAMME = ["cft", "eco", "fro", "stop"]
CRENEAUX_PAR_JOUR = 48
