"""Le radiateur, vu comme un thermostat Home Assistant."""
from __future__ import annotations

from homeassistant.components.climate import (ClimateEntity, ClimateEntityFeature,
                                              HVACMode)
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (DOMAIN, MODE_ARRET, MODE_VERS_PRESET, PRESET_VERS_MODE)
from .entity import EntiteHeatzy


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ThermostatHeatzy(hass.data[DOMAIN][entry.entry_id])])


class ThermostatHeatzy(EntiteHeatzy, ClimateEntity):
    """Pilotage par ordres fil pilote.

    Ce modèle n'accepte que quatre ordres : confort, éco, hors-gel et arrêt.
    « Confort −1 » et « Confort −2 » figurent au schéma de la gamme Heatzy mais
    l'appareil masque la valeur sur deux bits : ils ne sont pas exposés."""

    _attr_name = None
    _attr_translation_key = "radiateur"
    # obligatoire : ClimateEntity.capability_attributes le lit au moment
    # d'ajouter l'entite, et leve sans lui.
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (ClimateEntityFeature.PRESET_MODE
                                | ClimateEntityFeature.TURN_ON
                                | ClimateEntityFeature.TURN_OFF)
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = list(MODE_VERS_PRESET.values())

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "%s_climate" % coordinator.did

    @property
    def _mode(self) -> str | None:
        return (self.coordinator.data or {}).get("mode")

    @property
    def current_temperature(self) -> float | None:
        """La temperature SUR LAQUELLE l'appareil regule.

        C'est sa propre sonde, pas la piece : elle lit plus chaud que
        l'ambiance (un écart a été observé lors des essais). On l'expose quand meme, car
        c'est elle qui explique le comportement du radiateur -- mais ne pas
        s'en servir comme temperature ambiante.
        """
        return (self.coordinator.data or {}).get("temperature_interne")

    @property
    def hvac_mode(self) -> HVACMode:
        return (HVACMode.OFF if self._mode == MODE_ARRET or
                (self.coordinator.data or {}).get("on_off") is False else HVACMode.HEAT)

    @property
    def preset_mode(self) -> str | None:
        return MODE_VERS_PRESET.get(self._mode)

    async def _appliquer(self, mode: str) -> None:
        await self.coordinator.async_ecrire_verifiee({"on_off": True, "mode": mode})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._appliquer(PRESET_VERS_MODE[preset_mode])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode is HVACMode.OFF:
            # L'arrêt peut rendre la pile réseau indisponible une dizaine
            # de secondes ; ne pas relire immédiatement après cet ordre.
            await self._appliquer(MODE_ARRET)
            return
        if hvac_mode is not HVACMode.HEAT:
            raise HomeAssistantError("mode HVAC non pris en charge")

        mode = self._mode
        if mode in MODE_VERS_PRESET and (self.coordinator.data or {}).get("on_off"):
            # HEAT active le chauffage, sans choisir un nouveau preset.
            # Une automatisation peut ensuite demander confort sans passage fugitif en éco.
            return
        await self._appliquer(mode if mode in MODE_VERS_PRESET else "cft")

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self._appliquer(MODE_ARRET)
