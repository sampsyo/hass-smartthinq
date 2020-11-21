"""
Support for LG Smartthinq devices.
"""
import logging
import os
import json
import wideq

import voluptuous as vol

from homeassistant.const import CONF_REGION, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

DOMAIN = 'smartthinq'

CONF_LANGUAGE = 'language'
CONF_WIDEQ_STATE='wideq_state'
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_WIDEQ_STATE): cv.string
        })
}, extra=vol.ALLOW_EXTRA)


LOGGER = logging.getLogger(__name__)

SMARTTHINQ_COMPONENTS = [
    'sensor',
    'climate',
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

    LOGGER.error("Starting up")

    if KEY_SMARTTHINQ_DEVICES not in hass.data:
        hass.data[KEY_SMARTTHINQ_DEVICES] = []

    state_file = config[DOMAIN].get(CONF_WIDEQ_STATE)

    # Load the configuration from the state file
    try:
        with open(state_file) as f:
            LOGGER.debug("State file found '%s'", os.path.abspath(state_file))
            state = json.load(f)
    except IOError:
        state = {}
        LOGGER.debug("No state file found (tried: '%s')",
                     os.path.abspath(state_file))

    client = wideq.Client.load(state)
    hass.data[CONF_WIDEQ_STATE] = state

    while True:
        try:
            for device in client.devices:
                hass.data[KEY_SMARTTHINQ_DEVICES].append(device.id)

            for component in SMARTTHINQ_COMPONENTS:
                discovery.load_platform(hass, component, DOMAIN, {}, config)
            return True
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired.')
            client.refresh()


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
