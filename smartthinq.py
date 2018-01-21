import logging
import voluptuous as vol
from homeassistant.components import climate
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required('refresh_token'): cv.string,
})

MODES = {
    "@AC_MAIN_OPERATION_MODE_HEAT_W": climate.STATE_HEAT,
    "@AC_MAIN_OPERATION_MODE_COOL_W": climate.STATE_COOL,
    "@AC_MAIN_OPERATION_MODE_DRY_W": climate.STATE_DRY,
    "@AC_MAIN_OPERATION_MODE_FAN_W": climate.STATE_FAN_ONLY,
    "@AC_MAIN_OPERATION_MODE_ENERGY_SAVING_W": climate.STATE_ECO,
}
MAX_RETRIES = 5


def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    refresh_token = config.get('refresh_token')
    client = wideq.Client.from_token(refresh_token)

    add_devices(LGDevice(client, device) for device in client.devices)


class LGDevice(climate.ClimateDevice):
    def __init__(self, client, info):
        self._client = client
        self._device = info

        self._state = None

        # Cache the model information.
        self._model = client.model_info(self._device)

        self._mon = None
        self._start_monitoring()

    @property
    def temperature_unit(self):
        return const.TEMP_CELSIUS

    @property
    def name(self):
        return self._device.name

    @property
    def available(self):
        return True

    @property
    def supported_features(self):
        return (
            climate.SUPPORT_TARGET_TEMPERATURE |
            climate.SUPPORT_OPERATION_MODE
        )

    @property
    def current_temperature(self):
        if self._state:
            return float(self._state['TempCur'])

    @property
    def target_temperature(self):
        if self._state:
            return float(self._state['TempCfg'])

    @property
    def operation_list(self):
        return list(MODES.values())

    @property
    def current_operation(self):
        options = self._model.value('OpMode').options

        if self._state:
            mode = self._state['OpMode']
            mode_desc = options[mode]
            return MODES[mode_desc]

    def set_operation_mode(self, operation_mode):
        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}

        # Invert the OpMode mapping.
        options = self._model.value('OpMode').options
        options_inv = {v: k for k, v in options.items()}

        mode = options_inv[modes_inv[operation_mode]]
        self._client.session.set_device_controls(
            self._device.id,
            {'OpMode': mode},
        )

    def set_temperature(self, **kwargs):
        temperature = kwargs['temperature']
        self._client.session.set_device_controls(
            self._device.id,
            {'TempCfg': str(temperature)},
        )

    def _start_monitoring(self):
        """Start monitoring the device's status.

        Set the `_mon` field to an active `Monitor` object.
        """

        import wideq
        self._mon = wideq.Monitor(self._client.session, self._device.id)

    def update(self):
        """Poll for updated device status.

        Set the `_state` field to a new data mapping.
        """

        for _ in range(MAX_RETRIES):
            time.sleep(1)
            LOGGER.info('Polling...')
            res = self._mon.poll()
            if res:
                LOGGER.info('Status updated.')
                self._state = res
                return

        # We tried several times but got no result.
        LOGGER.warn('Status update failed.')
