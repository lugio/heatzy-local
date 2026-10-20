"""Consignes réglables : état de l'appareil, jamais préférence HA restaurée."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import EntiteHeatzy
from .datapoints import bornes_consigne, valeurs_consigne, attributs


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConsigneHeatzy(coord, base) for base in ("cft_temp", "eco_temp")]
                       + [ChampHeatzy(coord, champ) for champ in ("week", "hour", "minute", "derog_time")])


class ConsigneHeatzy(EntiteHeatzy, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coord, base):
        super().__init__(coord)
        self.base = base
        self._attr_translation_key = "confort" if base == "cft_temp" else "eco"
        self._attr_unique_id = f"{coord.did}_{base}_reglage"
        (self._attr_native_min_value, self._attr_native_max_value,
         self._attr_native_step) = bornes_consigne(coord.appareil.definition, base)

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.base)

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data or {}
        return {self.base + suffix: d.get(self.base + suffix) for suffix in ("L", "H")}

    async def async_set_native_value(self, value):
        try:
            valeurs = valeurs_consigne(self.coordinator.appareil.definition, self.base, value)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_ecrire_verifiee(valeurs)


class ChampHeatzy(EntiteHeatzy, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_step = 1

    def __init__(self, coord, champ):
        super().__init__(coord)
        self.champ = champ
        self._attr_translation_key = champ
        self._attr_unique_id = f"{coord.did}_{champ}_reglage"
        spec = attributs(coord.appareil.definition)[champ]["uint_spec"]
        self._attr_native_min_value = spec["min"]
        self._attr_native_max_value = spec["max"]

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.champ)

    @property
    def native_unit_of_measurement(self):
        if self.champ == "derog_time" and (self.coordinator.data or {}).get("derog_mode") == 2:
            return UnitOfTime.DAYS
        return None

    @property
    def extra_state_attributes(self):
        if self.champ == "derog_time":
            return {"description": "Jours en mode vacances ; unité non établie dans les autres modes"}
        return None

    async def async_set_native_value(self, value):
        if not self.native_min_value <= value <= self.native_max_value or int(value) != value:
            raise HomeAssistantError("valeur entière hors bornes du schéma")
        await self.coordinator.async_ecrire_verifiee({self.champ: int(value)})
