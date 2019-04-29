import logging
import threading
import voluptuous as vol
import json
from homeassistant.components import fan
from homeassistant.components.fan import (
	FanEntity)
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID,)
import time
import wideq

LGE_AIRPURIFIER_DEVICES = 'lge_AirPurifier_devices'

CONF_MAC = 'mac'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_MAC): cv.string,
})

# For Air Purifier
#-----------------------------------------------------------

SUPPORT_SET_SPEED = 1

CONF_AIRFAST_MODE = 'airfast_mode'
CONF_AIRREMOVAL_MODE = 'airremoval_mode'

ATTR_SPEED_OFF = '꺼짐'
ATTR_AIRREMOVAL_MODE = 'airremoval_mode'
ATTR_AIRFAST_MODE = 'airfast_mode'
ATTR_SPEED = 'speed'
ATTR_SPEED_LIST = 'speed_list'
ATTR_DEVICE_TYPE = 'device_type'
ATTR_STATUS = 'current_status'
ATTR_SENSORPM1 = 'PM1'
ATTR_SENSORPM2 = 'PM2'
ATTR_SENSORPM10 = 'PM10'
ATTR_TOTALAIRPOLUTION = 'total_air_polution'
ATTR_FILTER_STATE = 'filter_state'
ATTR_AIRPOLUTION = 'air_polution'

SERVICE_SET_AIRREMOVAL_MODE = 'lge_airpurifier_set_airremoval_mode'
SERVICE_SET_AIRFAST_MODE = 'lge_airpurifier_set_airfast_mode'

APSINGLECLEAN_FANMODES_LIST = {
    'LOWST_LOW': wideq.STATE_AIRPURIFIER_LOWST_LOW,
    'LOWST': wideq.STATE_AIRPURIFIER_LOWST,
    'LOW': wideq.STATE_AIRPURIFIER_LOW,
    'LOW_MID': wideq.STATE_AIRPURIFIER_LOW_MID,
    'MID': wideq.STATE_AIRPURIFIER_MID,
    'MID_HIGH': wideq.STATE_AIRPURIFIER_MID_HIGH,
    'HIGH': wideq.STATE_AIRPURIFIER_HIGH,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO,
}

APSINGLECLEAN_FANMODES = {
    'LOW': wideq.STATE_AIRPURIFIER_LOW,
    'MID': wideq.STATE_AIRPURIFIER_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_HIGH,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO,
}

APETCMODES = {
    'NOT_SUPPORTED': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'ON': wideq.STATE_AIRPURIFIER_ON,
    'OFF': wideq.STATE_AIRPURIFIER_OFF,
}

APTOTALAIRPOLUTION = {
    'NOT_SUPPORT': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'GOOD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_GOOD,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'BAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_BAD,
    'VERYBAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_VERYBAD
}

APSMELL = {
    'NOT_SUPPORT': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'WEEK': wideq.STATE_AIRPURIFIER_SMELL_WEEK,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'STRONG': wideq.STATE_AIRPURIFIER_SMELL_STRONG,
    'VERYSTRONG': wideq.STATE_AIRPURIFIER_SMELL_VERYSTRONG
}

LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRREMOVAL_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_AIRFAST_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRFAST_MODE): cv.string,
})
MAX_RETRIES = 5
LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)
    name = config[CONF_NAME]
    conf_mac = config[CONF_MAC]

    """Set up the LGE entity."""
    for device_id in hass.data[LGE_DEVICES]:
        device = client.get_device(device_id)
        model = client.model_info(device)
        mac = device.macaddress
        model_type = model.model_type
        if device.type == wideq.DeviceType.AIR_PURIFIER:
            LGE_AIRPURIFIER_DEVICES = []
            if mac == conf_mac.lower():
                ap_entity = LGEAPDEVICE(client, device, name, model_type)
                LGE_AIRPURIFIER_DEVICES.append(ap_entity)
                add_entities(LGE_AIRPURIFIER_DEVICES)
                LOGGER.debug("LGE AirPurifier is added")
            
    def airpurifier_service_handle(service):
        """Handle the AirPurifier services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        airremoval_mode = service.data.get(CONF_AIRREMOVAL_MODE)
        airfast_mode = service.data.get(CONF_AIRFAST_MODE)

        if service.service == SERVICE_SET_AIRREMOVAL_MODE:
            ap_entity.airremoval_mode(airremoval_mode)
        elif service.service == SERVICE_SET_AIRFAST_MODE:
            ap_entity.airfast_mode(airfast_mode)

    # Register air purifier service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRREMOVAL_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRFAST_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_AIRFAST_MODE_SCHEMA) 

# Air Purifier Main
class LGEAPDEVICE(LGEDevice, FanEntity):

    def __init__(self, client, device, name, model_type):
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
        self._type = model_type
        self._name = name

        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type

    @property
    def supported_features(self):
        return SUPPORT_SET_SPEED

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        supported_features = self.supported_features
        data = {}
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_STATUS] = self.current_status
        if supported_features & SUPPORT_SET_SPEED:
            data[ATTR_SPEED] = self.speed
            if self.speed_list:
                data[ATTR_SPEED_LIST] = self.speed_list 
        data[ATTR_AIRREMOVAL_MODE] = self.is_airremoval_mode
        data[ATTR_AIRFAST_MODE] = self.is_airfast_mode
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
            return '켜짐'
        elif self.is_on == False:
            return '꺼짐'

    def turn_on(self, speed = None, **kwargs) -> None:
        if speed is not None:
            self.set_speed(speed)
        else:
            LOGGER.info('Turning on...')
            self._ap.set_on(True)
            LOGGER.info('...done.')
        
    def turn_off(self, speed = None, **kwargs) -> None:
        LOGGER.info('Turning off...')
        self._ap.set_on(False)
        LOGGER.info('...done.') 

    @property
    def support_oplist(self):
        return self._state.support_oplist
            
    @property
    def speed_list(self):
        return list(APSINGLECLEAN_FANMODES.values())

    @property
    def speed(self) -> str:
        if self._state:
            mode = self._state.windstrength_state
            return APSINGLECLEAN_FANMODES_LIST[mode.name]


    def set_speed(self, speed_mode) -> None:
        import wideq
        # Invert the modes mapping.
        singleclean_fanmodes_inv = {v: k for k, v in APSINGLECLEAN_FANMODES.items()}
        mode = wideq.APWindStrength[singleclean_fanmodes_inv[speed_mode]]
        self._ap.set_windstrength(mode)

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
    def is_airfast_mode(self):
        if self._state:
            if 'CLEAN' in self.support_oplist:
                mode = self._state.airfast_state
            else:
                return '지원안함'
            return APETCMODES[mode.name]
    
    def airfast_mode(self, airfast_mode):
        if 'CLEAN' in self.support_oplist:
            if airfast_mode == '켜짐':
                self._ap.set_airfast(True)
            elif airfast_mode == '꺼짐':
                self._ap.set_airfast(False)
        else:
            return '지원안함'

    @property
    def filter_state(self):
        data = self._ap.get_filter_state()
        usetime = data['UseTime']
        changeperiod = data['ChangePeriod']
        if changeperiod == '0':
            return '지원안함'
        else:
            use = int(usetime)/int(changeperiod)
            remain = (1 - use)*100
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
