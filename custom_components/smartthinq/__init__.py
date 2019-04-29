"""
Support for LG Smartthinq device.
This is made for korean only.
If you want to apply other county devices, you should change the code little bit.
"""
import logging
import wideq

import voluptuous as vol

from homeassistant.const import (
    CONF_TOKEN, )
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

DOMAIN = 'smartthinq'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_TOKEN): cv.string,
        })
}, extra=vol.ALLOW_EXTRA)

LGE_DEVICES = 'lge_devices'

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    import wideq
    _LOGGER.info("Creating new LGE component")

    if LGE_DEVICES not in hass.data:
        hass.data[LGE_DEVICES] = []
    
    refresh_token = config[DOMAIN][CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)
    
    hass.data[CONF_TOKEN] = refresh_token
    
    for device in client.devices:
        device_id = device.id
        hass.data[LGE_DEVICES].append(device_id)
        
    return True
    
    
class LGEDevice(Entity):
	
    def __init__(self, client, device):
        self._client = client
        self._device = device
        
    @property
    def name(self):
        return self._device.name

    @property
    def available(self):
        return True
