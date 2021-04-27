import logging
import voluptuous as vol
from homeassistant.components import climate
from homeassistant.const import CONF_REGION, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time
from homeassistant.components.climate import const as c_const
from custom_components.smartthinq import (
    CONF_LANGUAGE, KEY_DEPRECATED_COUNTRY,
    KEY_DEPRECATED_LANGUAGE, KEY_DEPRECATED_REFRESH_TOKEN,
    CONF_WIDEQ_STATE)

try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice \
         as ClimateEntity

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required(KEY_DEPRECATED_REFRESH_TOKEN): cv.string,
    KEY_DEPRECATED_COUNTRY: cv.string,
    KEY_DEPRECATED_LANGUAGE: cv.string,
})

MODES = {
    'AI': c_const.HVAC_MODE_AUTO,
    'ENERGY_SAVER': c_const.HVAC_MODE_AUTO,
    'HEAT': c_const.HVAC_MODE_HEAT,
    'COOL': c_const.HVAC_MODE_COOL,
    'FAN': c_const.HVAC_MODE_FAN_ONLY,
    'DRY': c_const.HVAC_MODE_DRY,
    'ACO': c_const.HVAC_MODE_HEAT_COOL,
}
FAN_MODES = {
    'LOW': c_const.FAN_LOW,
    'LOW_MID': 'low-mid',
    'MID': c_const.FAN_MEDIUM,
    'MID_HIGH': 'mid-high',
    'HIGH': c_const.FAN_HIGH,

    'NATURE': 'nature',
    'POWER': 'power',
}

def swing_modes_index():
    from wideq import ACHSwingMode, ACVSwingMode
            # name: [horz_key, vert_key]
    return {'Off': [ACHSwingMode.OFF, ACVSwingMode.OFF],
            'Vertical': [ACHSwingMode.OFF, ACVSwingMode.ALL] ,
            'Horizontal': [ACHSwingMode.ALL, ACVSwingMode.OFF],
            'Vertical and Horizontal': [ACHSwingMode.ALL, ACVSwingMode.ALL] ,
            'Up Left': [ACHSwingMode.FIVE, ACVSwingMode.ONE] ,
            'Up Right': [ACHSwingMode.ONE, ACVSwingMode.ONE] ,
            'Up': [ACHSwingMode.ALL, ACVSwingMode.ONE]}
SWING_MODE_DEFAULT = "Unknown"


MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_F = 60  # Guessed from actual behavior: API reports are unreliable.
TEMP_MAX_F = 89
TEMP_MIN_C = 18  # Intervals read from the AC's remote control.
TEMP_MAX_C = 30


def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    client = wideq.Client.load(hass.data[CONF_WIDEQ_STATE])
    client.refresh()
    fahrenheit = hass.config.units.temperature_unit != '°C'
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


class LGDevice(ClimateEntity):
    def __init__(self, client, device, fahrenheit=True):
        self._client = client
        self._device = device
        self._fahrenheit = fahrenheit
        self._attrs = {}
        self._has_power = "maybe"

        import wideq
        self._ac = wideq.ACDevice(client, device)
        self._ac.monitor_start()

        # The response from the monitoring query.
        self._state = None

        # Store a transient temperature when we've just set it. We also
        # store the timestamp for when we set this value.
        self._transient_temp = None
        self._transient_time = None
        
        self._swing_mode = SWING_MODE_DEFAULT

    @property
    def device_state_attributes(self):
        return self._attrs

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
            c_const.SUPPORT_FAN_MODE |
            c_const.SUPPORT_SWING_MODE
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
        import wideq
        return [v for k, v in MODES.items()
                if wideq.ACMode[k].value in
                self._ac.model.value('airState.opMode').options.values()] \
            + [c_const.HVAC_MODE_OFF]

    @property
    def fan_modes(self):
        import wideq
        return [v for k, v in FAN_MODES.items()
                if wideq.ACFanSpeed[k].value in
                self._ac.model.value('airState.windStrength').options.values()]

    @property
    def swing_mode(self):
        # try to find out if the (initial) state matches a known state actually
        if self._swing_mode == SWING_MODE_DEFAULT:
            for k, v in swing_modes_index().items():
                if v[0] == self._state.horz_swing and v[1] == self._state.vert_swing:
                    self._swing_mode = k
                    break
            else:
                return SWING_MODE_DEFAULT
        
        return self._swing_mode

    def set_swing_mode(self, swing_mode):
        self._swing_mode = swing_mode
        LOGGER.info('Setting swing mode to %s...', self._swing_mode)
        
        horiz_mode = swing_modes_index()[self._swing_mode][0]
        vert_mode = swing_modes_index()[self._swing_mode][1]
        
        LOGGER.info('Setting device horizontal swing mode to %s...', horiz_mode)
        self._ac.set_horz_swing(horiz_mode)
        LOGGER.info('Mode set.')
        
        LOGGER.info('Setting device vertical swing mode to %s...', vert_mode)
        self._ac.set_vert_swing(vert_mode)
        LOGGER.info('Mode set.')

    @property
    def swing_modes(self):
        return [k for k, v in swing_modes_index().items()]

    @property
    def hvac_mode(self):
        if self._state:
            if not self._state.is_on:
                return c_const.HVAC_MODE_OFF
            mode = self._state.mode
            return MODES[mode.name]

    @property
    def fan_mode(self):
        if self._state:
            mode = self._state.fan_speed
            return FAN_MODES[mode.name]

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

        # Invert the fan modes mapping.
        fan_modes_inv = {v: k for k, v in FAN_MODES.items()}

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

    def check_power(self):
        """Poll for power consumption. If it fails once,
            assume it's not supported, and don't try again"""
        import wideq

        if not self._has_power:
            return

        try:
            power = self._ac.get_power()
            if power:
                self._attrs['power'] = power
                self._has_power = True
        except wideq.InvalidRequestError:
            LOGGER.info('Power consumption not available.')
            self._has_power = False

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
            except wideq.NotConnectedError:
                LOGGER.info('Device not available.')
                return

            self.check_power()

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
