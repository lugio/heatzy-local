"""Base commune aux entités : rattachement à l'appareil et disponibilité."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoordinateurHeatzy


class EntiteHeatzy(CoordinatorEntity[CoordinateurHeatzy]):
    """Toutes les entités partagent le même appareil dans le registre."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CoordinateurHeatzy) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.did)},
            name=coordinator.nom,
            manufacturer="Heatzy",
            model="Onyx",
            configuration_url=None,
        )
