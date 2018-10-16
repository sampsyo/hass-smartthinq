import logging
import threading
import voluptuous as vol
import json
from homeassistant.components import climate
from homeassistant.components.climate import (
	ClimateDevice)
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, TEMP_CELSIUS, CONF_TOKEN, CONF_ENTITY_ID)
import time
import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_HVAC_DEVICES = 'lge_HVAC_devices'

SUPPORT_TARGET_TEMPERATURE = 1
SUPPORT_AIRCLEAN_MODE = 32
SUPPORT_FAN_MODE = 64
SUPPORT_OPERATION_MODE = 128
SUPPORT_SWING_MODE = 512
SUPPORT_ON_OFF = 4096

CONF_AIRCLEAN_MODE = 'airclean_mode'
CONF_COOLPOWER_MODE = 'coolpower_mode'
CONF_AUTODRY_MODE = 'autodry_mode'
CONF_SMARTCARE_MODE = 'smartcare_mode'
CONF_POWERSAVE_MODE = 'powersave_mode'
CONF_LONGPOWER_MODE = 'longpower_mode'
CONF_WDIRUPDOWN_MODE = 'up_down_mode'


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
ATTR_AIRCLEAN_MODE = 'airclean_mode'
ATTR_COOLPOWER_MODE = 'coolpower_mode'
ATTR_AUTODRY_MODE = 'autodry_mode'
ATTR_SMARTCARE_MODE = 'smartcare_mode'
ATTR_POWERSAVE_MODE = 'powersave_mode'
ATTR_LONGPOWER_MODE = 'longpower_mode'
ATTR_UP_DOWN_MODE = 'up_down_mode'

CONVERTIBLE_ATTRIBUTE = [
    ATTR_TEMPERATURE
]

SERVICE_SET_AIRCLEAN_MODE = 'lge_hvac_set_airclean_mode'
SERVICE_SET_COOLPOWER_MODE = 'lge_hvac_set_coolpower_mode'
SERVICE_SET_AUTODRY_MODE = 'lge_hvac_set_autodry_mode'
SERVICE_SET_SMARTCARE_MODE = 'lge_hvac_set_smartcare_mode'
SERVICE_SET_POWERSAVE_MODE = 'lge_hvac_set_powersave_mode'
SERVICE_SET_LONGPOWER_MODE = 'lge_hvac_set_longpower_mode'
SERVICE_SET_WDIRUPDOWN_MODE = 'lge_hvac_set_up_down_mode'

MODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,
}

FANMODES = {
    'LOW' : wideq.STATE_LOW,
    'MID' : wideq.STATE_MID,
    'HIGH' : wideq.STATE_HIGH,
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
    'LEFT_RIGHT': wideq.STATE_LEFT_RIGHT,
    'RIGHTSIDE_LEFT_RIGHT': wideq.STATE_RIGHTSIDE_LEFT_RIGHT,
    'LEFTSIDE_LEFT_RIGHT': wideq.STATE_LEFTSIDE_LEFT_RIGHT,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,

}

AIRCLEANMODES = {
    'ON': wideq.STATE_AIRCLEAN,
    'OFF': wideq.STATE_AIRCLEAN_OFF,
}

COOLPOWERMODES = {
    'ON': wideq.STATE_COOLPOWER,
    'OFF': wideq.STATE_COOLPOWER_OFF,
}

AUTODRYMODES = {
    'ON': wideq.STATE_AUTODRY,
    'OFF': wideq.STATE_AUTODRY_OFF,
}

SMARTCAREMODES = {
    'ON': wideq.STATE_SMARTCARE,
    'OFF': wideq.STATE_SMARTCARE_OFF,
}

POWERSAVEMODES = {
    'ON': wideq.STATE_POWERSAVE,
    'OFF': wideq.STATE_POWERSAVE_OFF,
}

LONGPOWERMODES = {
    'ON': wideq.STATE_LONGPOWER,
    'OFF': wideq.STATE_LONGPOWER_OFF,
}

WDIRUPDOWNMODES = {
    'ON': wideq.STATE_UP_DOWN,
    'OFF': wideq.STATE_UP_DOWN_STOP,
}

LGE_HVAC_SET_AIRCLEAN_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRCLEAN_MODE): cv.string,
})

LGE_HVAC_SET_COOLPOWER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_COOLPOWER_MODE): cv.string,
})

LGE_HVAC_SET_AUTODRY_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AUTODRY_MODE): cv.string,
})

LGE_HVAC_SET_SMARTCARE_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SMARTCARE_MODE): cv.string,
})

LGE_HVAC_SET_POWERSAVE_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_POWERSAVE_MODE): cv.string,
})

LGE_HVAC_SET_LONGPOWER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_LONGPOWER_MODE): cv.string,
})

LGE_HVAC_SET_WDIRUPDOWN_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_WDIRUPDOWN_MODE): cv.string,
})

MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_C = 18
TEMP_MAX_C = 26

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)

    """Set up the LGE HVAC components."""

    LOGGER.debug("Creating new LGE HVAC")

    if LGE_HVAC_DEVICES not in hass.data:
        hass.data[LGE_HVAC_DEVICES] = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)

        if device.type == wideq.DeviceType.AC:
            hvac_entity = LGEHVACDEVICE(client, device)
            hass.data[LGE_HVAC_DEVICES].append(hvac_entity)
    add_entities(hass.data[LGE_HVAC_DEVICES])

    LOGGER.debug("LGE HVAC is added")

    def service_handle(service):
        """Handle the HVAC services."""
        entity_id = service.data.get(CONF_ENTITY_ID)
        airclean_mode = service.data.get(CONF_AIRCLEAN_MODE)
        coolpower_mode = service.data.get(CONF_COOLPOWER_MODE)
        autodry_mode = service.data.get(CONF_AUTODRY_MODE)
        smartcare_mode = service.data.get(CONF_SMARTCARE_MODE)        
        powersave_mode = service.data.get(CONF_POWERSAVE_MODE)
        longpower_mode = service.data.get(CONF_LONGPOWER_MODE)
        up_down_mode = service.data.get(CONF_WDIRUPDOWN_MODE)
        
        if service.service == SERVICE_SET_AIRCLEAN_MODE:
            hvac_entity.airclean_mode(airclean_mode)
        elif service.service == SERVICE_SET_COOLPOWER_MODE:
            hvac_entity.coolpower_mode(coolpower_mode)
        elif service.service == SERVICE_SET_AUTODRY_MODE:
            hvac_entity.autodry_mode(autodry_mode)
        elif service.service == SERVICE_SET_SMARTCARE_MODE:
            hvac_entity.smartcare_mode(smartcare_mode)
        elif service.service == SERVICE_SET_POWERSAVE_MODE:
            hvac_entity.powersave_mode(powersave_mode)
        elif service.service == SERVICE_SET_LONGPOWER_MODE:
            hvac_entity.longpower_mode(longpower_mode)
        elif service.service == SERVICE_SET_WDIRUPDOWN_MODE:
            hvac_entity.up_down_mode(up_down_mode)    
              
    # Register hvac service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRCLEAN_MODE, service_handle,
        schema=LGE_HVAC_SET_AIRCLEAN_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_COOLPOWER_MODE, service_handle,
        schema=LGE_HVAC_SET_COOLPOWER_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_AUTODRY_MODE, service_handle,
        schema=LGE_HVAC_SET_AUTODRY_MODE_SCHEMA) 
    hass.services.register(
        DOMAIN, SERVICE_SET_SMARTCARE_MODE, service_handle,
        schema=LGE_HVAC_SET_SMARTCARE_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_POWERSAVE_MODE, service_handle,
        schema=LGE_HVAC_SET_POWERSAVE_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_LONGPOWER_MODE, service_handle,
        schema=LGE_HVAC_SET_LONGPOWER_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_WDIRUPDOWN_MODE, service_handle,
        schema=LGE_HVAC_SET_WDIRUPDOWN_MODE_SCHEMA) 

class LGEHVACDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, celsius=True):
        """initialize a LGE HAVC Device."""
        LGEDevice.__init__(self, client, device)
        self._celsius = celsius

        import wideq
        self._ac = wideq.ACDevice(client, device)

        self._ac.monitor_start()
        self._ac.monitor_start()
        self._ac.delete_permission()
        self._ac.delete_permission()

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
            SUPPORT_TARGET_TEMPERATURE |
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_SWING_MODE |
            SUPPORT_ON_OFF
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
        data[ATTR_AIRCLEAN_MODE] = self.is_airclean_mode
        data[ATTR_COOLPOWER_MODE] = self.is_coolpower_mode
        data[ATTR_AUTODRY_MODE] = self.is_autodry_mode
        data[ATTR_SMARTCARE_MODE] = self.is_smartcare_mode
        data[ATTR_POWERSAVE_MODE] = self.is_powersave_mode
        data[ATTR_LONGPOWER_MODE] = self.is_longpower_mode
        data[ATTR_UP_DOWN_MODE] = self.is_up_down_mode
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
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        if supported_features & SUPPORT_SWING_MODE:
            data[ATTR_SWING_MODE] = self.current_swing_mode
            if self.swing_list:
                data[ATTR_SWING_LIST] = self.swing_list
        return data

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def current_status(self):
        if self._state.is_on == True:
            return 'ON'
        elif self._state.is_on == False:
            return 'OFF'

    def turn_on(self):
        LOGGER.info('Turning on...')
        self._ac.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._ac.set_on(False)
        LOGGER.info('...done.') 

    @property
    def operation_list(self):
        return list(MODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            return MODES[mode.name]
            
    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        mode = wideq.ACMode[modes_inv[operation_mode]]
        self._ac.set_mode(mode)

    @property
    def fan_list(self):
        return list(FANMODES.values())

    @property
    def current_fan_mode(self):
        if self._state:
            mode = self._state.windstrength_state
            return FANMODES[mode.name]
                    
    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in FANMODES.items()}

        mode = wideq.ACWindstrength[fanmodes_inv[fan_mode]]
        self._ac.set_windstrength(mode)

    @property
    def swing_list(self):
        return list(SWINGMODES.values())

    @property
    def current_swing_mode(self):
        if self._state:
            mode = self._state.wdirleftright_state
            return SWINGMODES[mode.name]
            
    def set_swing_mode(self, swing_mode):

        import wideq

        swingmodes_inv = {v: k for k, v in SWINGMODES.items()}

        mode = wideq.WDIRLEFTRIGHT[swingmodes_inv[swing_mode]]
        self._ac.set_wind_leftright(mode)


    @property
    def is_airclean_mode(self):
        if self._state:
            mode = self._state.airclean_state
            return AIRCLEANMODES[mode.name]
    

    def airclean_mode(self, airclean_mode):
        if airclean_mode == 'ON':
            self._ac.set_airclean(True)
        elif airclean_mode == 'OFF':
            self._ac.set_airclean(False)

    @property
    def is_autodry_mode(self):
        if self._state:
            mode = self._state.autodry_state
            return AUTODRYMODES[mode.name]


    def autodry_mode(self, autodry_mode):
        if autodry_mode == 'ON':
            self._ac.set_autodry(True)
        elif autodry_mode == 'OFF':
            self._ac.set_autodry(False)

    @property
    def is_smartcare_mode(self):
        if self._state:
            mode = self._state.smartcare_state
            return SMARTCAREMODES[mode.name]

    def smartcare_mode(self, smartcare_mode):
        if smartcare_mode == 'ON':
            self._ac.set_smartcare(True)
        elif smartcare_mode == 'OFF':
            self._ac.set_smartcare(False)

    @property
    def is_powersave_mode(self):
        if self._state:
            mode = self._state.powersave_state
            return POWERSAVEMODES[mode.name]


    def powersave_mode(self, powersave_mode):
        if powersave_mode == 'ON':
            self._ac.set_powersave(True)

    @property
    def is_coolpower_mode(self):
        if self._state:
            mode = self._state.icevalley_state
            return COOLPOWERMODES[mode.name]


    def coolpower_mode(self, coolpower_mode):
        if coolpower_mode == 'ON':
            self._ac.set_icevalley(True)
        elif coolpower_mode == 'OFF':
            self._ac.set_icevalley(False)

    @property
    def is_longpower_mode(self):
        if self._state:
            mode = self._state.longpower_state
            return LONGPOWERMODES[mode.name]


    def longpower_mode(self, longpower_mode):
        if longpower_mode == 'ON':
            self._ac.set_longpower(True)
        elif longpower_mode == 'OFF':
            self._ac.set_longpower(False)

    @property
    def is_up_down_mode(self):
        if self._state:
            mode = self._state.wdirupdown_state
            return WDIRUPDOWNMODES[mode.name]

    def up_down_mode(self, up_down_mode):
        if up_down_mode == 'ON':
            self._ac.set_wind_updown(True)
        elif up_down_mode == 'OFF':
            self._ac.set_wind_updown(False)

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
    def temperature_unit(self):
        if self._celsius:
            return const.TEMP_CELSIUS
        else:
            return const.TEMP_FAHRENHEIT

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

    def update(self):

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
                self._ac.monitor_start()
                self._ac.delete_permission()
                self._ac.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ac.monitor_start()
                self._ac.monitor_start()
                self._ac.delete_permission()
                self._ac.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ac.monitor_start()
        self._ac.monitor_start()
        self._ac.delete_permission()
        self._ac.delete_permission()
