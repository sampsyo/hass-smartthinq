import logging
import threading
import voluptuous as vol
import json
from homeassistant.components import climate
from homeassistant.components.climate import (
	ClimateDevice)
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID,)
import time
import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_AIRPURIFIER_DEVICES = 'lge_AirPurifier_devices'

SUPPORT_FAN_MODE = 64
SUPPORT_OPERATION_MODE = 128
SUPPORT_SWING_MODE = 512
SUPPORT_ON_OFF = 4096

CONF_CIRCULATEDIR_MODE = 'circulatedir_mode'
CONF_AIRREMOVAL_MODE = 'airremoval_mode'
CONF_SIGNALLIGHTING_MODE = 'signallighting_mode'

CONF_MAC = 'mac'

ATTR_SENSORPM1 = 'pm1'
ATTR_SENSORPM2 = 'pm2'
ATTR_SENSORPM10 = 'pm10'
ATTR_TOTALAIRPOLUTION = 'total_air_polution'
ATTR_AIRPOLUTION = 'air_polution'
ATTR_FILTER_STATE = 'filter_state'
ATTR_OPERATION_MODE = 'operation_mode'
ATTR_OPERATION_LIST = 'operation_list'
ATTR_FAN_MODE = 'fan_mode'
ATTR_FAN_LIST = 'fan_list'
ATTR_SWING_MODE = 'swing_mode'
ATTR_SWING_LIST = 'swing_list'
ATTR_STATUS = 'current_status'
ATTR_AIRREMOVAL_MODE = 'airremoval_mode'
ATTR_SIGNALLIGHTING_MODE = 'signallighting_mode'
ATTR_CIRCULATEDIR_MODE = 'circulatedir_mode'
ATTR_DEVICE_TYPE = 'device_type'

SERVICE_SET_AIRREMOVAL_MODE = 'lge_airpurifier_set_airremoval_mode'
SERVICE_SET_SIGNALLIGHTING_MODE = 'lge_airpurifier_set_signallighting_mode'
SERVICE_SET_CIRCULATEDIR_MODE = 'lge_airpurifier_set_circulatedir_mode'

MODES = {
    'CLEANBOOSTER': wideq.STATE_AIRPURIFIER_CIRCULATOR_CLEAN,
    'SINGLECLEAN': wideq.STATE_AIRPURIFIER_BABY_CARE,
    'DUALCLEAN': wideq.STATE_AIRPURIFIER_DUAL_CLEAN,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO_MODE,
}

FANMODES = {
    'LOW': wideq.STATE_AIRPURIFIER_LOW,
    'MID': wideq.STATE_AIRPURIFIER_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_HIGH,
    'POWER': wideq.STATE_AIRPURIFIER_POWER,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO,
}

CIRCULATEMODES = {
    'LOW': wideq.STATE_AIRPURIFIER_CIR_LOW,
    'MID': wideq.STATE_AIRPURIFIER_CIR_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_CIR_HIGH,
    'POWER': wideq.STATE_AIRPURIFIER_CIR_POWER,
    'AUTO': wideq.STATE_AIRPURIFIER_CIR_AUTO,
}

APETCMODES = {
    'ON': wideq.STATE_AIRPURIFIER_ON,
    'OFF': wideq.STATE_AIRPURIFIER_OFF,
}

APTOTALAIRPOLUTION = {
    'GOOD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_GOOD,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'BAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_BAD,
    'VERYBAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_VERYBAD
}

APSMELL = {
    'WEEK': wideq.STATE_AIRPURIFIER_SMELL_WEEK,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'STRONG': wideq.STATE_AIRPURIFIER_SMELL_STRONG,
    'VERYSTRONG': wideq.STATE_AIRPURIFIER_SMELL_VERYSTRONG
}

LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRREMOVAL_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_CIRCULATEDIR_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_CIRCULATEDIR_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_SIGNALLIGHTING_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SIGNALLIGHTING_MODE): cv.string,
})

MAX_RETRIES = 5

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)

    """Set up the LGE AirPurifier components."""

    LOGGER.debug("Creating new LGE AirPurifier")

    LGE_AIRPURIFIER_DEVICES = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)
        model = client.model_info(device)
        if device.type == wideq.DeviceType.AIR_PURIFIER:
            name = config[CONF_NAME]
            mac = device.macaddress
            conf_mac = config[CONF_MAC]
            model_type = model.model_type
            if mac == conf_mac.lower():
                ap_entity = LGEAPDEVICE(client, device, name, model_type)
                LGE_AIRPURIFIER_DEVICES.append(ap_entity)
            else:
                LOGGER.error("MAC Address is not matched")
                
    add_entities(LGE_AIRPURIFIER_DEVICES)

    LOGGER.debug("LGE AirPurifier is added")

    def service_handle(service):
        """Handle the AirPurifier services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        airremoval_mode = service.data.get(CONF_AIRREMOVAL_MODE)
        circulatedir_mode = service.data.get(CONF_CIRCULATEDIR_MODE)
        signallighting_mode = service.data.get(CONF_SIGNALLIGHTING_MODE)

        if service.service == SERVICE_SET_AIRREMOVAL_MODE:
            ap_entity.airremoval_mode(airremoval_mode)
        elif service.service == SERVICE_SET_CIRCULATEDIR_MODE:
            ap_entity.circulatedir_mode(circulatedir_mode)
        elif service.service == SERVICE_SET_SIGNALLIGHTING_MODE:
            ap_entity.signallighting_mode(signallighting_mode)

    # Register air purifier service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRREMOVAL_MODE, service_handle,
        schema=LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_CIRCULATEDIR_MODE, service_handle,
        schema=LGE_AIRPURIFIER_SET_CIRCULATEDIR_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_SIGNALLIGHTING_MODE, service_handle,
        schema=LGE_AIRPURIFIER_SET_SIGNALLIGHTING_MODE_SCHEMA) 

class LGEAPDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name, model_type, celsius=True):
        """initialize a LGE Air Purifier Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._ap = wideq.APDevice(client, device)

        self._ap.monitor_start()
        self._ap.monitor_start()
        self._ap.delete_permission()
        self._ap.delete_permission()

        # The response from the monitoring query.
        self._state = None
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
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_SWING_MODE |
            SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        supported_features = self.supported_features
        data = {}
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_STATUS] = self.current_status
        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list
        if supported_features & SUPPORT_SWING_MODE:
            data[ATTR_SWING_MODE] = self.current_circulate_mode
            if self.circulate_list:
                data[ATTR_SWING_LIST] = self.circulate_list            
        data[ATTR_AIRREMOVAL_MODE] = self.is_airremoval_mode
        data[ATTR_CIRCULATEDIR_MODE] = self.is_circulatedir_mode
        data[ATTR_SIGNALLIGHTING_MODE] = self.is_signallighting_mode
        data[ATTR_SENSORPM1] = self.sensorpm1
        data[ATTR_SENSORPM2] = self.sensorpm2
        data[ATTR_SENSORPM10] = self.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self.total_air_polution
        data[ATTR_AIRPOLUTION] = self.air_polution
        data[ATTR_FILTER_STATE] = self.filter_state

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
        self._ap.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._ap.set_on(False)
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
        mode = wideq.APOPMode[modes_inv[operation_mode]]
        self._ap.set_mode(mode)

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
        mode = wideq.APWindStrength[fanmodes_inv[fan_mode]]
        self._ap.set_windstrength(mode)

    @property
    def circulate_list(self):
        return list(CIRCULATEMODES.values())

    @property
    def current_circulate_mode(self):
        if self._state:
            mode = self._state.circulatestrength_state
            return CIRCULATEMODES[mode.name]

    def set_swing_mode(self, circulate_mode):

        import wideq
        circulatemodes_inv = {v: k for k, v in CIRCULATEMODES.items()}
        mode = wideq.APCirculateStrength[circulatemodes_inv[circulate_mode]]
        self._ap.set_circulatestrength(mode)

    @property
    def is_airremoval_mode(self):
        if self._state:
            mode = self._state.airremoval_state
            return APETCMODES[mode.name]
    
    def airremoval_mode(self, airremoval_mode):
        if airremoval_mode == '켜짐':
            self._ap.set_airremoval(True)
        elif airremoval_mode == '꺼짐':
            self._ap.set_airremoval(False)

    @property
    def is_circulatedir_mode(self):
        if self._state:
            mode = self._state.circulatedir_state
            return APETCMODES[mode.name]
    
    def circulatedir_mode(self, circulatedir_mode):
        if circulatedir_mode == '켜짐':
            self._ap.set_circulatedir(True)
        elif circulatedir_mode == '꺼짐':
            self._ap.set_circulatedir(False)

    @property
    def is_signallighting_mode(self):
        if self._state:
            mode = self._state.signallighting_state
            return APETCMODES[mode.name]
    
    def signallighting_mode(self, signallighting_mode):
        if signallighting_mode == '켜짐':
            self._ap.set_signallighting(True)
        elif signallighting_mode == '꺼짐':
            self._ap.set_signallighting(False)

    @property
    def filter_state(self):
        data = self._ap.get_filter_state()
        usetime = data['UseTime']
        changeperiod = data['ChangePeriod']
        use = int(usetime)/int(changeperiod)
        remain = (1 - use)*100

        if changeperiod == '0':
            return 'No Filter'
        else:
            return int(remain)

    @property
    def sensorpm1(self):
        if self._state:
            return self._state.sensorpm1

    @property
    def sensorpm2(self):
        if self._state:
            return self._state.sensorpm2


    @property
    def sensorpm10(self):
        if self._state:
            return self._state.sensorpm10

    @property
    def air_polution(self):
        if self._state:
            mode = self._state.air_polution
            return APSMELL[mode.name]
            
    @property
    def total_air_polution(self):
        if self._state:
            mode = self._state.total_air_polution
            return APTOTALAIRPOLUTION[mode.name]

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ap.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ap.monitor_start()
                self._ap.monitor_start()
                self._ap.delete_permission()
                self._ap.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ap.monitor_start()
                self._ap.monitor_start()
                self._ap.delete_permission()
                self._ap.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ap.monitor_start()
        self._ap.monitor_start()
        self._ap.delete_permission()
        self._ap.delete_permission()
