
from homeassistant.helpers.entity import Entity

class LGDevice(Entity):
    def __init__(self, client, device):
        self._client = client
        self._device = device

    @property
    def name(self):
        return self._device.name

    @property
    def available(self):
        return True

