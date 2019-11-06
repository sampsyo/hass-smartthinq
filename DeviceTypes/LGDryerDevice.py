import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
import datetime
from .LGDevice import LGDevice

"""Device specific variables"""
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

KEY_DRYER_DISCONNECTED = 'Disconnected'

class LGDryerDevice(LGDevice):
    def __init__(self, client, device, max_retries):
        """Initialize an LG Dryer Device."""
        super().__init__(client, device)

        # This constructor is called during platform creation. It must not
        # involve any API calls that actually need the dishwasher to be
        # connected, otherwise the device construction will fail and the entity
        # will not get created. Specifically, calls that depend on dishwasher
        # interaction should only happen in update(...), including the start of
        # the monitor task.
        import wideq
        self._dryer = wideq.DryerDevice(client, device)
        self._status = None
        self._failed_request_count = 0
        self._max_retries = max_retries

    @property
    def state_attributes(self):
        """Return the optional state attributes for the dishwasher."""
        data = {}
        data[ATTR_DRYER_STATE] = self.state
        return data

    @property
    def name(self):
        return "lg_dryer_" + self._dryer.device.id

    @property
    def state(self):
        if self._status:
          # Process is a more refined string to use for state, if it's present,
          # use it instead.
            return self._status.readable_process or self._status.readable_state
        return DRYER_STATE_READABLE[dryer.DryerState.OFF.name]

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
            (self._status.state == dryer.DryerState.END or
             self._status.state == dryer.DryerState.COMPLETE)):
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
            self._status.state == dryer.DryerState.OFF):
            return 0
        return self._status.initial_time if self._status else 0

    @property
    def error(self):
        if self._status:
            return self._status.error
        return KEY_DRYER_DISCONNECTED

    def _restart_monitor(self):
        import wideq

        try:
            self._dryer.monitor_start()
        except wideq.NotConnectedError:
            self._status = None
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()

    def update(self):
        """Poll for dryer state updates."""

        # This method is polled, so try to avoid sleeping in here. If an error
        # occurs, it will naturally be retried on the next poll.
        LOGGER.debug('Updating %s.', self.name)

        # On initial construction, the dryer monitor task
        # will not have been created. If so, start monitoring here.
        if getattr(self._dryer, 'mon', None) is None:
            self._restart_monitor()

        import wideq
        try:
            status = self._dryer.poll()
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

        if self._failed_request_count >= self._max_retries:
            # We tried several times but got no result. This might happen
            # when the monitoring request gets into a bad state, so we
            # restart the task.
            self._restart_monitor()
            self._failed_request_count = 0
