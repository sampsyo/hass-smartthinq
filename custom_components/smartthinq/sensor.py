import datetime
import logging
import time
import voluptuous as vol

from custom_components.smartthinq import (
    CONF_LANGUAGE, KEY_SMARTTHINQ_DEVICES, LGDevice)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_REGION, CONF_TOKEN

import wideq
from wideq import dishwasher

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

    for device_id in hass.data[KEY_SMARTTHINQ_DEVICES]:
        device = client.get_device(device_id)
        model = client.model_info(device)

        if device.type == wideq.DeviceType.DISHWASHER:
            base_name = "lg_dishwasher_" + device.id
            LOGGER.debug("Creating new LG DishWasher: %s" % base_name)
            try:
                dishwashers.append(LGDishWasherDevice(client, device, base_name))
            except wideq.NotConnectedError:
                # Dishwashers are only connected when in use. Ignore
                # NotConnectedError on platform setup.
                pass

    if dishwashers:
        add_entities(dishwashers, True)
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
