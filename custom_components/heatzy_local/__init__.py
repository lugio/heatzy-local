"""Intégration Heatzy local — pilotage des radiateurs sans le cloud Gizwits."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_HOST, CONF_NOM, DOMAIN
from .coordinator import CoordinateurHeatzy
from .services import enregistrer_services
from .gizwits import Appareil, ErreurHeatzy, decouvrir

_LOGGER = logging.getLogger(__name__)
PLATEFORMES = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.BUTTON, Platform.SELECT]


def _charger_definition(product_key: str) -> dict:
    """Le schéma des datapoints du produit, livré avec l'intégration."""
    chemin = Path(__file__).parent / "schemas" / ("%s.json" % product_key)
    if not chemin.exists():
        raise ErreurHeatzy("schéma absent pour le produit %s" % product_key)
    return json.loads(chemin.read_text(encoding="utf-8"))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hote = entry.data[CONF_HOST]
    try:
        ident = await decouvrir(hote)
        definition = await hass.async_add_executor_job(
            _charger_definition, ident["product_key"])
    except ErreurHeatzy as err:
        raise ConfigEntryNotReady(str(err)) from err

    appareil = Appareil(hote, definition)
    coord = CoordinateurHeatzy(hass, appareil, entry.data[CONF_NOM], ident["did"])
    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    enregistrer_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATEFORMES)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATEFORMES)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "mettre_a_l_heure")
            hass.services.async_remove(DOMAIN, "ecrire_programme")
    return ok
