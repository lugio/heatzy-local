"""Configuration de l'intégration depuis l'interface de Home Assistant."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv

from .const import CONF_HOST, CONF_NOM, DOMAIN
from .gizwits import ErreurHeatzy, decouvrir


class FluxHeatzy(ConfigFlow, domain=DOMAIN):
    """Demande l'adresse du radiateur et vérifie qu'il répond en local."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        erreurs: dict[str, str] = {}
        if user_input is not None:
            try:
                ident = await decouvrir(user_input[CONF_HOST])
            except ErreurHeatzy:
                erreurs["base"] = "injoignable"
            else:
                if not ident.get("did"):
                    erreurs["base"] = "pas_un_heatzy"
                else:
                    await self.async_set_unique_id(ident["did"])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NOM], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_NOM, default="Radiateur"): cv.string,
            }),
            errors=erreurs,
        )
