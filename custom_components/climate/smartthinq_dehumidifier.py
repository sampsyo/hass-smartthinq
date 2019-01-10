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
    ATTR_ENTITY_ID, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID)
import time
import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_DEHUMIDIFIER_DEVICES = 'lge_dehumidifier_devices'

CONF_AIRREMOVAL_MODE = 'airremoval_mode'

SUPPORT_TARGET_HUMIDITY = 8
SUPPORT_TARGET_HUMIDITY_HIGH = 16
SUPPORT_TARGET_HUMIDITY_LOW = 32
SUPPORT_FAN_MODE = 64
SUPPORT_OPERATION_MODE = 128
SUPPORT_ON_OFF = 4096

ATTR_CURRENT_HUMIDITY = 'current_humidity'
ATTR_HUMIDITY = 'humidity'
ATTR_MAX_HUMIDITY = 'max_humidity'
ATTR_MIN_HUMIDITY = 'min_humidity'
ATTR_TARGET_HUMIDITY_STEP = 'humidity_step'
ATTR_SENSORPM1 = 'PM1'
ATTR_SENSORPM2 = 'PM2'
ATTR_SENSORPM10 = 'PM10'
ATTR_TOTALAIRPOLUTION = 'total_air_polution'
ATTR_AIRPOLUTION = 'air_polution'
ATTR_OPERATION_MODE = 'operation_mode'
ATTR_OPERATION_LIST = 'operation_list'
ATTR_FAN_MODE = 'fan_mode'
ATTR_FAN_LIST = 'fan_list'
ATTR_STATUS = 'current_status'
ATTR_AIRREMOVAL_MODE = 'airremoval_mode'

SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE = 'lge_dehumidifier_set_airremoval_mode'

MODES = {
    'SMART_DEHUM': wideq.STATE_DEHUM_OPMODE_SMART_DEHUM,
    'FAST_DEHUM': wideq.STATE_DEHUM_OPMODE_FAST_DEHUM,
    'SILENT_DEHUM': wideq.STATE_DEHUM_OPMODE_SILENT_DEHUM,
    'CONCENTRATION_DRY': wideq.STATE_DEHUM_OPMODE_CONCENTRATION_DRY,
    'CLOTHING_DRY': wideq.STATE_DEHUM_OPMODE_CLOTHING_DRY,
    'IONIZER' : wideq.STATE_DEHUM_OPMODE_IONIZER,
}

FANMODES = {
    'LOW' : wideq.STATE_DEHUM_WINDSTRENGTH_LOW,
    'HIGH' : wideq.STATE_DEHUM_WIDESTRENGTH_HIGH,
}

SWINGMODES = {
    'LEFT_RIGHT': wideq.STATE_LEFT_RIGHT,
    'RIGHTSIDE_LEFT_RIGHT': wideq.STATE_RIGHTSIDE_LEFT_RIGHT,
    'LEFTSIDE_LEFT_RIGHT': wideq.STATE_LEFTSIDE_LEFT_RIGHT,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,

}

AIRREMOVALMODES = {
    'ON': wideq.STATE_DEHUM_AIRREMOVAL_ON,
    'OFF': wideq.STATE_DEHUM_AIRREMOVAL_OFF,
}

LGE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRREMOVAL_MODE): cv.string,
})

MAX_RETRIES = 5
TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
HUM_MIN = 30
HUM_MAX = 70
HUM_STEP = 5

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)
    name = config[CONF_NAME]

    """Set up the LGE DEHUMIDIFIER components."""

    LOGGER.debug("Creating new LGE DEHUMIDIFIER")

    if LGE_DEHUMIDIFIER_DEVICES not in hass.data:
        hass.data[LGE_DEHUMIDIFIER_DEVICES] = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)

        if device.type == wideq.DeviceType.DEHUMIDIFIER:
            hvac_entity = LGEDEHUMDEVICE(client, device, name)
            hass.data[LGE_DEHUMIDIFIER_DEVICES].append(hvac_entity)
    add_entities(hass.data[LGE_DEHUMIDIFIER_DEVICES])

    LOGGER.debug("LGE DEHUMIDIFIER is added")

    def service_handle(service):
        """Handle the DEHUMIDIFIER services."""
        entity_id = service.data.get(CONF_ENTITY_ID)
        airremoval_mode = service.data.get(CONF_AIRREMOVAL_MODE)
        
        if service.service == SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE:
            hvac_entity.airremoval_mode(airremoval_mode)
              
    # Register hvac service(s)
    hass.services.register(
        DOMAIN, SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE, service_handle,
        schema=LGE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE_SCHEMA)

class LGEDEHUMDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name):
        """initialize a LGE HAVC Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._dehum = wideq.DehumDevice(client, device)

        self._dehum.monitor_start()
        self._dehum.monitor_start()
        self._dehum.delete_permission()
        self._dehum.delete_permission()

        # The response from the monitoring query.
        self._state = None

        self._transient_hum = None
        self._transient_time = None
        self._name = name

        self.update()

    @property
    def name(self):
    	return self._name


    @property
    def supported_features(self):
        return (
            SUPPORT_TARGET_HUMIDITY |
            SUPPORT_TARGET_HUMIDITY_HIGH |
            SUPPORT_TARGET_HUMIDITY_LOW |
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {}
        data[ATTR_AIRREMOVAL_MODE] = self.is_airremoval_mode
        data[ATTR_SENSORPM1] = self._state.sensorpm1
        data[ATTR_SENSORPM2] = self._state.sensorpm2
        data[ATTR_SENSORPM10] = self._state.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self._state.total_air_polution
        data[ATTR_AIRPOLUTION] = self._state.air_polution
        data[ATTR_STATUS] = self.current_status

        if self.target_humidity_step is not None:
            data[ATTR_TARGET_HUMIDITY_STEP] = self.target_humidity_step
            
        supported_features = self.supported_features
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        if supported_features & SUPPORT_TARGET_HUMIDITY:
            data[ATTR_HUMIDITY] = self.target_humidity
            data[ATTR_CURRENT_HUMIDITY] = self.current_humidity

        if supported_features & SUPPORT_TARGET_HUMIDITY_LOW:
            data[ATTR_MIN_HUMIDITY] = self.min_humidity

        if supported_features & SUPPORT_TARGET_HUMIDITY_HIGH:
            data[ATTR_MAX_HUMIDITY] = self.max_humidity

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
        self._dehum.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._dehum.set_on(False)
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

        mode = wideq.DEHUMOPMode[modes_inv[operation_mode]]
        self._dehum.set_mode(mode)

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

        mode = wideq.DEHUMWindStrength[fanmodes_inv[fan_mode]]
        self._dehum.set_windstrength(mode)

    @property
    def is_airremoval_mode(self):
        if self._state:
            mode = self._state.airremoval_state
            return AIRREMOVALMODES[mode.name]
    
    def airremoval_mode(self, airremoval_mode):
        if airremoval_mode == '켜짐':
            self._dehum.set_airremoval(True)
        elif airremoval_mode == '꺼짐':
            self._dehum.set_airremoval(False)

    @property
    def min_humidity(self):
        return HUM_MIN

    @property
    def max_humidity(self):
        return HUM_MAX
        
    @property
    def target_humidity_step(self):
        return HUM_STEP

    @property
    def current_humidity(self):
        if self._state:
            return self._state.current_humidity

    @property
    def target_humidity(self):
        if self._state:
            return self._state.target_humidity
                               
    def set_humidity(self, humidity):

        LOGGER.info('Setting humidity to %s...', humidity)
        self._dehum.set_humidity(humidity)

        LOGGER.info('humidity set.')

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._dehum.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._dehum.monitor_start()
                self._dehum.monitor_start()
                self._dehum.delete_permission()
                self._dehum.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._dehum.monitor_start()
                self._dehum.monitor_start()
                self._dehum.delete_permission()
                self._dehum.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._dehum.monitor_start()
        self._dehum.monitor_start()
        self._dehum.delete_permission()
        self._dehum.delete_permission()
