import logging
import voluptuous as vol
import json
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.util.temperature import convert as convert_temperature
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, TEMP_CELSIUS, CONF_TOKEN, CONF_ENTITY_ID)
import time
import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_REF_DEVICES = 'lge_REF_devices'

CONF_REFRIGERATOR_TEMPERATURE = 'refrigerator_temperature'
CONF_FREEZER_TEMPERATURE = 'freezer_temperature'
CONF_ICEPLUS_MODE = 'iceplus_mode'
CONF_FRESHAIRFILTER_MODE = 'freshairfilter_mode'

ATTR_REFRIGERATOR_TEMPERATURE = 'refrigerator_temperature'
ATTR_FREEZER_TEMPERATURE = 'freezer_temperature'
ATTR_ICEPLUS_STATE = 'iceplus_state'
ATTR_ICEPLUS_LIST = 'iceplus_list'
ATTR_FRESHAIRFILTER_STATE = 'freshairfilter_state'
ATTR_FRESHAIRFILTER_LIST = 'freshairfilter_list'
ATTR_SMARTSAVING_MODE = 'smartsaving_mode'
ATTR_WATERFILTER_STATE = 'waterfilter_state'
ATTR_DOOR_STATE = 'door_state'
ATTR_SMARTSAVING_STATE = 'smartsaving_state'
ATTR_LOCKING_STATE = 'locking_state'
ATTR_ACTIVESAVING_STATE = 'activesaving_state'

SERVICE_SET_REFRIGERATOR_TEMPERATURE = 'lge_ref_set_refrigerator_temperature'
SERVICE_SET_FREEZER_TEMPERATURE = 'lge_ref_set_freezer_temperature'
SERVICE_SET_ICEPLUS_MODE = 'lge_ref_set_iceplus_mode'
SERVICE_SET_FRESHAIRFILTER_MODE = 'lge_ref_set_freshairfilter_mode'

ICEPLUSMODES = {
    'ON': wideq.STATE_ICE_PLUS,
    'OFF': wideq.STATE_ICE_PLUS_OFF,
}

FRESHAIRFILTERMODES = {
    'POWER' : wideq.STATE_FRESH_AIR_FILTER_POWER,
    'AUTO' : wideq.STATE_FRESH_AIR_FILTER_AUTO,
    'OFF' : wideq.STATE_FRESH_AIR_FILTER_OFF,
}

SMARTSAVINGMODES = {
    'NIGHT' : wideq.STATE_SMART_SAVING_NIGHT,
    'CUSTOM' : wideq.STATE_SMART_SAVING_CUSTOM,
    'OFF' : wideq.STATE_SMART_SAVING_OFF,
}

LGE_REF_SET_REFRIGERATOR_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_REFRIGERATOR_TEMPERATURE): cv.string,
})

LGE_REF_SET_FREEZER_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_FREEZER_TEMPERATURE): cv.string,
})

LGE_REF_SET_ICEPLUS_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_ICEPLUS_MODE): cv.string,
})

LGE_REF_SET_FRESHAIRFILTER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_FRESHAIRFILTER_MODE): cv.string,
})

MAX_RETRIES = 5

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)

    """Set up the LGE Refrigerator components."""

    LOGGER.debug("Creating new LGE Refrigerator")

    if LGE_REF_DEVICES not in hass.data:
        hass.data[LGE_REF_DEVICES] = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)

        if device.type == wideq.DeviceType.REFRIGERATOR:
            ref_entity = LGEREFDEVICE(client, device)
            hass.data[LGE_REF_DEVICES].append(ref_entity)
    add_entities(hass.data[LGE_REF_DEVICES])

    LOGGER.debug("LGE Refrigerator is added")
    
    def service_handle(service):
        """Handle the Refrigerator services."""
        entity_id = service.data.get(CONF_ENTITY_ID)
        refrigerator_temperature = service.data.get(CONF_REFRIGERATOR_TEMPERATURE)
        freezer_temperature = service.data.get(CONF_FREEZER_TEMPERATURE)
        iceplus_mode = service.data.get(CONF_ICEPLUS_MODE)
        freshairfilter_mode = service.data.get(CONF_FRESHAIRFILTER_MODE)
    
        if service.service == SERVICE_SET_REFRIGERATOR_TEMPERATURE:
            ref_entity.set_ref_temperature(refrigerator_temperature)
        elif service.service == SERVICE_SET_FREEZER_TEMPERATURE:
            ref_entity.set_freezer_temperature(freezer_temperature)
        elif service.service == SERVICE_SET_ICEPLUS_MODE:
            ref_entity.set_iceplus_mode(iceplus_mode)
        elif service.service == SERVICE_SET_FRESHAIRFILTER_MODE:
            ref_entity.set_fresh_air_filter_mode(freshairfilter_mode)
        
    hass.services.register(
        DOMAIN, SERVICE_SET_REFRIGERATOR_TEMPERATURE, service_handle,
        schema=LGE_REF_SET_REFRIGERATOR_TEMPERATURE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_FREEZER_TEMPERATURE, service_handle,
        schema=LGE_REF_SET_FREEZER_TEMPERATURE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_ICEPLUS_MODE, service_handle,
        schema=LGE_REF_SET_ICEPLUS_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_FRESHAIRFILTER_MODE, service_handle,
        schema=LGE_REF_SET_FRESHAIRFILTER_MODE_SCHEMA)

class LGEREFDEVICE(LGEDevice):
    def __init__(self, client, device):
        
        """initialize a LGE Refrigerator Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._ref = wideq.RefDevice(client, device)

        self._ref.monitor_start()
        self._ref.monitor_start()
        self._ref.delete_permission()
        self._ref.delete_permission()

        # The response from the monitoring query.
        self._state = None
        # Store a transient temperature when we've just set it. We also
        # store the timestamp for when we set this value.
        self._transient_temp = None
        self._transient_time = None

        self.update()

    @property
    def supported_features(self):
        """ none """

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_REFRIGERATOR_TEMPERATURE] = self.current_reftemp
        data[ATTR_FREEZER_TEMPERATURE] = self.current_freezertemp
        data[ATTR_ICEPLUS_STATE] = self.ice_plus_state
        data[ATTR_ICEPLUS_LIST] = self.ice_plus_list
        data[ATTR_FRESHAIRFILTER_STATE] = self.fresh_air_filter_state
        data[ATTR_FRESHAIRFILTER_LIST] = self.fresh_air_filter_list
        data[ATTR_SMARTSAVING_MODE] = self.smart_saving_mode
        data[ATTR_SMARTSAVING_STATE] = self.smart_saving_state
        data[ATTR_WATERFILTER_STATE] = self.water_filter_state
        data[ATTR_DOOR_STATE] = self.door_state
        data[ATTR_SMARTSAVING_STATE] = self.smart_saving_state
        data[ATTR_LOCKING_STATE] = self.locking_state
        data[ATTR_ACTIVESAVING_STATE] = self.active_saving_state
        return data

    @property
    def current_reftemp(self):
        if self._state:
            return self._state.current_reftemp

    def set_ref_temperature(self, refrigerator_temperature):
        self._ref.set_reftemp(refrigerator_temperature)

    @property
    def current_freezertemp(self):
        if self._state:
            return self._state.current_freezertemp

    def set_freezer_temperature(self, freezer_temperature):
        self._ref.set_freezertemp(freezer_temperature)

    @property
    def ice_plus_list(self):
        return list(ICEPLUSMODES.values())

    @property
    def ice_plus_state(self):
        if self._state:
            mode = self._state.iceplus_state
            return ICEPLUSMODES[mode.name]

    def set_iceplus_mode(self, iceplus_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in ICEPLUSMODES.items()}

        mode = wideq.ICEPLUS[modes_inv[iceplus_mode]]
        self._ref.set_iceplus(mode)

    @property
    def fresh_air_filter_list(self):
        return list(FRESHAIRFILTERMODES.values())

    @property
    def fresh_air_filter_state(self):
        if self._state:
            mode = self._state.freshairfilter_state
            return FRESHAIRFILTERMODES[mode.name]

    def set_fresh_air_filter_mode(self, freshairfilter_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in FRESHAIRFILTERMODES.items()}

        mode = wideq.FRESHAIRFILTER[modes_inv[freshairfilter_mode]]
        self._ref.set_freshairfilter(mode)

    @property
    def smart_saving_mode(self):
        if self._state:
            data = self._state.smartsaving_mode
            if data == "@RE_SMARTSAVING_MODE_NIGHT_W":
                return 'NIGHT'
            elif data == "@RE_SMARTSAVING_MODE_CUSTOM_W":
                return 'CUSTOM'
            elif data == "@CP_TERM_USE_NOT_W":
                return 'OFF'

    @property
    def water_filter_state(self):
        if self._state:
            data = self._state.waterfilter_state
            if data == '255':
                return 'NO FILTER'
            else:
                return data
    @property
    def door_state(self):
        if self._state:
            return self._state.door_state

    @property
    def smart_saving_state(self):
        if self._state:
            return self._state.smartsaving_state

    @property
    def locking_state(self):
        if self._state:
            return self._state.locking_state

    @property
    def active_saving_state(self):
        if self._state:
            return self._state.activesaving_state

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ref.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ref.monitor_start()
                self._ref.monitor_start()
                self._ref.delete_permission()
                self._ref.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ref.monitor_start()
                self._ref.monitor_start()
                self._ref.delete_permission()
                self._ref.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ref.monitor_start()
        self._ref.monitor_start()
        self._ref.delete_permission()
        self._ref.delete_permission()
