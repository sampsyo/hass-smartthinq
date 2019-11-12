import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
import datetime
from .LGDevice import LGDevice
from wideq import dishwasher as wideq_dishwasher

"""Device specific variables"""
ATTR_DW_STATE = 'state'
ATTR_DW_REMAINING_TIME = 'remaining_time'
ATTR_DW_REMAINING_TIME_IN_MINUTES = 'remaining_time_in_minutes'
ATTR_DW_INITIAL_TIME = 'initial_time'
ATTR_DW_INITIAL_TIME_IN_MINUTES = 'initial_time_in_minutes'
ATTR_DW_RESERVE_TIME = 'reserve_time'
ATTR_DW_RESERVE_TIME_IN_MINUTES = 'reserve_time_in_minutes'
ATTR_DW_COURSE = 'course'
ATTR_DW_ERROR = 'error'
ATTR_DW_DEVICE_TYPE = 'device_type'
KEY_DW_OFF = 'Off'
KEY_DW_DISCONNECTED = 'Disconnected'

class LGDishwasherDevice(LGDevice):
    def __init__(self, client, max_retries, device):
        """Initialize an LG DishWasher Device."""

        # Call LGDevice constructor
        super().__init__(client, max_retries, device, wideq_dishwasher.DishWasherDevice)

        # Overwrite variables
        self._name = "lg_dishwasher_" + device.id

    @property
    def state_attributes(self):
        """Return the optional state attributes for the dishwasher."""
        data = {}
        data[ATTR_DW_REMAINING_TIME] = self.remaining_time
        data[ATTR_DW_REMAINING_TIME_IN_MINUTES] = self.remaining_time_in_minutes
        data[ATTR_DW_INITIAL_TIME] = self.initial_time
        data[ATTR_DW_INITIAL_TIME_IN_MINUTES] = self.initial_time_in_minutes
        data[ATTR_DW_RESERVE_TIME] = self.reserve_time
        data[ATTR_DW_RESERVE_TIME_IN_MINUTES] = self.reserve_time_in_minutes
        data[ATTR_DW_COURSE] = self.course
        data[ATTR_DW_ERROR] = self.error

        # For convenience, include the state as an attribute.
        data[ATTR_DW_STATE] = self.state
        return data

    @property
    def state(self):
        if self._status:
          # Process is a more refined string to use for state, if it's present,
          # use it instead.
            return self._status.readable_process or self._status.readable_state
        return dishwasher.DISHWASHER_STATE_READABLE[dishwasher.DishWasherState.OFF.name]

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
            (self._status.process == wideq_dishwasher.DishWasherProcess.NIGHT_DRYING or
             self._status.state == wideq_dishwasher.DishWasherState.OFF or
             self._status.state == wideq_dishwasher.DishWasherState.COMPLETE)):
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
            self._status.state == wideq_dishwasher.DishWasherState.OFF):
            return 0
        return self._status.initial_time if self._status else 0

    @property
    def reserve_time(self):
        minutes = self.reserve_time_in_minutes if self._status else 0
        return str(datetime.timedelta(minutes=minutes))[:-3]

    @property
    def reserve_time_in_minutes(self):
        return self._status.reserve_time if self._status else 0

    @property
    def course(self):
        if self._status:
            if self._status.smart_course != KEY_DW_OFF:
                return self._status.smart_course
            else:
                return self._status.course
        return KEY_DW_OFF

    @property
    def error(self):
        if self._status:
            return self._status.error
        return KEY_DW_DISCONNECTED

