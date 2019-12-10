import wideq
import logging

from homeassistant.helpers.entity import Entity

LOGGER = logging.getLogger(__name__)

class LGDevice(Entity):
    def __init__(self, client, max_retries, device, wideq_constructor):
        self._client = client
        self._max_retries = max_retries
        self._device = device

        # Monitoring variables
        self._status = None
        self._name = "lg_device_" + device.id
        self._failed_request_count = 0

        # This constructor is called during platform creation. It must not
        # involve any API calls that actually need the dishwasher to be
        # connected, otherwise the device construction will fail and the entity
        # will not get created. Specifically, calls that depend on dishwasher
        # interaction should only happen in update(...), including the start of
        # the monitor task.
        self._wideq_device = wideq_constructor(client, device);

    @property
    def name(self):
        return self._name

    @property
    def available(self):
        return True

    def _restart_monitor(self):
        try:
            self._wideq_device.monitor_start()
        except wideq.NotConnectedError:
            LOGGER.info('Device not available.')
            self._status = None
        except wideq.NotLoggedInError:
            LOGGER.info('Session expired. Refreshing.')
            self._client.refresh()

    def update(self):
        """Poll for wideq device state updates."""

        # This method is polled, so try to avoid sleeping in here. If an error
        # occurs, it will naturally be retried on the next poll.
        LOGGER.debug('Updating %s.', self._name)

        # On initial construction, the dishwasher monitor task
        # will not have been created. If so, start monitoring here.
        if getattr(self._wideq_device, 'mon', None) is None:
            self._restart_monitor()

        try:
            status = self._wideq_device.poll()
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
