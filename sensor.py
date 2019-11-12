import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Configuration values needed"""
from custom_components.smartthinq import CONF_LANGUAGE, CONF_MAX_RETRIES, KEY_SMARTTHINQ_DEVICES
from homeassistant.const import CONF_REGION, CONF_TOKEN

"""Device specific imports"""
from .DeviceTypes.LGDishwasherDevice import LGDishwasherDevice
from .DeviceTypes.LGDryerDevice import LGDryerDevice

def setup_platform(hass, config, add_devices, discovery_info=None):
    refresh_token = hass.data.get(CONF_TOKEN)
    country = hass.data.get(CONF_REGION)
    language = hass.data.get(CONF_LANGUAGE)

    # Set up the wideq client
    max_retries = hass.data.get(CONF_MAX_RETRIES)
    persistent_notification = hass.components.persistent_notification
    client = wideq.Client.from_token(refresh_token, country, language)

    dishwashers = []
    dryers = []

    # Note: These devices are only connected when in use, otherwise
    # the 'wideq.NotConnectedError' is thrown. We ignore that here.
    for device_id in hass.data[KEY_SMARTTHINQ_DEVICES]:
        device = client.get_device(device_id)
        if device.type == wideq.DeviceType.DISHWASHER:
            try:
                dishwashers.append(LGDishwasherDevice(client, max_retries, device))
            except wideq.NotConnectedError:
                pass
        if device.type == wideq.DeviceType.DRYER:
            try:
                dryers.append(LGDryerDevice(client, max_retries, device))
            except wideq.NotConnectedError:
                pass

    # Add the devices
    if dishwashers:
        for device in dishwashers:
            LOGGER.debug("Found LG Dishwasher: %s" % device.name)
        add_devices(dishwashers, True)

    if dryers:
        for device in dishwashers:
            LOGGER.debug("Found LG Dryer: %s" % device.name)
        add_devices(dryers, True)
