import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
import datetime
from .LGDevice import LGDevice
from wideq import dryer as wideq_dryer

"""Device specific variables"""
ATTR_DRYER_REMAINING_TIME = 'remaining_time'
ATTR_DRYER_REMAINING_TIME_IN_MINUTES = 'remaining_time_in_minutes'
ATTR_DRYER_INITIAL_TIME = 'initial_time'
ATTR_DRYER_INITIAL_TIME_IN_MINUTES = 'initial_time_in_minutes'
ATTR_DRYER_ERROR = 'error'
ATTR_DRYER_STATE = 'state'

DRYER_STATE_READABLE = {
    'COOLING': 'Cooling',
    'END': 'Complete',
    'ERROR': 'Error',
    'DRYING': 'Drying',
    'INITIAL': 'Standby',
    'OFF': 'Off',
    'PAUSE': 'Paused',
    'RUNNING': 'Running',
    'SMART_DIAGNOSIS': 'Smart diagnosis',
    'WRINKLE_CARE': 'Wrinkle care',
    'UNKNOWN': 'Unknown'
}

DRYER_DRYLEVEL_READABLE = {
    'CUPBOARD': 'Cupboard',
    'DAMP': 'Damp',
    'EXTRA': 'Extra',
    'IRON': 'Iron',
    'LESS': 'Less',
    'MORE': 'More',
    'NORMAL': 'Normal',
    'OFF': 'Off',
    'VERY': 'Very',
    'UNKNOWN': 'Unknown'
}

DRYER_TEMPCONTROL_READABLE = {
    'OFF': 'Off',
    'ULTRA_LOW': 'Ultra low',
    'LOW': 'Low',
    'MEDIUM': 'Medium',
    'MID_HIGH': 'Mid high',
    'HIGH': 'High',
    'UNKNOWN': 'Unknown'
}

DRYER_TIMEDRY_READABLE = {
    'OFF': 'Off',
    'TWENTY': '20',
    'THIRTY': '30',
    'FOURTY': '40',
    'FIFTY': '50',
    'SIXTY': '60',
    'UNKNOWN': 'Unknown'
}
DRYER_ISON_YES = 'Yes'
DRYER_ISON_NO = 'No'
DRYER_COURSE_UNKNOWN = 'Unknown'
DRYER_SMARTCOURSE_UNKNOWN = 'Unknown'
DRYER_ERROR_NONE = ''

class LGDryerDevice(LGDevice):
    def __init__(self, client, max_retries, device):
        """Initialize an LG Dryer Device."""

        # Call LGDevice constructor
        super().__init__(client, max_retries, device, wideq_dryer.DryerDevice)

        # Overwrite variables
        self._name = "lg_dryer_" + device.id

    @property
    def state_attributes(self):
        """Return the optional state attributes for the dishwasher."""
        data = {}
        data[] = self.dry_level
        data[] = self.temperature_control
        data[] = self.time_dry
        data[] = self.is_on
        data[ATTR_DRYER_REMAINING_TIME] = self.remaining_time
        data[ATTR_DRYER_REMAINING_TIME_IN_MINUTES] = self.remaining_time_in_minutes
        data[ATTR_DRYER_INITIAL_TIME] = self.initial_time
        data[ATTR_DRYER_INITIAL_TIME_IN_MINUTES] = self.initial_time_in_minutes
        data[ATTR_DRYER_ERROR] = self.error
        data[] = self.course
        data[] = self.smart_course

        # For convenience, include the state as an attribute.
        data[ATTR_DRYER_STATE] = self.state
        return data

    @property
    def state(self):
        if self._status:
            return DRYER_STATE_READABLE[self._status.state.name]
        return DRYER_STATE_READABLE[wideq_dryer.DryerState.OFF.name]

    @property
    def dry_level(self):
        if self._status:
            return DRYER_DRYLEVEL_READABLE[self._status.dry_level.name]
        return DRYER_DRYLEVEL_READABLE[wideq_dryer.DryLevel.UNKNOWN.name]

    @property
    def temperature_control(self):
        if self._status:
            return DRYER_TEMPCONTROL_READABLE[self._status.temperature_control.name]
        return DRYER_TEMPCONTROL_READABLE[wideq_dryer.TempControl.UNKNOWN.name]

    @property
    def time_dry(self):
        if self._status:
            return DRYER_TIMEDRY_READABLE[self._status.time_dry.name]
        return DRYER_TIMEDRY_READABLE[wideq_dryer.TempControl.UNKNOWN.name]

    @property
    def is_on(self):
        if (self._status and self._status.is_on):
            return DRYER_ISON_YES
        return DRYER_ISON_NO

    @property
    def remaining_time(self):
        minutes = self.remaining_time_in_minutes if self._status else 0
        return str(datetime.timedelta(minutes=minutes))[:-3]

    @property
    def remaining_time_in_minutes(self):
        # The API (indefinitely) returns 1 minute remaining when a cycle is
        # either in state off or complete, or process night-drying. Return 0
        # minutes remaining in these instances, which is more reflective of
        # reality.
        if (self._status and
            (self._status.state == wideq_dryer.DryerState.END or
             self._status.state == wideq_dryer.DryerState.COMPLETE)):
            return 0
        return self._status.remaining_time if self._status else 0

    @property
    def initial_time(self):
        minutes = self.initial_time_in_minutes if self._status else 0
        return str(datetime.timedelta(minutes=minutes))[:-3]

    @property
    def initial_time_in_minutes(self):
        # When in state OFF, the dishwasher still returns the initial program
        # length of the previously ran cycle. Instead, return 0 which is more
        # reflective of the dishwasher being off.
        if (self._status and
            self._status.state == wideq_dryer.DryerState.OFF):
            return 0
        return self._status.initial_time if self._status else 0

    @property
    def course(self):
        if self._status:
            return self._status.course
        return DRYER_COURSE_UNKNOWN

    @property
    def smart_course(self):
        if self._status:
            return self._status.smart_course
        return DRYER_SMARTCOURSE_UNKNOWN

    @property
    def error(self):
        if self._status:
            return self._status.error
        return DRYER_ERROR_NONE
