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
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, TEMP_CELSIUS, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID,)
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
CONF_SENSORMON_MODE = 'sensormon_mode'
CONF_JET_MODE = 'jet_mode'
CONF_WDIRVSTEP_MODE = 'wdirvstep_mode'

CONF_MAC = 'mac'

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
ATTR_SENSORMON_MODE = 'sensormon_mode'
ATTR_JET_MODE = 'jet_mode'
ATTR_WDIRVSTEP_MODE = 'wdirvstep_mode'
ATTR_DEVICE_TYPE = 'device_type'

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
SERVICE_SET_SENSORMON_MODE = 'lge_hvac_set_sensormon_mode'
SERVICE_SET_JET_MODE = 'lge_hvac_set_jet_mode'
SERVICE_SET_WDIRVSTEP_MODE = 'lge_hvac_set_wdirvstep_mode'

MODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,
}

RAC_SACMODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,   
    'HEAT': wideq.STATE_HEAT,
    'AI': wideq.STATE_AI,
    'FAN': wideq.STATE_FAN,
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

RAC_SACFANMODES = {
    'SYSTEM_LOW': wideq.STATE_LOW,
    'SYSTEM_MID': wideq.STATE_MID,
    'SYSTEM_HIGH': wideq.STATE_HIGH,
    'SYSTEM_AUTO': wideq.STATE_AUTO,
    'SYSTEM_POWER': wideq.STATE_POWER,
}


SWINGMODES = {
    'LEFT_RIGHT': wideq.STATE_LEFT_RIGHT,
    'RIGHTSIDE_LEFT_RIGHT': wideq.STATE_RIGHTSIDE_LEFT_RIGHT,
    'LEFTSIDE_LEFT_RIGHT': wideq.STATE_LEFTSIDE_LEFT_RIGHT,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,
}

RAC_SACSWINGMODES = {
    'LEFT_RIGTH_ON': wideq.STATE_LEFT_RIGHT_ON,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,
}

WDIRVSTEP = {
    'OFF': wideq.STATE_WDIRVSTEP_OFF,
    'FIRST': wideq.STATE_WDIRVSTEP_FIRST,
    'SECOND': wideq.STATE_WDIRVSTEP_SECOND,
    'THIRD': wideq.STATE_WDIRVSTEP_THIRD,
    'FOURTH': wideq.STATE_WDIRVSTEP_FOURTH,
    'FIFTH': wideq.STATE_WDIRVSTEP_FIFTH,
    'SIXTH': wideq.STATE_WDIRVSTEP_SIXTH,
}

ACETCMODES = {
    'ON': wideq.STATE_MODE_ON,
    'OFF': wideq.STATE_MODE_OFF,
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
LGE_HVAC_SET_SENSORMON_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SENSORMON_MODE): cv.string,
})
LGE_HVAC_SET_JET_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_JET_MODE): cv.string,
})
LGE_HVAC_SET_WDIRVSTEP_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_WDIRVSTEP_MODE): cv.string,
})

MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_C = 18
TEMP_MIN_HEAT_C = 16
TEMP_MAX_C = 26
TEMP_MAX_HEAT_C = 30

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)

    """Set up the LGE HVAC components."""

    LOGGER.debug("Creating new LGE HVAC")

    LGE_HVAC_DEVICES = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)
        model = client.model_info(device)
        if device.type == wideq.DeviceType.AC:
            name = config[CONF_NAME]
            mac = device.macaddress
            conf_mac = config[CONF_MAC]
            model_type = model.model_type
            if mac == conf_mac.lower():
                hvac_entity = LGEHVACDEVICE(client, device, name, model_type)
                LGE_HVAC_DEVICES.append(hvac_entity)
            else:
                LOGGER.error("MAC Address is not matched")

    add_entities(LGE_HVAC_DEVICES)

    LOGGER.debug("LGE HVAC is added")

    def service_handle(service):
        """Handle the HVAC services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        airclean_mode = service.data.get(CONF_AIRCLEAN_MODE)
        coolpower_mode = service.data.get(CONF_COOLPOWER_MODE)
        autodry_mode = service.data.get(CONF_AUTODRY_MODE)
        smartcare_mode = service.data.get(CONF_SMARTCARE_MODE)        
        powersave_mode = service.data.get(CONF_POWERSAVE_MODE)
        longpower_mode = service.data.get(CONF_LONGPOWER_MODE)
        up_down_mode = service.data.get(CONF_WDIRUPDOWN_MODE)
        sensormon_mode = service.data.get(CONF_SENSORMON_MODE)
        jet_mode = service.data.get(CONF_JET_MODE)
        wdirvstep_mode = service.data.get(CONF_WDIRVSTEP_MODE)


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
        elif service.service == SERVICE_SET_SENSORMON_MODE:
            hvac_entity.sensormon_mode(sensormon_mode)
        elif service.service == SERVICE_SET_JET_MODE:
            hvac_entity.jet_mode(jet_mode)
        elif service.service == SERVICE_SET_WDIRVSTEP_MODE:
            hvac_entity.wdirvstep_mode(wdirvstep_mode)

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
    hass.services.register(
        DOMAIN, SERVICE_SET_SENSORMON_MODE, service_handle,
        schema=LGE_HVAC_SET_SENSORMON_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_JET_MODE, service_handle,
        schema=LGE_HVAC_SET_JET_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_WDIRVSTEP_MODE, service_handle,
        schema=LGE_HVAC_SET_WDIRVSTEP_MODE_SCHEMA)


class LGEHVACDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name, model_type, celsius=True):
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
        self._name = name
        self._type = model_type

        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type

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
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_TARGET_TEMPERATURE] = self.target_temperature
        data[ATTR_AIRCLEAN_MODE] = self.is_airclean_mode
        data[ATTR_COOLPOWER_MODE] = self.is_coolpower_mode
        data[ATTR_AUTODRY_MODE] = self.is_autodry_mode
        data[ATTR_SMARTCARE_MODE] = self.is_smartcare_mode
        data[ATTR_POWERSAVE_MODE] = self.is_powersave_mode
        data[ATTR_LONGPOWER_MODE] = self.is_longpower_mode
        data[ATTR_UP_DOWN_MODE] = self.is_up_down_mode
        data[ATTR_SENSORMON_MODE] = self.is_sensormon_mode
        data[ATTR_WDIRVSTEP_MODE] = self.is_wdirvstep_mode
        data[ATTR_HUMIDITY] = self.humidity
        data[ATTR_SENSORPM1] = self.sensorpm1
        data[ATTR_SENSORPM2] = self.sensorpm2
        data[ATTR_SENSORPM10] = self.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self.total_air_polution
        data[ATTR_AIRPOLUTION] = self.air_polution
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
        if self.is_on == True:
            return 'ON'
        elif self.is_on == False:
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
        if self.device_type == 'PAC':
            return list(MODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACMODES.values())
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACMODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            if self.device_type == 'PAC':
                return MODES[mode.name]
            if self.device_type == 'RAC':
                return RAC_SACMODES[mode.name]
            elif self.device_type == 'SAC_CST':
                return RAC_SACMODES[mode.name]
            
    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}
        rac_sacmodes_inv = {v: k for k, v in RAC_SACMODES.items()}
        
        if self.device_type == 'PAC':
            mode = wideq.ACMode[modes_inv[operation_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.ACMode[rac_sacmodes_inv[operation_mode]]
        elif self.device_type == 'SAC_CST':
            mode = wideq.ACMode[rac_sacmodes_inv[operation_mode]]
        self._ac.set_mode(mode)

    @property
    def fan_list(self):
        if self.device_type == 'PAC':
            return list(FANMODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACFANMODES.values())            
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACFANMODES.values())

    @property
    def current_fan_mode(self):
        if self._state:
            mode = self._state.windstrength_state
            if self.device_type == 'PAC':
                return FANMODES[mode.name]
            elif self.device_type == 'RAC':
                return RAC_SACFANMODES[mode.name]                
            elif self.device_type == 'SAC_CST':
                return RAC_SACFANMODES[mode.name]
                    
    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in FANMODES.items()}
        rac_sacfanmodes_inv = {v: k for k, v in RAC_SACFANMODES.items()}

        if self.device_type == 'PAC':
            mode = wideq.ACWindstrength[fanmodes_inv[fan_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.ACWindstrength[rac_sacfanmodes_inv[fan_mode]]            
        elif self.device_type == 'SAC_CST':
            mode = wideq.ACWindstrength[rac_sacfanmodes_inv[fan_mode]]
        self._ac.set_windstrength(mode)

    @property
    def swing_list(self):
        if self.device_type == 'PAC':
            return list(SWINGMODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACSWINGMODES.values())
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACSWINGMODES.values())

    @property
    def current_swing_mode(self):
        if self._state:
            mode = self._state.wdirleftright_state
            if self.device_type == 'PAC':
                return SWINGMODES[mode.name]
            elif self.device_type == 'RAC':
                return RAC_SACSWINGMODES[mode.name]     
            elif self.device_type == 'SAC_CST':
                return RAC_SACSWINGMODES[mode.name]
            
    def set_swing_mode(self, swing_mode):

        import wideq
        swingmodes_inv = {v: k for k, v in SWINGMODES.items()}
        rac_sacswingmodes_inv = {v: k for k, v in RAC_SACSWINGMODES.items()}

        if self.device_type == 'PAC':
            mode = wideq.WDIRLEFTRIGHT[swingmodes_inv[swing_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.WDIRLEFTRIGHT[rac_sacswingmodes_inv[swing_mode]]
        elif self.device_type == 'SAC_CST':
            mode = wideq.WDIRLEFTRIGHT[rac_sacswingmodes_inv[swing_mode]]
        self._ac.set_wind_leftright(mode)

    @property
    def is_wdirvstep_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                return 'Not Supported'
            elif self.device_type == 'RAC':
                try:
                    mode = self._state.wdirvstep_state
                    return WDIRVSTEP[mode.name]
                except ValueError:
                    fourvain_mode = self._state.fourvain_wdirvstep_state
                    return WDIRVSTEP[fourvain_mode.name]
            elif self.device_type == 'SAC_CST':
                try:
                    mode = self._state.wdirvstep_state
                    return WDIRVSTEP[mode.name]
                except ValueError:
                    fourvain_mode = self._state.fourvain_wdirvstep_state
                    return WDIRVSTEP[fourvain_mode.name]

    def wdirvstep_mode(self, wdirvstep_mode):

        import wideq
        wdirvstepmodes_inv = {v: k for k, v in WDIRVSTEP.items()}

        if self.device_type == 'PAC':
            return 'Not Supported'
        elif self.device_type == 'RAC':
            vstep_state = self._state.wdirvstep_state
            if int(vstep_state.value) < 10:
                mode = wideq.WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
            elif int(vstep_state.value) > 10:
                mode = wideq.FOURVAIN_WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
        elif self.device_type == 'SAC_CST':
            vstep_state = self._state.wdirvstep_state
            if int(vstep_state.value) < 10:
                mode = wideq.WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
            elif int(vstep_state.value) > 10:
                mode = wideq.FOURVAIN_WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
        self._ac.set_wdirvstep(mode)

    @property
    def is_airclean_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.airclean_state
            elif self.device_type == 'RAC':
                mode = self._state.airclean_state
            elif self.device_type == 'SAC_CST':
                mode = self._state.sac_airclean_state
            return ACETCMODES[mode.name]
    
    def airclean_mode(self, airclean_mode):
        name = 'AirClean'
        if airclean_mode == 'ON':
            if self.device_type == 'PAC':
                self._ac.set_airclean(True)
            elif self.device_type == 'RAC':
                self._ac.set_airclean(True)
            elif self.device_type == 'SAC_CST':
                self._ac.set_etc_mode(name, True)
        elif airclean_mode == 'OFF':
            if self.device_type == 'PAC':
                self._ac.set_airclean(False)
            elif self.device_type == 'RAC':
                self._ac.set_airclean(False)
            elif self.device_type == 'SAC_CST':
                self._ac.set_etc_mode(name, False)

    @property
    def is_autodry_mode(self):
        if self._state:
            mode = self._state.autodry_state
            return ACETCMODES[mode.name]


    def autodry_mode(self, autodry_mode):
        name = 'AutoDry'
        if autodry_mode == 'ON':
            self._ac.set_etc_mode(name, True)
        elif autodry_mode == 'OFF':
            self._ac.set_etc_mode(name, False)

    @property
    def is_smartcare_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.smartcare_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    def smartcare_mode(self, smartcare_mode):
        name = 'SmartCare'
        if self.device_type == 'PAC':
            if smartcare_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif smartcare_mode == 'OFF':
                self._ac.set_etc_mode(name, False)
            

    @property
    def is_powersave_mode(self):
        if self._state:
            mode = self._state.powersave_state
            return ACETCMODES[mode.name]


    def powersave_mode(self, powersave_mode):
        name = 'PowerSave'
        if powersave_mode == 'ON':
            self._ac.set_etc_mode(name, True)

    @property
    def is_coolpower_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.icevalley_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    def coolpower_mode(self, coolpower_mode):
        name = 'IceValley'
        if self.device_type == 'PAC':
            if coolpower_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif coolpower_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

    @property
    def is_longpower_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.longpower_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    def longpower_mode(self, longpower_mode):
        name = 'FlowLongPower'
        if self.device_type == 'PAC':
            if longpower_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif longpower_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

    @property
    def is_up_down_mode(self):
        if self._state:
            mode = self._state.wdirupdown_state
            return ACETCMODES[mode.name]

    def up_down_mode(self, up_down_mode):
        name = 'WDirUpDown'
        if up_down_mode == 'ON':
            self._ac.set_etc_mode(name, True)
        elif up_down_mode == 'OFF':
            self._ac.set_etc_mode(name, False)

    @property
    def is_sensormon_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.sensormon_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    def sensormon_mode(self, sensormon_mode):
        name = 'SensorMon'
        if self.device_type == 'PAC':
            if sensormon_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif sensormon_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

    @property
    def is_jet_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                return 'Not Supported'
            elif self.device_type == 'RAC':
                mode = self._state.jet_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'SAC_CST':
                mode = self._state.jet_state
                return ACETCMODES[mode.name]

    def jet_mode(self, jet_mode):
        name = 'Jet'
        if self.device_type == 'RAC':
            if jet_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif jet_mode == 'OFF':
                self._ac.set_etc_mode(name, False)
        elif self.device_type == 'SAC_CST':
            if jet_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif jet_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

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
    def humidity(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.humidity
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'
    
    @property
    def sensorpm1(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm1
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    @property
    def sensorpm2(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm2
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    @property
    def sensorpm10(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm10
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    @property
    def air_polution(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.air_polution
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'
            
    @property
    def total_air_polution(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.total_air_polution
            elif self.device_type == 'RAC':
                return 'Not Supported'
            elif self.device_type == 'SAC_CST':
                return 'Not Supported'

    @property
    def temperature_unit(self):
        if self._celsius:
            return const.TEMP_CELSIUS
        else:
            return const.TEMP_FAHRENHEIT

    @property
    def min_temp(self):
        if self._celsius:
            if self.device_type == 'PAC':
                return TEMP_MIN_C
            elif self.device_type == 'RAC':
                return TEMP_MIN_HEAT_C
            elif self.device_type == 'SAC_CST':
                return TEMP_MIN_HEAT_C
        return climate.ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        if self._celsius:
            if self.device_type == 'PAC':
                return TEMP_MAX_C
            elif self.device_type == 'RAC':
                return TEMP_MAX_HEAT_C
            elif self.device_type == 'SAC_CST':
                return TEMP_MAX_HEAT_C
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
