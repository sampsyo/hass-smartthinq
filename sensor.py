import datetime
import logging
import time
import voluptuous as vol

from custom_components.smartthinq import (
    CONF_LANGUAGE, KEY_SMARTTHINQ_DEVICES, LGDevice)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_REGION, CONF_TOKEN, DEVICE_CLASS_POWER, POWER_WATT

from . import wideq
from .wideq import dishwasher
from .wideq import ac

REQUIREMENTS = ['https://github.com/dacrypt/wideq/archive/master.zip#wideq==1.3.1']

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

ATTR_AC_STATE = 'state'
ATTR_AC_POWER = 'power'

MAX_RETRIES = 5

KEY_DW_OFF = 'Off'
KEY_DW_DISCONNECTED = 'Disconnected'

LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the LG dishwasher entities"""

    refresh_token = hass.data[CONF_TOKEN]
    region = hass.data[CONF_REGION]
    language = hass.data[CONF_LANGUAGE]

    client = wideq.Client.from_token(refresh_token, region, language)
    dishwashers = []
    acs = []

    for device_id in hass.data[KEY_SMARTTHINQ_DEVICES]:
        device = client.get_device(device_id)
        model = client.model_info(device)

        LOGGER.debug('SMARTTHINQ_DEVICE: %s' % device.type)
        LOGGER.debug('SMARTTHINQ_DEVICE: %s' % wideq.DeviceType.AC)

        if device.type == wideq.DeviceType.DISHWASHER:
            base_name = "lg_dishwasher_" + device.id
            LOGGER.debug("Creating new LG DishWasher: %s" % base_name)
            try:
                dishwashers.append(LGDishWasherDevice(client, device, base_name))
            except wideq.NotConnectedError:
                # Dishwashers are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass
        elif device.type == wideq.DeviceType.AC:
            # base_name = "lg_ac_" + device.id
            base_name = device.name + " Power"
            LOGGER.debug("Creating new LG AC power sensot: %s" % base_name)
            try:
                acs.append(LGACPowerSensor(client, device, base_name))
            except wideq.NotConnectedError:
                # AC are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass

    if dishwashers:
        add_entities(dishwashers, True)

    if acs:
        add_entities(acs, True)

    return True

class LGDishWasherDevice(LGDevice):
    def __init__(self, client, device, name):
        """Initialize an LG DishWasher Device."""

        super().__init__(client, device)

        # This constructor is called during platform creation. It must not
        # involve any API calls that actually need the dishwasher to be
        # connected, otherwise the device construction will fail and the entity
        # will not get created. Specifically, calls that depend on dishwasher
        # interaction should only happen in update(...), including the start of
        # the monitor task.
        self._dishwasher = dishwasher.DishWasherDevice(client, device)
        self._name = name
        self._status = None
        self._failed_request_count = 0

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
    def name(self):
        return self._name

    @property
    def state(self):
        if self._status:
          # Process is a more refined string to use for state, if it's present,
          # use it instead.
            return self._status.readable_process or self._status.readable_state
        return dishwasher.DISHWASHER_STATE_READABLE[
            dishwasher.DishWasherState.OFF.name]

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
            (self._status.process == dishwasher.DishWasherProcess.NIGHT_DRYING or
             self._status.state == dishwasher.DishWasherState.OFF or
             self._status.state == dishwasher.DishWasherState.COMPLETE)):
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
            self._status.state == dishwasher.DishWasherState.OFF):
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

    def _restart_monitor(self):
        try:
            self._dishwasher.monitor_start()
        except wideq.NotConnectedError:
            self._status = None
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()

    def update(self):
        """Poll for dishwasher state updates."""

        # This method is polled, so try to avoid sleeping in here. If an error
        # occurs, it will naturally be retried on the next poll.

        LOGGER.debug('Updating %s.', self.name)

        # On initial construction, the dishwasher monitor task
        # will not have been created. If so, start monitoring here.
        if getattr(self._dishwasher, 'mon', None) is None:
            self._restart_monitor()

        try:
            status = self._dishwasher.poll()
        except wideq.NotConnectedError:
            self._status = None
            return
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()
            self._restart_monitor()
            return

        if status:
            LOGGER.debug('Status updated.')
            self._status = status
            self._failed_request_count = 0
            return

        LOGGER.debug('No status available yet.')
        self._failed_request_count += 1

        if self._failed_request_count >= MAX_RETRIES:
            # We tried several times but got no result. This might happen
            # when the monitoring request gets into a bad state, so we
            # restart the task.
            self._restart_monitor()
            self._failed_request_count = 0
# class LGACDevice(LGDevice):
#     def __init__(self, client, device, name):
#         """Initialize an LG AC Device."""

#         super().__init__(client, device)

#         # This constructor is called during platform creation. It must not
#         # involve any API calls that actually need the ac to be
#         # connected, otherwise the device construction will fail and the entity
#         # will not get created. Specifically, calls that depend on ac
#         # interaction should only happen in update(...), including the start of
#         # the monitor task.
#         self._ac = ac.ACDevice(client, device)
#         self._name = name
#         self._status = None
#         self._failed_request_count = 0

#     @property
#     def state_attributes(self):
#         """Return the optional state attributes for the ac."""
#         data = {}
#         # For convenience, include the state as an attribute.
#         data[ATTR_AC_STATE] = self.state
#         return data

#     @property
#     def name(self):
#         return self._name

#     @property
#     def state(self):
#         if self._status:
#           # Process is a more refined string to use for state, if it's present,
#           # use it instead.
#             return self._status.mode.name 
#         return 'OFF'

#     @property
#     def error(self):
#         if self._status:
#             return self._status.error
#         return KEY_AC_DISCONNECTED

#     def _restart_monitor(self):
#         try:
#             self._ac.monitor_start()
#         except wideq.NotConnectedError:
#             self._status = None
#         except wideq.NotLoggedInError:
#             LOGGER.info('Session expired. Refreshing.')
#             self._client.refresh()

#     def update(self):
#         """Poll for ac state updates."""

#         # This method is polled, so try to avoid sleeping in here. If an error
#         # occurs, it will naturally be retried on the next poll.

#         LOGGER.debug('Updating sensor %s.', self.name)

#         # On initial construction, the ac monitor task
#         # will not have been created. If so, start monitoring here.
#         if getattr(self._ac, 'mon', None) is None:
#             self._restart_monitor()

#         try:
#             status = self._ac.poll()
#         except wideq.NotConnectedError:
#             self._status = None
#             return
#         except wideq.NotLoggedInError:
#             LOGGER.info('Session expired. Refreshing.')
#             self._client.refresh()
#             self._restart_monitor()
#             return

#         if status:
#             LOGGER.debug('Status updated.')
#             self._status = status
#             self._failed_request_count = 0
#             return

#         LOGGER.debug('No status available yet.')
#         self._failed_request_count += 1

#         if self._failed_request_count >= MAX_RETRIES:
#             # We tried several times but got no result. This might happen
#             # when the monitoring request gets into a bad state, so we
#             # restart the task.
#             self._restart_monitor()
#             self._failed_request_count = 0

class LGACPowerSensor(LGDevice):
    def __init__(self, client, device, name):
        """Initialize an LG AC Power Sensor."""

        super().__init__(client, device)

        # This constructor is called during platform creation. It must not
        # involve any API calls that actually need the ac to be
        # connected, otherwise the device construction will fail and the entity
        # will not get created. Specifically, calls that depend on ac
        # interaction should only happen in update(...), including the start of
        # the monitor task.
        self._ac = ac.ACDevice(client, device)
        self._name = name
        # self._status = None
        self._state = None
        self._unit_of_measurement = POWER_WATT
        self._device_class = DEVICE_CLASS_POWER
        self._failed_request_count = 0

    # @property
    # def state_attributes(self):
    #     """Return the optional state attributes for the ac."""
    #     data = {}
    #     data[ATTR_AC_POWER] = self.power

    #     # For convenience, include the state as an attribute.
    #     # data[ATTR_AC_STATE] = self.state
    #     return data

    @property
    def name(self):
        """Return the name of the sensor."""
        LOGGER.info('Sensor name: %s', self._name)
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Type of sensor."""
        return self._device_class

    # @property
    # def error(self):
    #     if self._status:
    #         return self._status.error
    #     return KEY_AC_DISCONNECTED

    def _restart_monitor(self):
        try:
            self._ac.monitor_start()
        except wideq.NotConnectedError:
            self._state = None
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()

    def update(self):
        """Poll for ac power updates."""

        # This method is polled, so try to avoid sleeping in here. If an error
        # occurs, it will naturally be retried on the next poll.

        LOGGER.debug('Updating sensor %s.', self.name)

        # On initial construction, the ac monitor task
        # will not have been created. If so, start monitoring here.
        if getattr(self._ac, 'mon', None) is None:
            LOGGER.debug('Restart monitor')
            self._restart_monitor()

        try:
            state = float(self._ac.get_power())
            LOGGER.debug('Power %d', state)

        except wideq.NotConnectedError:
            LOGGER.debug('Not connected')
            self._state = None
            return
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()
            self._restart_monitor()
            return

        if state:
            LOGGER.debug('state updated. %d', state)
            self._state = state
            self._failed_request_count = 0
            return

        LOGGER.debug('No state available yet.')
        self._failed_request_count += 1

        if self._failed_request_count >= MAX_RETRIES:
            # We tried several times but got no result. This might happen
            # when the monitoring request gets into a bad state, so we
            # restart the task.
            self._restart_monitor()
            self._failed_request_count = 0
