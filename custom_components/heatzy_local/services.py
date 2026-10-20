"""Actions locales ciblées sur l'entité climate du radiateur."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .datapoints import valeurs_programme, MODES


def enregistrer_services(hass):
    if hass.services.has_service(DOMAIN, "mettre_a_l_heure"):
        return

    def coordinateur(call):
        entree = er.async_get(hass).async_get(call.data["entity_id"])
        if entree is None or entree.platform != DOMAIN:
            raise HomeAssistantError("entité Heatzy local attendue")
        coord = hass.data.get(DOMAIN, {}).get(entree.config_entry_id)
        if coord is None:
            raise HomeAssistantError("radiateur non chargé")
        return coord

    async def horloge(call):
        await coordinateur(call).async_synchroniser_horloge()

    hass.services.async_register(DOMAIN, "mettre_a_l_heure", horloge,
                                 schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}))

    async def programme(call):
        try:
            valeurs = valeurs_programme(call.data["jour"], call.data["ordres"])
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        await coordinateur(call).async_ecrire_verifiee(valeurs)

    def jour_valide(valeur):
        if type(valeur) is not int or not 0 <= valeur <= 7:
            raise vol.Invalid("jour attendu : 0 (tous) ou 1..7")
        return valeur

    hass.services.async_register(DOMAIN, "ecrire_programme", programme,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id,
                           vol.Required("jour"): jour_valide,
                           vol.Required("ordres"): vol.All([vol.In(MODES)], vol.Length(min=48, max=48))}))
