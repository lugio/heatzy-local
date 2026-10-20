"""Coordinateur de relevés pour un radiateur Heatzy local."""
from __future__ import annotations

import logging
import json
import os
import re
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MODES_ORDRE, PERIODE_RELEVE
from .gizwits import Appareil, ErreurHeatzy
from .datapoints import valeurs_horloge, horloge_confirmee
from .transactions import Transaction, EcritureNonConfirmee

_LOGGER = logging.getLogger(__name__)


class CoordinateurHeatzy(DataUpdateCoordinator[dict]):
    """Interroge l'appareil en local et met l'état à disposition des entités."""

    def __init__(self, hass: HomeAssistant, appareil: Appareil, nom: str,
                 did: str) -> None:
        super().__init__(
            hass, _LOGGER, name="%s (%s)" % (nom, appareil.hote),
            update_interval=timedelta(seconds=PERIODE_RELEVE),
        )
        self.appareil = appareil
        self.nom = nom
        self.did = did
        self._echecs = 0
        self.transaction = Transaction(appareil, self._sauvegarder)

    async def _sauvegarder(self, etat: dict, demande: dict) -> None:
        def sauvegarder():
            dossier = Path(self.hass.config.path("heatzy_local_backups"))
            dossier.mkdir(mode=0o700, parents=True, exist_ok=True)
            ident = re.sub(r"[^a-zA-Z0-9_-]", "_", self.did)
            chemin = dossier / (ident + "_" + uuid4().hex + ".json")
            contenu = {"date": datetime.now(timezone.utc).isoformat(),
                       "did": self.did, "avant": etat, "demande": demande}
            fd = os.open(chemin, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fichier:
                json.dump(contenu, fichier, ensure_ascii=False)
                fichier.flush()
                os.fsync(fichier.fileno())
        await self.hass.async_add_executor_job(sauvegarder)

    async def async_ecrire_verifiee(self, valeurs: dict, verifier=None) -> None:
        try:
            etat = await self.transaction.ecrire(valeurs, verifier)
        except EcritureNonConfirmee as err:
            self.async_set_updated_data(err.etat)
            raise HomeAssistantError(str(err)) from err
        except (ErreurHeatzy, OSError, TimeoutError, ValueError) as err:
            raise HomeAssistantError("écriture non vérifiée sur %s : %s"
                                     % (self.nom, err)) from err
        self._echecs = 0
        etat["_lu_a"] = datetime.now(timezone.utc).isoformat()
        self.async_set_updated_data(etat)

    async def async_synchroniser_horloge(self) -> None:
        await self.async_ecrire_verifiee(
            lambda: valeurs_horloge(datetime.now(ZoneInfo(self.hass.config.time_zone))),
            horloge_confirmee)

    async def _async_update_data(self) -> dict:
        try:
            donnees = await self.transaction.lire()
        except ErreurHeatzy as err:
            # Un echec isole ne doit pas rendre les entites indisponibles :
            # le Wi-Fi de ces radiateurs est le maillon faible, et l'appareil
            # ferme ses sessions sans prevenir. On garde l'etat precedent et
            # on ne declare l'echec qu'apres trois sondages rates d'affilee.
            self._echecs += 1
            if self._echecs < 3 and self.data:
                _LOGGER.debug("lecture %d/3 ratee sur %s : %s",
                              self._echecs, self.appareil.hote, err)
                return self.data
            raise UpdateFailed(str(err)) from err
        self._echecs = 0
        donnees["_lu_a"] = datetime.now(timezone.utc).isoformat()
        return donnees
