import logging
import voluptuous as vol
import json
from datetime import timedelta
import time

from homeassistant.components import sensor
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_TOKEN, CONF_ENTITY_ID)
from homeassistant.exceptions import PlatformNotReady


import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_WASHER_DEVICES = 'lge_washer_devices'

ATTR_CURRENT_STATUS = 'current_status'
ATTR_RUN_STATE = 'run_state'
ATTR_PRE_STATE = 'pre_state'
ATTR_REMAIN_TIME = 'remain_time'
ATTR_INITIAL_TIME = 'initial_time'
ATTR_RESERVE_TIME = 'reserve_time'
ATTR_CURRENT_COURSE = 'current_course'
ATTR_ERROR_STATE = 'error_state'
ATTR_WASH_OPTION_STATE = 'wash_option_state'
ATTR_SPIN_OPTION_STATE = 'spin_option_state'
ATTR_WATERTEMP_OPTION_STATE = 'watertemp_option_state'
ATTR_RINSECOUNT_OPTION_STATE = 'rinsecount_option_state'
ATTR_DRYLEVEL_STATE = 'drylevel_state'
ATTR_FRESHCARE_MODE = 'freshcare_mode'
ATTR_CHILDLOCK_MODE = 'childlock_mode'
ATTR_STEAM_MODE = 'steam_mode'
ATTR_TURBOSHOT_MODE = 'turboshot_mode'
ATTR_TUBCLEAN_COUNT = 'tubclean_count'
ATTR_LOAD_LEVEL = 'load_level'

RUNSTATES = {
    'OFF': wideq.STATE_WASHER_POWER_OFF,
    'INITIAL': wideq.STATE_WASHER_INITIAL,
    'PAUSE': wideq.STATE_WASHER_PAUSE,
    'ERROR_AUTO_OFF': wideq.STATE_WASHER_ERROR_AUTO_OFF,
    'RESERVE': wideq.STATE_WASHER_RESERVE,
    'DETECTING': wideq.STATE_WASHER_DETECTING,
    'ADD_DRAIN': wideq.STATE_WASHER_ADD_DRAIN,
    'DETERGENT_AMOUNT': wideq.STATE_WASHER_DETERGENT_AMOUT,
    'RUNNING': wideq.STATE_WASHER_RUNNING,
    'PREWASH': wideq.STATE_WASHER_PREWASH,
    'RINSING': wideq.STATE_WASHER_RINSING,
    'RINSE_HOLD': wideq.STATE_WASHER_RINSE_HOLD,
    'SPINNING': wideq.STATE_WASHER_SPINNING,
    'DRYING': wideq.STATE_WASHER_DRYING,
    'END': wideq.STATE_DRYER_END,
    'FRESHCARE': wideq.STATE_WASHER_FRESHCARE,
    'TCL_ALARM_NORMAL': wideq.STATE_WASHER_TCL_ALARM_NORMAL,
    'FROZEN_PREVENT_INITIAL': wideq.STATE_WASHER_FROZEN_PREVENT_INITIAL,
    'FROZEN_PREVENT_RUNNING': wideq.STATE_WASHER_FROZEN_PREVENT_RUNNING,
    'FROZEN_PREVENT_PAUSE': wideq.STATE_WASHER_FROZEN_PREVENT_PAUSE,
    'ERROR': wideq.STATE_WASHER_ERROR,
}

SOILLEVELSTATES = {
    'NO_SELECT': wideq.STATE_WASHER_TERM_NO_SELECT,
    'LIGHT': wideq.STATE_WASHER_SOILLEVEL_LIGHT,
    'NORMAL': wideq.STATE_WASHER_SOILLEVEL_NORMAL,
    'HEAVY': wideq.STATE_WASHER_SOILLEVEL_HEAVY,
    'PRE_WASH': wideq.STATE_WASHER_SOILLEVEL_PRE_WASH,
    'SOAKING': wideq.STATE_WASHER_SOILLEVEL_SOAKING,
    'OFF': wideq.STATE_WASHER_POWER_OFF,

}

WATERTEMPSTATES = {
    'NO_SELECT': wideq.STATE_WASHER_TERM_NO_SELECT,
    'COLD' : wideq.STATE_WASHER_WATERTEMP_COLD,
    'THIRTY' : wideq.STATE_WASHER_WATERTEMP_30,
    'FOURTY' : wideq.STATE_WASHER_WATERTEMP_40,
    'SIXTY': wideq.STATE_WASHER_WATERTEMP_60,
    'NINTYFIVE': wideq.STATE_WASHER_WATERTEMP_95,
    'OFF': wideq.STATE_WASHER_POWER_OFF,

}

SPINSPEEDSTATES = {
    'NO_SELECT': wideq.STATE_WASHER_TERM_NO_SELECT,
    'EXTRA_LOW' : wideq.STATE_WASHER_SPINSPEED_EXTRA_LOW,
    'LOW' : wideq.STATE_WASHER_SPINSPEED_LOW,
    'MEDIUM' : wideq.STATE_WASHER_SPINSPEED_MEDIUM,
    'HIGH': wideq.STATE_WASHER_SPINSPEED_HIGH,
    'EXTRA_HIGH': wideq.STATE_WASHER_SPINSPEED_EXTRA_HIGH,
    'OFF': wideq.STATE_WASHER_POWER_OFF,
}

RINSECOUNTSTATES = {
    'NO_SELECT': wideq.STATE_WASHER_TERM_NO_SELECT,
    'ONE' : wideq.STATE_WASHER_RINSECOUNT_1,
    'TWO' : wideq.STATE_WASHER_RINSECOUNT_2,
    'THREE' : wideq.STATE_WASHER_RINSECOUNT_3,
    'FOUR': wideq.STATE_WASHER_RINSECOUNT_4,
    'FIVE': wideq.STATE_WASHER_RINSECOUNT_5,
    'OFF': wideq.STATE_WASHER_POWER_OFF,
}

DRYLEVELSTATES = {
    'NO_SELECT': wideq.STATE_WASHER_TERM_NO_SELECT,
    'WIND' : wideq.STATE_WASHER_DRYLEVEL_WIND,
    'TURBO' : wideq.STATE_WASHER_DRYLEVEL_TURBO,
    'TIME_30' : wideq.STATE_WASHER_DRYLEVEL_TIME_30,
    'TIME_60': wideq.STATE_WASHER_DRYLEVEL_TIME_60,
    'TIME_90': wideq.STATE_WASHER_DRYLEVEL_TIME_90,
    'TIME_120': wideq.STATE_WASHER_DRYLEVEL_TIME_120,
    'TIME_150': wideq.STATE_WASHER_DRYLEVEL_TIME_150,
    'OFF': wideq.STATE_WASHER_POWER_OFF,
}

ERRORS = {
    'ERROR_dE2' : wideq.STATE_WASHER_ERROR_dE2,
    'ERROR_IE' : wideq.STATE_WASHER_ERROR_IE,
    'ERROR_OE' : wideq.STATE_WASHER_ERROR_OE,
    'ERROR_UE' : wideq.STATE_WASHER_ERROR_UE,
    'ERROR_FE' : wideq.STATE_WASHER_ERROR_FE,
    'ERROR_PE' : wideq.STATE_WASHER_ERROR_PE,
    'ERROR_tE' : wideq.STATE_WASHER_ERROR_tE,
    'ERROR_LE' : wideq.STATE_WASHER_ERROR_LE,
    'ERROR_CE' : wideq.STATE_WASHER_ERROR_CE,
    'ERROR_PF' : wideq.STATE_WASHER_ERROR_PF,
    'ERROR_FF' : wideq.STATE_WASHER_ERROR_FF,
    'ERROR_dCE' : wideq.STATE_WASHER_ERROR_dCE,
    'ERROR_EE' : wideq.STATE_WASHER_ERROR_EE,
    'ERROR_PS' : wideq.STATE_WASHER_ERROR_PS,
    'ERROR_dE1' : wideq.STATE_WASHER_ERROR_dE1,
    'ERROR_LOE' : wideq.STATE_WASHER_ERROR_LOE,        
    'NO_ERROR' : wideq.STATE_NO_ERROR,
    'OFF': wideq.STATE_DRYER_POWER_OFF,
}

OPTIONITEMMODES = {
    'ON': wideq.STATE_OPTIONITEM_ON,
    'OFF': wideq.STATE_OPTIONITEM_OFF,
}

MAX_RETRIES = 5

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)

    """Set up the LGE Washer components."""

    LOGGER.debug("Creating new LGE Washer")

    if LGE_WASHER_DEVICES not in hass.data:
        hass.data[LGE_WASHER_DEVICES] = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)

        if device.type == wideq.DeviceType.WASHER:
            try:
            	washer_entity = LGEWASHERDEVICE(client, device)
            except wideq.NotConnectError:
                LOGGER.info('Connection Lost. Retrying.')
                raise PlatformNotReady
            hass.data[LGE_WASHER_DEVICES].append(washer_entity)
    add_entities(hass.data[LGE_WASHER_DEVICES])

    LOGGER.debug("LGE Washer is added")
    
class LGEWASHERDEVICE(LGEDevice):
    def __init__(self, client, device):
        
        """initialize a LGE Washer Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._washer = wideq.WasherDevice(client, device)

        self._washer.monitor_start()
        self._washer.monitor_start()
        self._washer.delete_permission()
        self._washer.delete_permission()

        # The response from the monitoring query.
        self._state = None

        self.update()

    @property
    def supported_features(self):
        """ none """

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_RUN_STATE] = self.current_run_state
        data[ATTR_PRE_STATE] = self.pre_state
        data[ATTR_REMAIN_TIME] = self.remain_time
        data[ATTR_INITIAL_TIME] = self.initial_time
        data[ATTR_RESERVE_TIME] = self.reserve_time
        data[ATTR_CURRENT_COURSE] = self.current_course
        data[ATTR_ERROR_STATE] = self.error_state
        data[ATTR_WASH_OPTION_STATE] = self.wash_option_state
        data[ATTR_SPIN_OPTION_STATE] = self.spin_option_state
        data[ATTR_WATERTEMP_OPTION_STATE] = self.watertemp_option_state
        data[ATTR_RINSECOUNT_OPTION_STATE] = self.rinsecount_option_state
        data[ATTR_DRYLEVEL_STATE] = self.drylevel_state
        data[ATTR_FRESHCARE_MODE] = self.freshcare_mode
        data[ATTR_CHILDLOCK_MODE] = self.childlock_mode
        data[ATTR_STEAM_MODE] = self.steam_mode
        data[ATTR_TURBOSHOT_MODE] = self.turboshot_mode
        data[ATTR_TUBCLEAN_COUNT] = self.tubclean_count
        data[ATTR_LOAD_LEVEL] = self.load_level
        return data

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def current_run_state(self):
        if self._state:
            run = self._state.run_state
            return RUNSTATES[run.name]

    @property
    def run_list(self):
        return list(RUNSTATES.values())

    @property
    def pre_state(self):
        if self._state:
            pre = self._state.pre_state
            return RUNSTATES[pre.name]

    @property
    def remain_time(self):    
        if self._state:
            remain_hour = self._state.remaintime_hour
            remain_min = self._state.remaintime_min
            remaintime = [remain_hour, remain_min]
            if int(remain_min) < 10:
                return ":0".join(remaintime)
            else:
                return ":".join(remaintime)
            
    @property
    def initial_time(self):
        if self._state:
            initial_hour = self._state.initialtime_hour
            initial_min = self._state.initialtime_min
            initialtime = [initial_hour, initial_min]
            if int(initial_min) < 10:
                return ":0".join(initialtime)
            else:
                return ":".join(initialtime)

    @property
    def reserve_time(self):
        if self._state:
            reserve_hour = self._state.reservetime_hour
            reserve_min = self._state.reservetime_min
            reservetime = [reserve_hour, reserve_min]
            if int(reserve_min) < 10:
                return ":0".join(reservetime)
            else:
                return ":".join(reservetime)

    @property
    def current_course(self):
        if self._state:
            course = self._state.current_course
            smartcourse = self._state.current_smartcourse
            if course == '다운로드코스':
                return smartcourse
            elif course == 'OFF':
                return '꺼짐'
            else:
                return course

    @property
    def error_state(self):
        if self._state:
            error = self._state.error_state
            return ERRORS[error]


    @property
    def wash_option_state(self):
        if self._state:
            wash_option = self._state.wash_option_state
            if wash_option == 'OFF':
                return SOILLEVELSTATES['OFF']
            else:
                return SOILLEVELSTATES[wash_option.name]

    @property
    def spin_option_state(self):
        if self._state:
            spin_option = self._state.spin_option_state
            if spin_option == 'OFF':
                return SPINSPEEDSTATES['OFF']
            else:
                return SPINSPEEDSTATES[spin_option.name]

    @property
    def watertemp_option_state(self):
        if self._state:
            watertemp_option = self._state.water_temp_option_state
            if watertemp_option == 'OFF':
                return WATERTEMPSTATES['OFF']
            else:
                return WATERTEMPSTATES[watertemp_option.name]

    @property
    def rinsecount_option_state(self):
        if self._state:
            rinsecount_option = self._state.rinsecount_option_state
            if rinsecount_option == 'OFF':
                return RINSECOUNTSTATES['OFF']
            else:
                return RINSECOUNTSTATES[rinsecount_option.name]

    @property
    def drylevel_state(self):
        if self._state:
            drylevel = self._state.drylevel_option_state
            if drylevel == 'OFF':
                return DRYLEVELSTATES['OFF']
            else:
                return DRYLEVELSTATES[drylevel.name]

    @property
    def freshcare_mode(self):
        if self._state:
            mode = self._state.freshcare_state
            return OPTIONITEMMODES[mode]

    @property
    def childlock_mode(self):
        if self._state:
            mode = self._state.childlock_state
            return OPTIONITEMMODES[mode]

    @property
    def steam_mode(self):
        if self._state:
            mode = self._state.steam_state
            return OPTIONITEMMODES[mode]

    @property
    def turboshot_mode(self):
        if self._state:
            mode = self._state.turboshot_state
            return OPTIONITEMMODES[mode]

    @property
    def tubclean_count(self):
        if self._state:
            return self._state.tubclean_count
    
    @property
    def load_level(self):
        if self._state:
            load_level = self._state.load_level
            if load_level == 1:
                return '소량'
            elif load_level == 2:
                return '적음'
            elif load_level == 3:
                return '보통'
            elif load_level == 4:
                return '많음'
            else:
                return '없음'

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._washer.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._washer.monitor_start()
                self._washer.monitor_start()
                self._washer.delete_permission()
                self._washer.delete_permission()

                continue

            except wideq.NotConnectError:
                LOGGER.info('Connection Lost. Retrying.')
                self._client.refresh()
                time.sleep(60)
                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._washer.monitor_start()
                self._washer.monitor_start()
                self._washer.delete_permission()
                self._washer.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._washer.monitor_start()
        self._washer.monitor_start()
        self._washer.delete_permission()
        self._washer.delete_permission()
