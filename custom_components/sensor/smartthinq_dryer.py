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
    ATTR_ENTITY_ID, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID)

import wideq

REQUIREMENTS = ['wideq']
DEPENDENCIES = ['smartthinq']

LGE_DRYER_DEVICES = 'lge_dryer_devices'

CONF_MAC = 'mac'

ATTR_RUN_STATE = 'run_state'
ATTR_RUN_LIST = 'run_list'
ATTR_REMAIN_TIME = 'remain_time'
ATTR_INITIAL_TIME = 'initial_time'
ATTR_CURRENT_COURSE = 'current_course'
ATTR_COURSE_LIST = 'course_list'
ATTR_ERROR_STATE = 'error_state'
ATTR_ERROR_LIST = 'error_list'
ATTR_DRYLEVEL_STATE = 'drylevel_state'
ATTR_DRYLEVEL_LIST = 'drylevel_list'
ATTR_ECOHYBRID_STATAE = 'ecohybrid_state'
ATTR_ECOHYBRID_LIST = 'ecohybrid_list'
ATTR_PROCESS_STATE = 'process_state'
ATTR_PROCESS_LIST = 'process_list'
ATTR_CURRENT_SMARTCOURSE = 'current_smartcourse'
ATTR_SMARTCOURSE_LIST = 'smartcourse_list'
ATTR_ANTICREASE_MODE = 'anticrease_mode'
ATTR_CHILDLOCK_MODE = 'childlock_mode'
ATTR_SELFCLEANING_MODE = 'selfcleaning_mode'
ATTR_DAMPDRYBEEP_MODE = 'dampdrybeep_mode'
ATTR_HANDIRON_MODE = 'handiron_mode'
ATTR_RESERVE_INITIAL_TIME = 'reserve_initial_time'
ATTR_RESERVE_REMAIN_TIME = 'reserve_remain_time'
ATTR_DEVICE_TYPE = 'device_type'

RUNSTATES = {
    'OFF': wideq.STATE_DRYER_POWER_OFF,
    'INITIAL': wideq.STATE_DRYER_INITIAL,
    'RUNNING': wideq.STATE_DRYER_RUNNING,
    'PAUSE': wideq.STATE_DRYER_PAUSE,
    'END': wideq.STATE_DRYER_END,
    'ERROR': wideq.STATE_DRYER_ERROR,
}

PROCESSSTATES = {
    'DETECTING': wideq.STATE_DRYER_PROCESS_DETECTING,
    'STEAM': wideq.STATE_DRYER_PROCESS_STEAM,
    'DRY': wideq.STATE_DRYER_PROCESS_DRY,
    'COOLING': wideq.STATE_DRYER_PROCESS_COOLING,
    'ANTI_CREASE': wideq.STATE_DRYER_PROCESS_ANTI_CREASE,
    'END': wideq.STATE_DRYER_PROCESS_END,
    'OFF': wideq.STATE_DRYER_POWER_OFF,
}

DRYLEVELMODES = {
    'IRON' : wideq.STATE_DRY_LEVEL_IRON,
    'CUPBOARD' : wideq.STATE_DRY_LEVEL_CUPBOARD,
    'EXTRA' : wideq.STATE_DRY_LEVEL_EXTRA,
    'OFF': wideq.STATE_DRYER_POWER_OFF,    
}

ECOHYBRIDMODES = {
    'ECO' : wideq.STATE_ECOHYBRID_ECO,
    'NORMAL' : wideq.STATE_ECOHYBRID_NORMAL,
    'TURBO' : wideq.STATE_ECOHYBRID_TURBO,
    'OFF': wideq.STATE_DRYER_POWER_OFF,    
}

COURSES = {
    'Cotton Soft_타월' : wideq.STATE_COURSE_COTTON_SOFT,
    'Bulky Item_이불' : wideq.STATE_COURSE_BULKY_ITEM,
    'Easy Care_셔츠' : wideq.STATE_COURSE_EASY_CARE,
    'Cotton_표준' : wideq.STATE_COURSE_COTTON,
    'Sports Wear_기능성의류' : wideq.STATE_COURSE_SPORTS_WEAR,
    'Quick Dry_급속' : wideq.STATE_COURSE_QUICK_DRY,
    'Wool_울/섬세' : wideq.STATE_COURSE_WOOL,
    'Rack Dry_선반 건조' : wideq.STATE_COURSE_RACK_DRY,
    'Cool Air_송풍' : wideq.STATE_COURSE_COOL_AIR,        
    'Warm Air_온풍' : wideq.STATE_COURSE_WARM_AIR,
    '침구털기' : wideq.STATE_COURSE_BEDDING_BRUSH,
    'Sterilization_살균' : wideq.STATE_COURSE_STERILIZATION,
    'Power_강력' : wideq.STATE_COURSE_POWER,
    'Refresh': wideq.STATE_COURSE_REFRESH,
    'OFF': wideq.STATE_DRYER_POWER_OFF,
}

SMARTCOURSES = {
    'Gym Clothes_운동복' : wideq.STATE_SMARTCOURSE_GYM_CLOTHES,
    'Rainy Season_장마철' : wideq.STATE_SMARTCOURSE_RAINY_SEASON,
    'Deodorization_리프레쉬' : wideq.STATE_SMARTCOURSE_DEODORIZATION,
    'Small Load_소량 건조' : wideq.STATE_SMARTCOURSE_SMALL_LOAD,
    'Lingerie_란제리' : wideq.STATE_SMARTCOURSE_LINGERIE,
    'Easy Iron_촉촉 건조' : wideq.STATE_SMARTCOURSE_EASY_IRON,
    'SUPER_DRY' : wideq.STATE_SMARTCOURSE_SUPER_DRY,
    'Economic Dry_절약 건조' : wideq.STATE_SMARTCOURSE_ECONOMIC_DRY,
    'Big Size Item_큰 빨래 건조' : wideq.STATE_SMARTCOURSE_BIG_SIZE_ITEM,
    'Minimize Wrinkles_구김 완화 건조' : wideq.STATE_SMARTCOURSE_MINIMIZE_WRINKLES,
    'Full Size Load_다량 건조' : wideq.STATE_SMARTCOURSE_FULL_SIZE_LOAD,
    'Jean_청바지' : wideq.STATE_SMARTCOURSE_JEAN,
    'OFF': wideq.STATE_DRYER_POWER_OFF,

}

ERRORS = {
    'ERROR_DOOR' : wideq.STATE_ERROR_DOOR,
    'ERROR_DRAINMOTOR' : wideq.STATE_ERROR_DRAINMOTOR,
    'ERROR_LE1' : wideq.STATE_ERROR_LE1,
    'ERROR_TE1' : wideq.STATE_ERROR_TE1,
    'ERROR_TE2' : wideq.STATE_ERROR_TE2,
    'ERROR_F1' : wideq.STATE_ERROR_F1,
    'ERROR_LE2' : wideq.STATE_ERROR_LE2,
    'ERROR_AE' : wideq.STATE_ERROR_AE,
    'ERROR_dE4' : wideq.STATE_ERROR_dE4,
    'ERROR_NOFILTER' : wideq.STATE_ERROR_NOFILTER,
    'ERROR_EMPTYWATER' : wideq.STATE_ERROR_EMPTYWATER,
    'ERROR_CE1' : wideq.STATE_ERROR_CE1,
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

    """Set up the LGE Dryer components."""

    LOGGER.debug("Creating new LGE Dryer")

    LGE_DRYER_DEVICES = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)
        model = client.model_info(device)
        if device.type == wideq.DeviceType.DRYER:
            name = config[CONF_NAME]
            mac = device.macaddress
            conf_mac = config[CONF_MAC]
            model_type = model.model_type
            if mac == conf_mac.lower():
                dryer_entity = LGEDRYERDEVICE(client, device, name, model_type)
                LGE_DRYER_DEVICES.append(dryer_entity)
            else:
                LOGGER.error("MAC Address is not matched")

    add_entities(LGE_DRYER_DEVICES)

    LOGGER.debug("LGE Dryer is added")
    
class LGEDRYERDEVICE(LGEDevice):
    def __init__(self, client, device, name, model_type):
        
        """initialize a LGE Dryer Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._dryer = wideq.DryerDevice(client, device)

        self._dryer.monitor_start()
        self._dryer.monitor_start()
        self._dryer.delete_permission()
        self._dryer.delete_permission()

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
        """ none """

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_RUN_STATE] = self.current_run_state
        data[ATTR_RUN_LIST] = self.run_list
        data[ATTR_REMAIN_TIME] = self.remain_time
        data[ATTR_INITIAL_TIME] = self.initial_time
        data[ATTR_RESERVE_REMAIN_TIME] = self.reserve_remain_time
        data[ATTR_RESERVE_INITIAL_TIME] = self.reserve_initial_time
        data[ATTR_CURRENT_COURSE] = self.current_course
        data[ATTR_COURSE_LIST] = self.course_list
        data[ATTR_CURRENT_SMARTCOURSE] = self.current_smartcourse
        data[ATTR_SMARTCOURSE_LIST] = self.smartcourse_list
        data[ATTR_ERROR_STATE] = self.error_state
        data[ATTR_ERROR_LIST] = self.error_list
        data[ATTR_DRYLEVEL_STATE] = self.drylevel_state
        data[ATTR_DRYLEVEL_LIST] = self.drylevel_list
        data[ATTR_ECOHYBRID_STATAE] = self.ecohybrid_state
        data[ATTR_ECOHYBRID_LIST] = self.ecohybrid_list
        data[ATTR_PROCESS_STATE] = self.current_process_state
        data[ATTR_PROCESS_LIST] = self.process_list
        data[ATTR_ANTICREASE_MODE] = self.anticrease_mode
        data[ATTR_CHILDLOCK_MODE] = self.childlock_mode
        data[ATTR_SELFCLEANING_MODE] = self.selfcleaning_mode
        data[ATTR_DAMPDRYBEEP_MODE] = self.dampdrybeep_mode
        data[ATTR_HANDIRON_MODE] = self.handiron_mode
        return data
    
    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def state(self):
        if self._state:
            run = self._state.run_state
            return RUNSTATES[run.name]

    @property
    def current_run_state(self):
        if self._state:
            run = self._state.run_state
            return RUNSTATES[run.name]

    @property
    def run_list(self):
        return list(RUNSTATES.values())

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
    def reserve_remain_time(self):
        if self._state:
            reserve_hour = self._state.reservetime_hour
            reserve_min = self._state.reservetime_min
            reservetime = [reserve_hour, reserve_min]
            if int(reserve_min) < 10:
                return ":0".join(reservetime)
            else:
                return ":".join(reservetime)

    @property
    def reserve_initial_time(self):
        if self._state:
            reserveinitial_hour = self._state.reserveinitialtime_hour
            reserveinitial_min = self._state.reserveinitialtime_min
            reserveinitialtime = [reserveinitial_hour, reserveinitial_min]
            if int(reserveinitial_min) < 10:
                return ":0".join(reserveinitialtime)
            else:
                return ":".join(reserveinitialtime)


    @property
    def current_course(self):
        if self._state:
            course = self._state.current_course
            return COURSES[course]            

    @property
    def course_list(self):
        return list(COURSES.values())

    @property
    def current_smartcourse(self):
        if self._state:
            smartcourse = self._state.current_smartcourse
            return SMARTCOURSES[smartcourse]

    @property
    def smartcourse_list(self):
        return list(SMARTCOURSES.values())

    @property
    def error_state(self):
        if self._state:
            error = self._state.error_state
            return ERRORS[error]

    @property
    def error_list(self):
        return list(ERRORS.values())

    @property
    def drylevel_state(self):
        if self._state:
            drylevel = self._state.drylevel_state
            if drylevel == 'OFF':
                return DRYLEVELMODES['OFF']
            else:
                return DRYLEVELMODES[drylevel.name]

    @property
    def drylevel_list(self):
        return list(DRYLEVELMODES.values())

    @property
    def ecohybrid_state(self):
        if self._state:
            ecohybrid = self._state.ecohybrid_state
            if ecohybrid == 'OFF':
                return ECOHYBRIDMODES['OFF']
            else:
                return ECOHYBRIDMODES[ecohybrid.name]

    @property
    def ecohybrid_list(self):
        return list(ECOHYBRIDMODES.values())
        
    @property
    def current_process_state(self):
        if self._state:
            process = self._state.process_state
            if self.is_on == False:
                return PROCESSSTATES['OFF']
            else:
                return PROCESSSTATES[process.name]

    @property
    def process_list(self):
        return list(PROCESSSTATES.values())

    @property
    def anticrease_mode(self):
        if self._state:
            mode = self._state.anticrease_state
            return OPTIONITEMMODES[mode]

    @property
    def childlock_mode(self):
        if self._state:
            mode = self._state.childlock_state
            return OPTIONITEMMODES[mode]

    @property
    def selfcleaning_mode(self):
        if self._state:
            mode = self._state.selfcleaning_state
            return OPTIONITEMMODES[mode]

    @property
    def dampdrybeep_mode(self):
        if self._state:
            mode = self._state.dampdrybeep_state
            return OPTIONITEMMODES[mode]

    @property
    def handiron_mode(self):
        if self._state:
            mode = self._state.handiron_state
            return OPTIONITEMMODES[mode]

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._dryer.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._dryer.monitor_start()
                self._dryer.monitor_start()
                self._dryer.delete_permission()
                self._dryer.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._dryer.monitor_start()
                self._dryer.monitor_start()
                self._dryer.delete_permission()
                self._dryer.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._dryer.monitor_start()
        self._dryer.monitor_start()
        self._dryer.delete_permission()
        self._dryer.delete_permission()
