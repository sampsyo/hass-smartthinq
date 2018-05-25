import logging
import voluptuous as vol
from homeassistant.components import climate
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time
import wideq

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required('refresh_token'): cv.string,
})

MODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,
    'POWER_SAVE' : wideq.STATE_POWER_SAVE,
    'AIRCLEAN': wideq.STATE_AIRCLEAN,
    'AIRCLEAN_OFF': wideq.STATE_AIRCLEAN_OFF,
    'SMARTCARE': wideq.STATE_SMARTCARE,
    'SMARTCARE_OFF': wideq.STATE_SMARTCARE_OFF,
    'AUTODRY': wideq.STATE_AUTODRY,
    'AUTODRY_OFF': wideq.STATE_AUTODRY_OFF,
}

FANMODES = {
    'LOW' : wideq.STATE_LOW,
    'MID' : wideq.STATE_MID,
    'HIGH' : wideq.STATE_HIGH,
    'COOLPOWER' : wideq.STATE_COOLPOWER,
    'LONGPOWER' : wideq.STATE_LONGPOWER,
    'RIGHT_ONLY_LOW': wideq.STATE_RIGHT_ONLY_LOW,
    'RIGHT_ONLY_MID': wideq.STATE_RIGHT_ONLY_MID,
    'RIGHT_ONLY_HIGH': wideq.STATE_RIGHT_ONLY_HIGH,
    'LEFT_ONLY_LOW': wideq.STATE_LEFT_ONLY_LOW,
    'LEFT_ONLY_MID': wideq.STATE_LEFT_ONLY_MID,
    'LEFT_ONLY_HIGH': wideq.STATE_LEFT_ONLY_HIGH,
    'RIGHT_LOW_LEFT_MID': wideq.STATE_RIGHT_LOW_LEFT_MID,
    'RIGHT_LOW_LEFT_HIGH': wideq.STATE_RIGHT_LOW_LEFT_HIGH,
    'RIGHT_MID_LEFT_LOW': wideq.STATE_RIGHT_MID_LEFT_LOW,
    'RIGHT_MID_LEFT_HIGH': wideq.STATE_RIGHT_MID_LEFT_HIGH,
    'RIGHT_HIGH_LEFT_LOW': wideq.STATE_RIGHT_HIGH_LEFT_LOW,
    'RIGHT_HIGH_LEFT_MID': wideq.STATE_RIGHT_HIGH_LEFT_MID,

}

SWINGMODES = {
    'UP_DOWN': wideq.STATE_UP_DOWN,
    'UP_DOWN_STOP' : wideq.STATE_UP_DOWN_STOP,
    'LEFT_RIGHT': wideq.STATE_LEFT_RIGHT,
    'RIGHTSIDE_LEFT_RIGHT': wideq.STATE_RIGHTSIDE_LEFT_RIGHT,
    'LEFTSIDE_LEFT_RIGHT': wideq.STATE_LEFTSIDE_LEFT_RIGHT,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,

}


MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_C = 18
TEMP_MAX_C = 26

def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    refresh_token = config.get('refresh_token')
    client = wideq.Client.from_token(refresh_token)

    add_devices(
        LGDevice(client, device)
        for device in client.devices
        if device.type == wideq.DeviceType.AC
    )


class LGDevice(climate.ClimateDevice):
    def __init__(self, client, device, celsius=True):
        self._client = client
        self._device = device
        self._celsius = celsius

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
        if self._celsius:
            return const.TEMP_CELSIUS
        else:
            return const.TEMP_FAHRENHEIT

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
            climate.SUPPORT_OPERATION_MODE |
            climate.SUPPORT_FAN_MODE |
            climate.SUPPORT_SWING_MODE |
            climate.SUPPORT_ON_OFF
        )

    @property
    def min_temp(self):
        if self._celsius:
            return TEMP_MIN_C
        return climate.ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        if self._celsius:
            return TEMP_MAX_C
        return climate.ClimateDevice.max_temp.fget(self)
    
    @property
    def current_temperature(self):
        if self._state:
            if self._celsius:
                return self._state.temp_cur_c

    @property
    def current_humidity(self):
        import wideq
        if self._state:
            return self._state.sensor_humidity(self)
    """
    @property
    def device_state_attributes(self):

        attrs = {}
        attrs['SensorHumidity'] = self.current_humidity(self)
        return attrs
    """

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
            if self._celsius:
                return self._state.temp_cfg_c
            else:
                return self._state.temp_cfg_f

    @property
    def operation_list(self):
        return list(MODES.values())
   
    @property
    def fan_list(self):
        return list(FANMODES.values())

    @property
    def swing_list(self):
        return list(SWINGMODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            return MODES[mode.name]

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        if operation_mode == 'SMARTCARE':
            self._ac.set_smartcare(True)
        elif operation_mode == 'SMARTCARE_OFF':
            self._ac.set_smartcare(False)
        elif operation_mode == 'POWER_SAVE':
            self._ac.set_powersave(True)
        elif operation_mode == 'AIRCLEAN_OFF':
            self._ac.set_airclean(False)
        elif operation_mode == 'AUTODRY':
            self._ac.set_autodry(True)
        elif operation_mode == 'AUTODRY_OFF':
            self._ac.set_autodry(False)
        else:
            mode = wideq.ACMode[modes_inv[operation_mode]]
            self._ac.set_mode(mode)

    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in FANMODES.items()}
        
        if fan_mode == 'COOLPOWER':
            self._ac.set_icevalley(True)
        elif fan_mode == 'LONGPOWER':
            self._ac.set_longpower(True)
        else :
            mode = wideq.ACWindstrength[fanmodes_inv[fan_mode]]
            self._ac.set_windstrength(mode)

    def set_swing_mode(self, swing_mode):
        import wideq
        swingmodes_inv = {v: k for k, v in SWINGMODES.items()}

        if swing_mode == 'UP_DOWN':
            self._ac.set_wind_updown(True)
        elif swing_mode == 'UP_DOWN_STOP':
            self._ac.set_wind_updown(False)
        else :
            mode = wideq.WDIRLEFTRIGHT[swingmodes_inv[swing_mode]]
            self._ac.set_wind_leftright(mode)


    def set_temperature(self, **kwargs):
        temperature = kwargs['temperature']
        self._transient_temp = temperature
        self._transient_time = time.time()

        LOGGER.info('Setting temperature to %s...', temperature)
        if self._celsius:
            self._ac.set_celsius(temperature)
        else:
            self._ac.set_fahrenheit(temperature)
        LOGGER.info('Temperature set.')

    def turn_on(self):
        LOGGER.info('Turning on...')
        self._ac.set_on(True)
        LOGGER.info('...done.')

    def turn_off(self):
        LOGGER.info('Turning off...')
        self._ac.set_on(False)
        LOGGER.info('...done.')

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
