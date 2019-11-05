import logging

"""Configuration values needed"""
from custom_components.smartthinq import (
    CONF_LANGUAGE, DEPRECATION_WARNING, KEY_DEPRECATED_COUNTRY,
    KEY_DEPRECATED_LANGUAGE, KEY_DEPRECATED_REFRESH_TOKEN)
from homeassistant.const import CONF_REGION, CONF_TOKEN

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
from .LGDevices.LGDishwasherDevice import LGDishwasherDevice

def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    """Set up the LG dishwasher devices"""
    if any(key in config for key in ((KEY_DEPRECATED_REFRESH_TOKEN, KEY_DEPRECATED_COUNTRY, KEY_DEPRECATED_LANGUAGE))):
        LOGGER.warning(DEPRECATION_WARNING)

    refresh_token = config.get(KEY_DEPRECATED_REFRESH_TOKEN) or \
        hass.data.get(CONF_TOKEN)
    country = config.get(KEY_DEPRECATED_COUNTRY) or \
        hass.data.get(CONF_REGION)
    language = config.get(KEY_DEPRECATED_LANGUAGE) or \
        hass.data.get(CONF_LANGUAGE)

    client = wideq.Client.from_token(refresh_token, country, language)
    add_devices(_dishwashers(hass, client), True)

def _dishwashers(hass, client):
    """Generate all the dishwasher devices associated with the user's
    LG account.

    Log errors for devices that can't be used for whatever reason.
    """

    import wideq

    for device in client.devices:
        if device.type == wideq.DeviceType.DISHWASHER:
            try:
                d = LGDishwasherDevice(client, device)
            except wideq.NotConnectedError:
                # Dishwashers are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass
            else:
                yield d
