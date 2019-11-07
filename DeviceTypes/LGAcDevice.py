import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
import time
from .LGDevice import LGDevice
from homeassistant.components import climate
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate import const as c_const
from wideq import ac as wideq_ac

"""Implementation specific variables"""
MODES = {
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
}

TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_F = 60  # Guessed from actual behavior: API reports are unreliable.
TEMP_MAX_F = 89
TEMP_MIN_C = 18  # Intervals read from the AC's remote control.
TEMP_MAX_C = 30

class LGAcDevice(LGDevice, ClimateDevice):
    def __init__(self, client, max_retries, device, fahrenheit):
        """Initialize an LG Climate Device."""

        super().__init__(client, max_retries, device)
        self._name = "lg_climate_" + device.id

        self._fahrenheit = fahrenheit
        self._ac = wideq_ac.ACDevice(client, device)
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
        return list(FAN_MODES.values())

    @property
    def hvac_mode(self):
        if self._state:
            if not self._state.is_on:
                return c_const.HVAC_MODE_OFF
            mode = self._state.mode
            return MODES[mode.name]

    @property
    def fan_mode(self):
        mode = self._state.fan_speed
        return FAN_MODES[mode.name]

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == c_const.HVAC_MODE_OFF:
            self._ac.set_on(False)
            return

        # Some AC units must be powered on before setting the mode.
        if not self._state.is_on:
            self._ac.set_on(True)

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        mode = wideq_ac.ACMode[modes_inv[hvac_mode]]
        LOGGER.info('Setting mode to %s...', mode)
        self._ac.set_mode(mode)
        LOGGER.info('Mode set.')

    def set_fan_mode(self, fan_mode):
        # Invert the fan modes mapping.
        fan_modes_inv = {v: k for k, v in FAN_MODES.items()}

        mode = wideq_ac.ACFanSpeed[fan_modes_inv[fan_mode]]
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

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(self._max_retries):
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
