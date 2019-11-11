import logging
import voluptuous as vol
from homeassistant.components import climate
from homeassistant.const import CONF_REGION, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time
from homeassistant.components.climate import const as c_const
from custom_components.smartthinq import (
    CONF_LANGUAGE, DEPRECATION_WARNING, KEY_DEPRECATED_COUNTRY,
    KEY_DEPRECATED_LANGUAGE, KEY_DEPRECATED_REFRESH_TOKEN)

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required(KEY_DEPRECATED_REFRESH_TOKEN): cv.string,
    KEY_DEPRECATED_COUNTRY: cv.string,
    KEY_DEPRECATED_LANGUAGE: cv.string,
})

MODES = {
    'HEAT': c_const.HVAC_MODE_HEAT,
    'COOL': c_const.HVAC_MODE_COOL,
    'FAN': c_const.HVAC_MODE_FAN_ONLY,
    'DRY': c_const.HVAC_MODE_DRY,
    'ACO': c_const.HVAC_MODE_HEAT_COOL,
}

# add for diffrent lg ac device in same ha
FAN_MODES_BY_DEVICE_NAME = {}
FAN_MODES_BY_DEVICE_NAME['DEFAULT'] = {
    'LOW': c_const.FAN_LOW,
    'LOW_MID': 'low-mid',
    'MID': c_const.FAN_MEDIUM,
    'MID_HIGH': 'mid-high',
    'HIGH': c_const.FAN_HIGH,
	'AUTO': 'AUTO',
	'NATURE': 'NATURE',	
}
FAN_MODES_BY_DEVICE_NAME['PAC_910604_WW'] = {
    'R_LOW' : 'R[L]',
    'R_MID' : 'R[M]',
    'R_HIGH' : 'R[H]',
    'L_LOW' : 'L[L]',
    'L_MID' : 'L[M]',
    'L_HIGH' : 'L[H]',
    'L_LOWR_LOW' : 'L[L]-R[L]',
    'L_LOWR_MID' : 'L[L]-R[M]',
    'L_LOWR_HIGH' : 'L[L]-R[H]',
    'L_MIDR_LOW' : 'L[M]-R[L]',
    'L_MIDR_MID' : 'L[M]-R[M]',
    'L_MIDR_HIGH' : 'L[M]-R[H]',
    'L_HIGHR_LOW' : 'L[H]-R[L]',
    'L_HIGHR_MID' : 'L[H]-R[M]',
    'L_HIGHR_HIGH' : 'L[H]-R[H]',
    'AUTO_2' : 'AUTO',
    'POWER_2' : 'POWER',
    'LONGPOWER' : 'LONG-POWER',    
}

FAN_MODES_BY_DEVICE_NAME['RAC_056905_WW'] = {
    'LOW': c_const.FAN_LOW,
    'MID': c_const.FAN_MEDIUM,
    'HIGH': c_const.FAN_HIGH,
    'NATURE': 'NATURE',	
}

MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_F = 60  # Guessed from actual behavior: API reports are unreliable.
TEMP_MAX_F = 89
TEMP_MIN_C = 18  # Intervals read from the AC's remote control.
TEMP_MAX_C = 30


def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    if any(key in config for key in (
        (KEY_DEPRECATED_REFRESH_TOKEN,
         KEY_DEPRECATED_COUNTRY,
         KEY_DEPRECATED_LANGUAGE))):
        LOGGER.warning(DEPRECATION_WARNING)

    refresh_token = config.get(KEY_DEPRECATED_REFRESH_TOKEN) or \
        hass.data.get(CONF_TOKEN)
    country = config.get(KEY_DEPRECATED_COUNTRY) or \
        hass.data.get(CONF_REGION)
    language = config.get(KEY_DEPRECATED_LANGUAGE) or \
        hass.data.get(CONF_LANGUAGE)

    fahrenheit = hass.config.units.temperature_unit != '°C'

    client = wideq.Client.from_token(refresh_token, country, language)
    add_devices(_ac_devices(hass, client, fahrenheit), True)


def _ac_devices(hass, client, fahrenheit):
    """Generate all the AC (climate) devices associated with the user's
    LG account.

    Log errors for devices that can't be used for whatever reason.
    """
    import wideq

    persistent_notification = hass.components.persistent_notification

    for device in client.devices:
        if device.type == wideq.DeviceType.AC:
            try:
                d = LGDevice(client, device, fahrenheit)
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


class LGDevice(climate.ClimateDevice):
    def __init__(self, client, device, fahrenheit=True):
        self._client = client
        self._device = device
        self._fahrenheit = fahrenheit

        import wideq
        self._ac = wideq.ACDevice(client, device)
        self._ac.monitor_start()

        # The response from the monitoring query.
        self._state = None

        # Store a transient temperature when we've just set it. We also
        # store the timestamp for when we set this value.
        self._transient_temp = None
        self._transient_time = None

    @property
    def temperature_unit(self):
        if self._fahrenheit:
            return const.TEMP_FAHRENHEIT
        else:
            return const.TEMP_CELSIUS

    @property
    def name(self):
        return self._device.name

    @property
    def available(self):
        return True

    @property
    def supported_features(self):
        return (
            c_const.SUPPORT_TARGET_TEMPERATURE |
            c_const.SUPPORT_FAN_MODE
        )

    @property
    def min_temp(self):
        if self._fahrenheit:
            return TEMP_MIN_F
        else:
            return TEMP_MIN_C

    @property
    def max_temp(self):
        if self._fahrenheit:
            return TEMP_MAX_F
        else:
            return TEMP_MAX_C

    @property
    def current_temperature(self):
        if self._state:
            if self._fahrenheit:
                return self._state.temp_cur_f
            else:
                return self._state.temp_cur_c

    @property
    def target_temperature(self):
        # Use the recently-set target temperature if it was set recently
        # (within TRANSIENT_EXP seconds ago).
        if self._transient_temp:
            interval = time.time() - self._transient_time
            if interval < TRANSIENT_EXP:
                return self._transient_temp
            else:
                self._transient_temp = None

        # Otherwise, actually use the device's state.
        if self._state:
            if self._fahrenheit:
                return self._state.temp_cfg_f
            else:
                return self._state.temp_cfg_c

    @property
    def hvac_modes(self):
        return list(MODES.values()) + [c_const.HVAC_MODE_OFF]

    @property
    def fan_modes(self):
        # if model id is exists
        # then return model's fan mode
        # else return default fan mode
        if self._device.model_id in FAN_MODES_BY_DEVICE_NAME:
            return list(FAN_MODES_BY_DEVICE_NAME[self._device.model_id].values())
        return list(FAN_MODES_BY_DEVICE_NAME['DEFAULT'].values())
    
    @property
    def hvac_mode(self):
        if self._state:
            if not self._state.is_on:
                return c_const.HVAC_MODE_OFF
            mode = self._state.mode
            return MODES[mode.name]

    @property
    def fan_mode(self):
        if self._device.model_id in FAN_MODES_BY_DEVICE_NAME:
            return FAN_MODES_BY_DEVICE_NAME[self._device.model_id][mode.name]
        return FAN_MODES_BY_DEVICE_NAME['DEFAULT'][mode.name]

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == c_const.HVAC_MODE_OFF:
            self._ac.set_on(False)
            return

        # Some AC units must be powered on before setting the mode.
        if not self._state.is_on:
            self._ac.set_on(True)

        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        mode = wideq.ACMode[modes_inv[hvac_mode]]
        LOGGER.info('Setting mode to %s...', mode)
        self._ac.set_mode(mode)
        LOGGER.info('Mode set.')

    def set_fan_mode(self, fan_mode):
        import wideq
        fan_modes_inv = None
        if self._device.model_id in FAN_MODES_BY_DEVICE_NAME:
            fan_modes_inv = {v: k for k, v in FAN_MODES_BY_DEVICE_NAME[self._device.model_id].items()}
        else:
            fan_modes_inv = {v: k for k, v in FAN_MODES_BY_DEVICE_NAME['DEFAULT'].items()}

        mode = wideq.ACFanSpeed[fan_modes_inv[fan_mode]]
        LOGGER.info('Setting fan mode to %s', fan_mode)
        self._ac.set_fan_speed(mode)
        LOGGER.info('Fan mode set.')

    def set_temperature(self, **kwargs):
        temperature = kwargs['temperature']
        self._transient_temp = temperature
        self._transient_time = time.time()

        LOGGER.info('Setting temperature to %s...', temperature)
        if self._fahrenheit:
            self._ac.set_fahrenheit(temperature)
        else:
            self._ac.set_celsius(temperature)
        LOGGER.info('Temperature set.')

    def update(self):
        """Poll for updated device status.

        Set the `_state` field to a new data mapping.
        """

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ac.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ac.monitor_start()
                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)  # Exponential backoff.

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')
        self._ac.monitor_start()
