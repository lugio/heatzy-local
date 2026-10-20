"""Modes Onyx constatés dans l'APK, sans prétendre lire la présence."""
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import EntiteHeatzy

MODES = {"off": 0, "programme": 1, "vacances": 2, "auto": 3}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DerogationHeatzy(hass.data[DOMAIN][entry.entry_id])])


class DerogationHeatzy(EntiteHeatzy, SelectEntity):
    _attr_translation_key = "derogation"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(MODES)

    def __init__(self, coord):
        super().__init__(coord)
        self._attr_unique_id = f"{coord.did}_derog_mode_reglage"

    @property
    def current_option(self):
        code = (self.coordinator.data or {}).get("derog_mode")
        return next((nom for nom, valeur in MODES.items() if valeur == code), None)

    @property
    def extra_state_attributes(self):
        return {"code_brut": (self.coordinator.data or {}).get("derog_mode"),
                "auto": "Mode de détection armable ; aucun état de présence remonté",
                "codes_non_documentes": [4, 5]}

    async def async_select_option(self, option):
        if option not in MODES:
            raise HomeAssistantError("mode de dérogation non documenté")
        await self.coordinator.async_ecrire_verifiee({"derog_mode": MODES[option]})
