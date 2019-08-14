"""
Support for LG Smartthinq devices.
"""
import logging
import wideq

import voluptuous as vol

from homeassistant.const import CONF_REGION, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

DOMAIN = 'smartthinq'

CONF_LANGUAGE = 'language'
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_TOKEN): cv.string,
        CONF_REGION: cv.string,
        CONF_LANGUAGE: cv.string,
        })
}, extra=vol.ALLOW_EXTRA)


LOGGER = logging.getLogger(__name__)

SMARTTHINQ_COMPONENTS = [
    'sensor'
]
KEY_SMARTTHINQ_DEVICES = 'smartthinq_devices'

def setup(hass, config):
    if KEY_SMARTTHINQ_DEVICES not in hass.data:
        hass.data[KEY_SMARTTHINQ_DEVICES] = []

    refresh_token = config[DOMAIN].get(CONF_TOKEN)
    region = config[DOMAIN].get(CONF_REGION)
    language = config[DOMAIN].get(CONF_LANGUAGE)

    client = wideq.Client.from_token(refresh_token, region, language)

    hass.data[CONF_TOKEN] = refresh_token
    hass.data[CONF_REGION] = region
    hass.data[CONF_LANGUAGE] = language

    for device in client.devices:
        hass.data[KEY_SMARTTHINQ_DEVICES].append(device.id)

    for component in SMARTTHINQ_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)
    return True


class LGDevice(Entity):
    def __init__(self, client, device):
        self._client = client
        self._device = device

    @property
    def name(self):
        return self._device.name

    @property
    def available(self):
        return True
