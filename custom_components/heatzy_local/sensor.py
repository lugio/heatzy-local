"""Capteurs : données brutes, états et consignes rapportés par le radiateur."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription, SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EntiteHeatzy
from .datapoints import programmes


@dataclass(frozen=True, kw_only=True)
class DescriptionHeatzy(SensorEntityDescription):
    valeur: Callable[[dict], float | str | None]


CAPTEURS: tuple[DescriptionHeatzy, ...] = (
    # Champ power_data H/L : signification physique et unité non établies.
    # Mission4 : 24 paires avec le Shelly ne justifient ni W ni Wh/kWh.
    # Valeur non monotone ; conserver le brut sans classe ni unité.
    # La clé historique reste stable pour préserver les références existantes.
    DescriptionHeatzy(
        key="conso_rapportee", translation_key="conso_rapportee",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        valeur=lambda d: d.get("puissance"),
    ),
    DescriptionHeatzy(
        key="consigne_confort", translation_key="consigne_confort",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        valeur=lambda d: d.get("cft_temp"),
    ),
    DescriptionHeatzy(
        key="consigne_eco", translation_key="consigne_eco",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        valeur=lambda d: d.get("eco_temp"),
    ),
    # La sonde du radiateur, pas celle de la piece : voir gizwits.py et le
    # README. L'ecart avec une sonde d'ambiance est ce qui explique pourquoi
    # l'appareil sous-chauffe.
    DescriptionHeatzy(
        key="temperature_interne", translation_key="temperature_interne",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        valeur=lambda d: d.get("temperature_interne"),
    ),
    # APK Onyx : correction thermique (brut-5), pas qualité Wi-Fi.
    # Certaines valeurs matérielles sont hors plage de l'UI : garder le brut.
    DescriptionHeatzy(
        key="com_temp", translation_key="com_temp",
        entity_category=EntityCategory.DIAGNOSTIC,
        valeur=lambda d: d.get("com_temp"),
    ),
    # Créneau prévu selon l'horloge rapportée, sans supposer le programme actif.
    DescriptionHeatzy(
        key="programme_creneau", translation_key="programme_creneau",
        device_class=SensorDeviceClass.ENUM,
        options=["cft", "eco", "fro", "stop"],
        entity_category=EntityCategory.DIAGNOSTIC,
        valeur=lambda d: d.get("programme_creneau"),
    ),
    # Le mode reellement applique par l'appareil. Il peut differer de la
    # consigne quand un programme horaire ou une derogation agit : c'est ce
    # qui permet de voir que le radiateur ne fait pas ce qu'on lui demande.
    DescriptionHeatzy(
        key="mode_effectif", translation_key="mode_effectif",
        device_class=SensorDeviceClass.ENUM,
        options=["cft", "eco", "fro", "stop", "cft1", "cft2"],
        entity_category=EntityCategory.DIAGNOSTIC,
        valeur=lambda d: d.get("mode_effectif"),
    ),
    DescriptionHeatzy(
        key="derogation", translation_key="derogation",
        entity_category=EntityCategory.DIAGNOSTIC,
        valeur=lambda d: d.get("derog_time"),
    ),
    DescriptionHeatzy(
        key="programme", translation_key="programme",
        valeur=lambda d: sum(v is not None for v in programmes(d).values()) or None,
    ),
    # L'horloge interne : elle sert a verifier qu'on lit bien l'appareil et
    # non un cache. Si elle derive, le programme horaire se decale.
    DescriptionHeatzy(
        key="horloge", translation_key="horloge",
        entity_category=EntityCategory.DIAGNOSTIC,
        valeur=lambda d: d.get("horloge"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(CapteurHeatzy(coord, d) for d in CAPTEURS)


class CapteurHeatzy(EntiteHeatzy, SensorEntity):
    entity_description: DescriptionHeatzy

    def __init__(self, coordinator, description: DescriptionHeatzy) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = "%s_%s" % (coordinator.did, description.key)

    @property
    def native_value(self) -> float | None:
        return self.entity_description.valeur(self.coordinator.data or {})


    @property
    def extra_state_attributes(self):
        if self.entity_description.key == "temperature_interne":
            d = self.coordinator.data or {}
            return {"cur_tempL": d.get("cur_tempL"), "cur_tempH": d.get("cur_tempH"),
                    "decodage": "cur_tempL/10 mesuré sur ces appareils ; octet H non interprété"}
        if self.entity_description.key == "conso_rapportee":
            d = self.coordinator.data or {}
            return {"power_dataL": d.get("power_dataL"), "power_dataH": d.get("power_dataH"),
                    "unite": "non établie", "periode": "non établie"}
        if self.entity_description.key == "mode_effectif":
            return {"cur_mode": (self.coordinator.data or {}).get("cur_mode")}
        if self.entity_description.key == "programme":
            return {"jours": programmes(self.coordinator.data or {}),
                    "debut": "00:00", "creneau_minutes": 30,
                    "jours_iso": {"1": "lundi", "2": "mardi", "3": "mercredi", "4": "jeudi",
                                  "5": "vendredi", "6": "samedi", "7": "dimanche"}}
        if self.entity_description.key == "horloge":
            d = self.coordinator.data or {}
            return {k: d.get(k) for k in ("week", "hour", "minute", "_lu_a")}
        if self.entity_description.key == "com_temp":
            brut = (self.coordinator.data or {}).get("com_temp")
            return {"description": "Code de correction thermique ; encodage hors plage non élucidé",
                    "correction_selon_apk": brut - 5 if isinstance(brut, int) and 0 <= brut <= 10 else None}
        return None
