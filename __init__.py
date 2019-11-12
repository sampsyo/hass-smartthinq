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

SMARTTHINQ_COMPONENTS = [
    'climate',
    'sensor',
]
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

def setup(hass, config):
    if DOMAIN not in config:
        LOGGER.warning(DEPRECATION_WARNING)
        return True

    if KEY_SMARTTHINQ_DEVICES not in hass.data:
        hass.data[KEY_SMARTTHINQ_DEVICES] = []

    refresh_token = config[DOMAIN].get(CONF_TOKEN)
    region = config[DOMAIN].get(CONF_REGION)
    language = config[DOMAIN].get(CONF_LANGUAGE)
    max_retries = config[DOMAIN].get(CONF_MAX_RETRIES)
    if max_retries is None:
        max_retries = 5

    import wideq
    client = wideq.Client.from_token(refresh_token, region, language)

    hass.data[CONF_TOKEN] = refresh_token
    hass.data[CONF_REGION] = region
    hass.data[CONF_LANGUAGE] = language
    hass.data[CONF_MAX_RETRIES] = max_retries

    for device in client.devices:
        hass.data[KEY_SMARTTHINQ_DEVICES].append(device.id)

    for component in SMARTTHINQ_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)
    return True
