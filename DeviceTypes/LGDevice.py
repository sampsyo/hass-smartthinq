from homeassistant.helpers.entity import Entity

class LGDevice(Entity):
    def __init__(self, client, max_retries, device):
        self._client = client
        self._max_retries = max_retries
        self._device = device

        self._status = None
        self._name = "lg_device_" + device.id
        self._failed_request_count = 0

    @property
    def name(self):
        return self._name

    @property
    def available(self):
        return True

