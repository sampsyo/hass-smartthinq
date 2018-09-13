import logging
import voluptuous as vol
import json
from homeassistant.components import climate
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, CONF_TOKEN)
import time
import wideq

REQUIREMENTS = ['wideq']

ATTR_CURRENT_TEMPERATURE = 'current_temperature'
ATTR_MAX_TEMP = 'max_temp'
ATTR_MIN_TEMP = 'min_temp'
ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_HUMIDITY = 'humidity'
ATTR_SENSORPM1 = 'PM1'
ATTR_SENSORPM2 = 'PM2'
ATTR_SENSORPM10 = 'PM10'
ATTR_TOTALAIRPOLUTION = 'total_air_polution'
ATTR_FILTER_STATE = 'filter_state'
ATTR_MFILTER_STATE = 'mfilter_state'
ATTR_AIRPOLUTION = 'air_polution'
ATTR_OPERATION_MODE = 'operation_mode'
ATTR_OPERATION_LIST = 'operation_list'
ATTR_FAN_MODE = 'fan_mode'
ATTR_FAN_LIST = 'fan_list'
ATTR_SWING_MODE = 'swing_mode'
ATTR_SWING_LIST = 'swing_list'
ATTR_STATUS = 'current_status'

CONVERTIBLE_ATTRIBUTE = [
    ATTR_TEMPERATURE
]

LOGGER = logging.getLogger(__name__)

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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_TOKEN): cv.string,
})

MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_C = 18
TEMP_MAX_C = 26

def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    refresh_token = config.get(CONF_TOKEN)
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
    def supported_features(self):
        return (
            climate.SUPPORT_TARGET_TEMPERATURE |
            climate.SUPPORT_OPERATION_MODE |
            climate.SUPPORT_FAN_MODE |
            climate.SUPPORT_SWING_MODE |
            climate.SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {
            ATTR_CURRENT_TEMPERATURE: show_temp(
                self.hass, self.current_temperature, self.temperature_unit,
                self.precision),
            ATTR_MIN_TEMP: show_temp(
                self.hass, self.min_temp, self.temperature_unit,
                self.precision),
            ATTR_MAX_TEMP: show_temp(
                self.hass, self.max_temp, self.temperature_unit,
                self.precision),
            ATTR_TEMPERATURE: show_temp(
                self.hass, self.target_temperature, self.temperature_unit,
                self.precision),
        }
        data[ATTR_TARGET_TEMPERATURE] = self.target_temperature
        data[ATTR_HUMIDITY] = self._state.humidity
        data[ATTR_SENSORPM1] = self._state.sensorpm1
        data[ATTR_SENSORPM2] = self._state.sensorpm2
        data[ATTR_SENSORPM10] = self._state.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self._state.total_air_polution
        data[ATTR_AIRPOLUTION] = self._state.air_polution        
        data[ATTR_STATUS] = self.current_status
        data[ATTR_FILTER_STATE] = self.filter_state
        data[ATTR_MFILTER_STATE] = self.mfilter_state

        supported_features = self.supported_features
        if supported_features & climate.SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        if supported_features & climate.SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        if supported_features & climate.SUPPORT_SWING_MODE:
            data[ATTR_SWING_MODE] = self.current_swing_mode
            if self.swing_list:
                data[ATTR_SWING_LIST] = self.swing_list

        return data

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
    def current_status(self):
        if self._state.is_on == True:
            return 'ON'
        elif self._state.is_on == False:
            return 'OFF'

    @property
    def filter_state(self):
        data = self._ac.get_filter_state()
        usetime = data['UseTime']
        changeperiod = data['ChangePeriod']
        use = int(usetime)/int(changeperiod)
        remain = (1 - use)*100

        if changeperiod == '0':
            return 'No Filter'
        else:
            return int(remain)

    @property
    def mfilter_state(self):
        data = self._ac.get_mfilter_state()

        remaintime = data['RemainTime']
        changeperiod = data['ChangePeriod']
        remain = int(remaintime)/int(changeperiod)

        if changeperiod == '0':
            return 'No mFilter'    
        else:
            return int(remain * 100)



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
