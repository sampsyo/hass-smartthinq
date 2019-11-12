import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Configuration values needed"""
from custom_components.smartthinq import CONF_LANGUAGE, CONF_MAX_RETRIES, KEY_SMARTTHINQ_DEVICES
from homeassistant.const import CONF_REGION, CONF_TOKEN

"""Device specific imports"""
from .DeviceTypes.LGAcDevice import LGAcDevice

def setup_platform(hass, config, add_devices, discovery_info=None):
    refresh_token = hass.data.get(CONF_TOKEN)
    country = hass.data.get(CONF_REGION)
    language = hass.data.get(CONF_LANGUAGE)

    # Set up the wideq client
    max_retries = hass.data.get(CONF_MAX_RETRIES)
    persistent_notification = hass.components.persistent_notification
    client = wideq.Client.from_token(refresh_token, country, language)

    airconditioners = []

    # Note: These devices are only connected when in use, otherwise
    # the 'wideq.NotConnectedError' is thrown. We ignore that here.
    fahrenheit = hass.config.units.temperature_unit != '°C'
    for device_id in hass.data[KEY_SMARTTHINQ_DEVICES]:
        device = client.get_device(device_id)
        if device.type == wideq.DeviceType.AC:
            try:
                d = LGAcDevice(client, max_retries, device, fahrenheit)
                airconditioners.append(d)
            except wideq.NotConnectedError:
                LOGGER.error('SmartThinQ device not available: %s', device.name)
                persistent_notification.async_create('SmartThinQ device not available: %s' % device.name, title='SmartThinQ Error')

    # Add the devices
    if airconditioners:
        for device in airconditioners:
            LOGGER.debug("Found LG Airconditioner: %s" % device.name)
        add_devices(airconditioners, True)
