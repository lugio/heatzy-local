"""Protocole LAN Gizwits GAgent, en asyncio.

Etabli par retro-conception le 2026-10-19/20 : APK com.gizwits.heatzy 8.2.6,
sondage de l'appareil reel, et specification d'ecriture de
markosharknz1/ha-jebao-pumps (PROTOCOL.md), elle-meme tracee par
decompilation de transDatasToP0Data et confirmee contre des trames capturees.

    trame = 00 00 00 03 | longueur(varint) | flag(1) | commande(2) | charge
"""
from __future__ import annotations

import asyncio
import logging
import re

from .const import (ACTION_ECRITURE, ACTION_LECTURE, CMD_CONTROLE, CMD_DECOUVERTE,
                    CMD_LECTURE, CMD_LOGIN, CMD_PASSCODE, DELAI_RESEAU, ENTETE,
                    PORT_CONTROLE, PORT_DECOUVERTE)

_LOGGER = logging.getLogger(__name__)


def _varint(n: int) -> bytes:
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out


def _trame(commande: int, charge: bytes = b"", flag: int = 0) -> bytes:
    corps = bytes([flag]) + commande.to_bytes(2, "big") + charge
    return ENTETE + _varint(len(corps)) + corps


class ErreurHeatzy(Exception):
    """Echec de communication avec l'appareil."""


def _lire_varint(d: bytes, i: int) -> tuple[int, int]:
    n = decalage = 0
    while i < len(d):
        o = d[i]
        n |= (o & 0x7F) << decalage
        i += 1
        if not o & 0x80:
            return n, i
        decalage += 7
    raise ErreurHeatzy("varint tronque")


def _depiler(d: bytes):
    """Decoupe un tampon en trames (commande, charge).

    Indispensable : l'appareil emet spontanement des trames 0x0093 a chaque
    changement d'etat, et plusieurs trames arrivent dans le meme paquet TCP.
    Decoder a l'aveugle le 10e octet d'un tampon quelconque donne des valeurs
    fantaisistes -- c'est ainsi qu'une puissance de 21845 W (0x5555) a ete
    publiee le 2026-10-20.
    """
    i = 0
    while i + 4 <= len(d):
        if d[i:i + 4] != ENTETE:
            i += 1
            continue
        try:
            taille, j = _lire_varint(d, i + 4)
        except ErreurHeatzy:
            return
        if taille < 3 or j + taille > len(d):
            return
        corps = d[j:j + taille]
        yield int.from_bytes(corps[1:3], "big"), corps[3:]
        i = j + taille


async def decouvrir(hote: str) -> dict:
    """Identite de l'appareil, par UDP. N'exige aucune authentification."""
    boucle = asyncio.get_running_loop()
    futur = boucle.create_future()

    class _Proto(asyncio.DatagramProtocol):
        def datagram_received(self, data, _addr):
            if not futur.done():
                futur.set_result(data)

        def error_received(self, exc):
            if not futur.done():
                futur.set_exception(exc)

    transport, _ = await boucle.create_datagram_endpoint(
        _Proto, remote_addr=(hote, PORT_DECOUVERTE))
    try:
        transport.sendto(_trame(CMD_DECOUVERTE))
        data = await asyncio.wait_for(futur, DELAI_RESEAU)
    except (asyncio.TimeoutError, OSError) as err:
        raise ErreurHeatzy("aucune reponse de %s" % hote) from err
    finally:
        transport.close()

    txt = data.decode("latin-1")
    pk = re.search(r"[0-9a-f]{32}", txt)
    did = re.search(r"[A-Za-z0-9]{22}", txt)
    return {"host": hote,
            "product_key": pk.group(0) if pk else None,
            "did": did.group(0) if did else None}


class Appareil:
    """Session locale courte, fermée après chaque opération et chaque échec.

    Les indisponibilités observées après écriture ne prouvent pas un
    redémarrage systématique du micrologiciel.
    """

    def __init__(self, hote: str, definition: dict) -> None:
        self.hote = hote
        self.definition = definition
        self._attrs: list[dict] = []
        for ent in definition.get("entities", []):
            self._attrs.extend(ent.get("attrs", []))
        self._inscriptibles = [a for a in self._attrs
                               if "writable" in (a.get("type") or "")]
        # la trame de donnees doit couvrir le dernier datapoint du schema,
        # sinon elle est tronquee et les positions ne veulent rien dire
        self._taille_attendue = max(
            (a["position"]["byte_offset"] +
             (a["position"]["len"] if a["position"]["unit"] == "byte" else 1))
            for a in self._attrs) if self._attrs else 0

    # ── bas niveau ────────────────────────────────────────────────────────
    async def _reponse(self, lect, attendue: int) -> bytes:
        """Attend la commande demandée sans confondre notification et réponse."""
        for _ in range(12):
            commande, charge = await asyncio.wait_for(
                self._trame_suivante(lect), DELAI_RESEAU)
            if commande == attendue:
                return charge
        raise ErreurHeatzy("réponse attendue absente de %s" % self.hote)

    async def _session(self):
        ecr = None
        try:
            lect, ecr = await asyncio.wait_for(
                asyncio.open_connection(self.hote, PORT_CONTROLE), DELAI_RESEAU)
            ecr.write(_trame(CMD_PASSCODE))
            await ecr.drain()
            charge = await self._reponse(lect, CMD_PASSCODE + 1)
            if len(charge) < 2:
                raise ErreurHeatzy("challenge local tronqué")
            n = int.from_bytes(charge[:2], "big")
            passcode = charge[2:]
            if not n or len(passcode) != n:
                raise ErreurHeatzy("longueur du challenge local invalide")
            ecr.write(_trame(CMD_LOGIN, charge[:2] + passcode))
            await ecr.drain()
            resultat = await self._reponse(lect, CMD_LOGIN + 1)
            if resultat != b"\x00":
                raise ErreurHeatzy("login local refusé par %s" % self.hote)
            return lect, ecr
        except asyncio.CancelledError:
            if ecr is not None:
                self._fermer(ecr)
            raise
        except (ErreurHeatzy, OSError, asyncio.IncompleteReadError) as err:
            if ecr is not None:
                self._fermer(ecr)
            if isinstance(err, ErreurHeatzy):
                raise
            raise ErreurHeatzy("authentification locale interrompue sur %s"
                               % self.hote) from err

    @staticmethod
    def _fermer(ecr) -> None:
        try:
            ecr.close()
        except Exception:  # noqa: BLE001 - fermeture de confort
            pass

    # ── lecture ───────────────────────────────────────────────────────────
    @staticmethod
    async def _trame_suivante(lect) -> tuple[int, bytes]:
        """Lit UNE trame, en suivant le prefixe de longueur.

        Indispensable : read() rend ce qui est disponible, pas une trame. Sur
        une lecture partielle, les octets restants commencent au milieu d'une
        trame et une resynchronisation sur un faux en-tete decode des positions
        decalees -- un mode `cft` devenait `eco` un sondage sur deux.
        """
        fenetre = await lect.readexactly(4)
        for _ in range(4096):
            if fenetre == ENTETE:
                break
            fenetre = fenetre[1:] + await lect.readexactly(1)
        else:
            raise ErreurHeatzy("entete introuvable")
        octets = b""
        for _ in range(8):
            o = await lect.readexactly(1)
            octets += o
            if not o[0] & 0x80:
                break
        else:
            raise ErreurHeatzy("varint de longueur aberrant")
        taille, _ = _lire_varint(octets, 0)
        if not 3 <= taille <= 65535:
            raise ErreurHeatzy("longueur de trame aberrante : %d" % taille)
        corps = await lect.readexactly(taille)
        return int.from_bytes(corps[1:3], "big"), corps[3:]

    async def lire(self) -> dict:
        lect, ecr = await self._session()
        try:
            ecr.write(_trame(CMD_LECTURE, bytes([ACTION_LECTURE])))
            await ecr.drain()
            # On consomme les trames une a une jusqu'a la reponse de lecture :
            # l'appareil intercale des notifications 0x0093 spontanees, dont la
            # charge a un tout autre format (DID prefixe, 131 octets).
            for _ in range(12):
                try:
                    commande, charge = await asyncio.wait_for(
                        self._trame_suivante(lect), DELAI_RESEAU)
                except (asyncio.TimeoutError, asyncio.IncompleteReadError) as err:
                    raise ErreurHeatzy(
                        "flux interrompu par %s" % self.hote) from err
                if commande != CMD_LECTURE + 1:
                    continue
                donnees = charge[1:]   # octet 0 = action
                if len(donnees) < self._taille_attendue:
                    raise ErreurHeatzy(
                        "reponse de lecture tronquee : %d octets pour %d attendus"
                        % (len(donnees), self._taille_attendue))
                return self._decoder(donnees)
            raise ErreurHeatzy("aucune reponse de lecture de %s" % self.hote)
        except (OSError, asyncio.IncompleteReadError) as err:
            raise ErreurHeatzy("lecture locale interrompue sur %s" % self.hote) from err
        finally:
            self._fermer(ecr)

    def _decoder(self, d: bytes) -> dict:
        out: dict = {}
        for a in self._attrs:
            p = a["position"]
            o = p["byte_offset"]
            if o >= len(d):
                continue
            if p["unit"] == "bit":
                v = (d[o] >> p["bit_offset"]) & ((1 << p["len"]) - 1)
                if a["data_type"] == "bool":
                    v = bool(v)
                elif a["data_type"] == "enum":
                    v = a["enum"][v] if v < len(a["enum"]) else v
            else:
                v = int.from_bytes(d[o:o + p["len"]], "big")
            out[a["name"]] = v
        for base in ("cft_temp", "eco_temp"):
            lo, hi = out.get(base + "L"), out.get(base + "H")
            if lo is not None and hi is not None:
                out[base] = round((hi * 256 + lo) / 10.0, 1)
        if "power_dataL" in out and "power_dataH" in out:
            out["puissance"] = out["power_dataH"] * 256 + out["power_dataL"]
        from .const import MODES_ORDRE
        cm = out.get("cur_mode")
        if isinstance(cm, int) and cm < len(MODES_ORDRE):
            out["mode_effectif"] = MODES_ORDRE[cm]
        h, m = out.get("hour"), out.get("minute")
        if h is not None and m is not None:
            out["horloge"] = "%02d:%02d" % (h, m)
        # Temperature mesuree par le radiateur : cur_tempL SEUL, en dixiemes.
        # Composer cur_tempH*256+cur_tempL donne 75 degres pour une piece a 20.
        # C'est aussi ce que fait l'integration de reference cyr-ius/hass-heatzy
        # pour cette famille d'appareils.
        # Sonde du radiateur : ne pas l'assimiler à une température ambiante
        # calibrée. L'interprétation des octets reste limitée à ce modèle.
        lo = out.get("cur_tempL")
        if lo is not None:
            out["temperature_interne"] = round(lo / 10.0, 1)
        out["programme_creneau"] = self._creneau_courant(out)
        return out

    @staticmethod
    def _creneau_courant(etat: dict) -> str | None:
        """L'ordre que le programme interne reclame pour le creneau en cours.

        Le créneau prévu ne prouve pas que le programme est actif : l'APK
        Onyx utilise derog_mode=1 pour son activation. L'appareil rapporte
        sa propre horloge, dont la fraîcheur doit être vérifiée séparément.
        """
        from .const import MODES_PROGRAMME
        jour, heure, minute = etat.get("week"), etat.get("hour"), etat.get("minute")
        if None in (jour, heure, minute) or not 1 <= jour <= 7:
            return None
        creneau = heure * 2 + (1 if minute >= 30 else 0)
        octet = etat.get("p%d_data%d" % (jour, creneau // 4 + 1))
        if octet is None:
            return None
        return MODES_PROGRAMME[(octet >> ((creneau % 4) * 2)) & 3]

    # ── ecriture ──────────────────────────────────────────────────────────
    def _charge_ecriture(self, valeurs: dict, sequence: int) -> bytes:
        ecr = self._inscriptibles
        nb_flags = (max(a["id"] for a in ecr) // 8) + 1
        bits_total = sum(a["position"]["len"] for a in ecr
                         if a["position"]["unit"] == "bit")
        taille = max(a["position"]["byte_offset"] +
                     (a["position"]["len"] if a["position"]["unit"] == "byte" else 1)
                     for a in ecr)
        flags = bytearray(nb_flags)
        vals = bytearray(taille)
        par_nom = {a["name"]: a for a in ecr}
        for nom, v in valeurs.items():
            a = par_nom[nom]
            # drapeau : poids faible d'abord, PUIS tampon entier inverse
            flags[nb_flags - (a["id"] // 8) - 1] |= 1 << (a["id"] % 8)
            p = a["position"]
            if p["unit"] == "byte":
                spec = a.get("uint_spec") or {}
                brut = int(round((v - spec.get("addition", 0)) /
                                 (spec.get("ratio", 1) or 1)))
                vals[p["byte_offset"]:p["byte_offset"] + p["len"]] = \
                    brut.to_bytes(p["len"], "big")
            else:
                if a["data_type"] == "enum" and isinstance(v, str):
                    v = a["enum"].index(v)
                v = int(v)
                for i in range(p["len"]):
                    if not (v >> i) & 1:
                        continue
                    o = (p["byte_offset"] - ((p["bit_offset"] + i) >> 3)
                         + ((bits_total - 1) >> 3))
                    if 0 <= o < len(vals):
                        vals[o] |= 1 << ((p["bit_offset"] + i) & 7)
        p0 = bytes([ACTION_ECRITURE]) + bytes(flags) + bytes(vals)
        return sequence.to_bytes(4, "big") + p0

    async def ecrire(self, valeurs: dict, sequence: int = 1) -> None:
        """on_off et mode partagent l'octet 0 : il faut armer les DEUX
        drapeaux, sinon l'appareil remet on_off a 0."""
        lect, ecr = await self._session()
        try:
            ecr.write(_trame(CMD_CONTROLE, self._charge_ecriture(valeurs, sequence)))
            await ecr.drain()
            try:
                await asyncio.wait_for(lect.read(8192), DELAI_RESEAU)
            except asyncio.TimeoutError:
                pass   # l'accuse n'est pas un indicateur fiable, on relit apres
        finally:
            self._fermer(ecr)
