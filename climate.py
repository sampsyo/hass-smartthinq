
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Configuration values needed"""
from custom_components.smartthinq import CONF_LANGUAGE, CONF_MAX_RETRIES
from homeassistant.const import CONF_REGION, CONF_TOKEN

"""Device specific imports"""
from .DeviceTypes.LGClimateDevice import LGClimateDevice

def setup_platform(hass, config, add_devices, discovery_info=None):
    refresh_token = hass.data.get(CONF_TOKEN)
    country = hass.data.get(CONF_REGION)
    language = hass.data.get(CONF_LANGUAGE)

    """Set up the wideq client"""
    import wideq
    client = wideq.Client.from_token(refresh_token, country, language)

    """Add the devices"""
    add_devices(_wideq_ac_devices(hass, client), True)

def _wideq_ac_devices(hass, client):
    """Generate all the AC (climate) devices associated with the user's
    LG account.

    Log errors for devices that can't be used for whatever reason.
    """
    import wideq

    max_retries = hass.data.get(CONF_MAX_RETRIES)
    fahrenheit = hass.config.units.temperature_unit != '°C'
    persistent_notification = hass.components.persistent_notification
    
    for device in client.devices:
        if device.type == wideq.DeviceType.AC:
            try:
                d = LGClimateDevice(client, device, max_retries, fahrenheit)
            except wideq.NotConnectedError:
                LOGGER.error(
                    'SmartThinQ device not available: %s', device.name
                )
                persistent_notification.async_create(
                    'SmartThinQ device not available: %s' % device.name,
                    title='SmartThinQ Error',
                )
            else:
                yield d


