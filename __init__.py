"""
Support for LG Smartthinq devices.
"""
import logging
import voluptuous as vol

from homeassistant.const import CONF_REGION, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery

"""General variables"""
REQUIREMENTS = ['wideq']
DOMAIN = 'smartthinq'
CONF_LANGUAGE = 'language'
CONF_MAX_RETRIES = 'max_retries'
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_TOKEN): cv.string,
        CONF_REGION: cv.string,
        CONF_LANGUAGE: cv.string,
        CONF_MAX_RETRIES: cv.positive_int,
        })
}, extra=vol.ALLOW_EXTRA)
LOGGER = logging.getLogger(__name__)

KEY_SMARTTHINQ_DEVICES = 'smartthinq_devices'
README_URL = 'https://github.com/sampsyo/hass-smartthinq/blob/master/README.md'

KEY_DEPRECATED_REFRESH_TOKEN = 'refresh_token'
KEY_DEPRECATED_COUNTRY = 'country'
KEY_DEPRECATED_LANGUAGE = 'language'

DEPRECATION_WARNING = (
    'Direct use of the smartthinq components without a toplevel '
    'smartthinq platform configuration is deprecated. Please use '
    'a top-level smartthinq platform instead. Please see {readme_url} . '
    'Configuration mapping:\n '
    '\tclimate.{key_deprecated_token} -> {domain}.{key_token}\n'
    '\tclimate.{key_deprecated_country} -> {domain}.{key_region}\n'
    '\tclimate.{key_deprecated_language} -> {domain}.{key_language}').format(
        readme_url=README_URL,
        key_deprecated_token=KEY_DEPRECATED_REFRESH_TOKEN,
        key_token=CONF_TOKEN,
        key_deprecated_country=KEY_DEPRECATED_COUNTRY,
        key_region=CONF_REGION,
        key_deprecated_language=KEY_DEPRECATED_LANGUAGE,
        key_language=CONF_LANGUAGE,
        domain=DOMAIN)

"""Device specific imports"""
from .LGDevices.LGDishwasherDevice import LGDishwasherDevice

def setup(hass, config):
    if DOMAIN not in config:
        LOGGER.warning(DEPRECATION_WARNING)
        return True

    import wideq

    refresh_token = config[DOMAIN].get(CONF_TOKEN)
    region = config[DOMAIN].get(CONF_REGION)
    language = config[DOMAIN].get(CONF_LANGUAGE)
    client = wideq.Client.from_token(refresh_token, region, language)

    if KEY_SMARTTHINQ_DEVICES not in hass.data:
        hass.data[KEY_SMARTTHINQ_DEVICES] = []

    for device in client.devices:
        hass.data[KEY_SMARTTHINQ_DEVICES].append(device.id)

    """Add the devices"""
    max_retries = config[DOMAIN].get(CONF_MAX_RETRIES)
    if max_retries is None:
        max_retries = 5

    hass.data[CONF_TOKEN] = refresh_token
    hass.data[CONF_REGION] = region
    hass.data[CONF_LANGUAGE] = language
    hass.data[CONF_MAX_RETRIES] = max_retries
    add_devices(_wideq_devices(hass, client), True)

    return True

def _wideq_devices(hass, client):
    """Generate all the LG devices associated with the user's account.

    Log errors for devices that can't be used for whatever reason.
    """

    import wideq

    # Get specific variables needed for device discovery below
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
        if device.type == wideq.DeviceType.DISHWASHER:
            try:
                d = LGDishwasherDevice(client, device, max_retries)
            except wideq.NotConnectedError:
                # Dishwashers are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass
            else:
                yield d
