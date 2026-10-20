"""Interrupteurs : verrouillage des touches et programme horaire de l'appareil."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EntiteHeatzy


@dataclass(frozen=True, kw_only=True)
class DescriptionInterrupteur(SwitchEntityDescription):
    datapoint: str
    valeur: Callable[[dict], bool | None]


INTERRUPTEURS: tuple[DescriptionInterrupteur, ...] = (
    DescriptionInterrupteur(
        key="verrouillage", translation_key="verrouillage",
        icon="mdi:lock", entity_category=EntityCategory.CONFIG,
        datapoint="LOCK_C", valeur=lambda d: bool(d["LOCK_C"]) if "LOCK_C" in d else None,
    ),
    # Le schéma décrit 1=serveur, 0=appareil, mais cela ne démontre pas
    # l'activation du planning Onyx : l'APK utilise derog_mode=1 pour PROG.
    # Conserver ce champ distinct sans lui attribuer tout retour de preset.
    DescriptionInterrupteur(
        key="pilotage_serveur", translation_key="pilotage_serveur",
        icon="mdi:home-assistant", entity_category=EntityCategory.CONFIG,
        datapoint="timer_switch", valeur=lambda d: bool(d["timer_switch"]) if "timer_switch" in d else None,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(InterrupteurHeatzy(coord, d) for d in INTERRUPTEURS)


class InterrupteurHeatzy(EntiteHeatzy, SwitchEntity):
    entity_description: DescriptionInterrupteur

    def __init__(self, coordinator, description: DescriptionInterrupteur) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = "%s_%s" % (coordinator.did, description.key)

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.valeur(self.coordinator.data or {})

    async def _ecrire(self, valeur: bool) -> None:
        await self.coordinator.async_ecrire_verifiee(
            {self.entity_description.datapoint: int(valeur)})

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._ecrire(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._ecrire(False)
