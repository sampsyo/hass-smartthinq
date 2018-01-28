import logging
import voluptuous as vol
from homeassistant.components import climate
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required('refresh_token'): cv.string,
})

MODES = {
    "@AC_MAIN_OPERATION_MODE_HEAT_W": climate.STATE_HEAT,
    "@AC_MAIN_OPERATION_MODE_COOL_W": climate.STATE_COOL,
    "@AC_MAIN_OPERATION_MODE_DRY_W": climate.STATE_DRY,
    "@AC_MAIN_OPERATION_MODE_FAN_W": climate.STATE_FAN_ONLY,
    "@AC_MAIN_OPERATION_MODE_ENERGY_SAVING_W": climate.STATE_ECO,
}
MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_F = 60  # Guessed from actual behavior: API reports are unreliable.
TEMP_MAX_F = 89


def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    refresh_token = config.get('refresh_token')
    client = wideq.Client.from_token(refresh_token)

    add_devices(LGDevice(client, device) for device in client.devices)


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

        self.update()

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
            climate.SUPPORT_TARGET_TEMPERATURE |
            climate.SUPPORT_OPERATION_MODE
        )

    @property
    def min_temp(self):
        if self._fahrenheit:
            return TEMP_MIN_F
        return climate.ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        if self._fahrenheit:
            return TEMP_MAX_F
        return climate.ClimateDevice.max_temp.fget(self)

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
    def operation_list(self):
        options = self._ac.model.value('OpMode').options
        return [
            v for k, v in MODES.items()
            if k in options
        ]

    @property
    def current_operation(self):
        options = self._ac.model.value('OpMode').options

        if self._state:
            mode = self._state.data['OpMode']
            mode_desc = options[mode]
            return MODES[mode_desc]

    def set_operation_mode(self, operation_mode):
        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        # Invert the OpMode mapping.
        options = self._ac.model.value('OpMode').options
        options_inv = {v: k for k, v in options.items()}

        mode = options_inv[modes_inv[operation_mode]]

        LOGGER.info('Setting mode to %s...', mode)
        self._client.session.set_device_controls(
            self._device.id,
            {'OpMode': mode},
        )
        LOGGER.info('Mode set.')

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
        for _ in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ac.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ac.monitor_start()

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                return

            LOGGER.info('No status available yet.')
            time.sleep(1)

        # We tried several times but got no result.
        LOGGER.warn('Status update failed.')
