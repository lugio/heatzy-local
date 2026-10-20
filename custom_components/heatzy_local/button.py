"""Synchronisation manuelle de l'horloge du radiateur, sans cloud."""
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import EntiteHeatzy


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HorlogeHeatzy(hass.data[DOMAIN][entry.entry_id])])


class HorlogeHeatzy(EntiteHeatzy, ButtonEntity):
    _attr_translation_key = "synchroniser_horloge"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coord):
        super().__init__(coord)
        self._attr_unique_id = f"{coord.did}_synchroniser_horloge"

    async def async_press(self):
        await self.coordinator.async_synchroniser_horloge()
