import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Configuration values needed"""
from custom_components.smartthinq import CONF_LANGUAGE, CONF_MAX_RETRIES
from homeassistant.const import CONF_REGION, CONF_TOKEN

"""Device specific imports"""
from .LGDevices.LGDishwasherDevice import LGDishwasherDevice

def setup_platform(hass, config, add_devices, discovery_info=None):
    refresh_token = hass.data.get(CONF_TOKEN)
    country = hass.data.get(CONF_REGION)
    language = hass.data.get(CONF_LANGUAGE)

    """Set up the wideq client"""
    import wideq
    client = wideq.Client.from_token(refresh_token, country, language)

    """Add the devices"""
    add_devices(_wideq_sensors(hass, client), True)

def _wideq_sensors(hass, client):
    """Generate all the sensor devices associated with the user's
    LG account.

    Log errors for devices that can't be used for whatever reason.
    """

    import wideq

    max_retries = hass.data.get(CONF_MAX_RETRIES)
    for device in client.devices:
        if device.type == wideq.DeviceType.DISHWASHER:
            try:
                d = LGDishwasherDevice(client, device, max_retries)
            except wideq.NotConnectedError:
                # Dishwashers are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass
            else:
                yield d
