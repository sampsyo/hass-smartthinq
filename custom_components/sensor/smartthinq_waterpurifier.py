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

LGE_WATERPURIFIER_DEVICES = 'lge_waterpurifier_devices'

ATTR_COLD_WATER_USAGE_DAY = 'cold_water_usage_day'
ATTR_NORMAL_WATER_USAGE_DAY = 'normal_water_usage_day'
ATTR_HOT_WATER_USAGE_DAY = 'hot_water_usage_day'
ATTR_TOTAL_WATER_USAGE_DAY = 'total_water_usage_day'

ATTR_COLD_WATER_USAGE_WEEK = 'cold_water_usage_week'
ATTR_NORMAL_WATER_USAGE_WEEK = 'normal_water_usage_week'
ATTR_HOT_WATER_USAGE_WEEK = 'hot_water_usage_week'
ATTR_TOTAL_WATER_USAGE_WEEK = 'total_water_usage_week'

ATTR_COLD_WATER_USAGE_MONTH = 'cold_water_usage_month'
ATTR_NORMAL_WATER_USAGE_MONTH = 'normal_water_usage_month'
ATTR_HOT_WATER_USAGE_MONTH = 'hot_water_usage_month'
ATTR_TOTAL_WATER_USAGE_MONTH = 'total_water_usage_month'

ATTR_COLD_WATER_USAGE_YEAR = 'cold_water_usage_year'
ATTR_NORMAL_WATER_USAGE_YEAR = 'normal_water_usage_year'
ATTR_HOT_WATER_USAGE_YEAR = 'hot_water_usage_year'
ATTR_TOTAL_WATER_USAGE_YEAR = 'total_water_usage_year'

ATTR_COCKCLEAN_STATE = 'cockcelan_state'

COCKCLEANMODES = {
    'WAITING': wideq.STATE_WATERPURIFIER_COCKCLEAN_WAIT,
    'COCKCLEANING': wideq.STATE_WATERPURIFIER_COCKCLEAN_ON,
}

MAX_RETRIES = 5

LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)
    name = config[CONF_NAME]

    """Set up the LGE WATER PURIFIER components."""

    LOGGER.debug("Creating new LGE WATER PURIFIER")

    if LGE_WATERPURIFIER_DEVICES not in hass.data:
        hass.data[LGE_WATERPURIFIER_DEVICES] = []

    for device_id in (d for d in hass.data[LGE_DEVICES]):
        device = client.get_device(device_id)

        if device.type == wideq.DeviceType.WATER_PURIFIER:
            waterpurifier_entity = LGEWATERPURIFIERDEVICE(client, device, name)
            hass.data[LGE_WATERPURIFIER_DEVICES].append(waterpurifier_entity)
    add_entities(hass.data[LGE_WATERPURIFIER_DEVICES])

    LOGGER.debug("LGE WATER PURIFIER is added")
    
class LGEWATERPURIFIERDEVICE(LGEDevice):
    def __init__(self, client, device, name):
        
        """initialize a LGE WATER PURIFIER Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._wp = wideq.WPDevice(client, device)

        self._wp.monitor_start()
        self._wp.monitor_start()
        self._wp.delete_permission()
        self._wp.delete_permission()

        # The response from the monitoring query.
        self._state = None
        self._name = name
        
        self.update()

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        """ none """

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_COLD_WATER_USAGE_DAY] = self.cold_water_usage_day
        data[ATTR_NORMAL_WATER_USAGE_DAY] = self.normal_water_usage_day
        data[ATTR_HOT_WATER_USAGE_DAY] = self.hot_water_usage_day
        data[ATTR_TOTAL_WATER_USAGE_DAY] = self.total_water_usage_day
        data[ATTR_COLD_WATER_USAGE_WEEK] = self.cold_water_usage_week
        data[ATTR_NORMAL_WATER_USAGE_WEEK] = self.normal_water_usage_week
        data[ATTR_HOT_WATER_USAGE_WEEK] = self.hot_water_usage_week
        data[ATTR_TOTAL_WATER_USAGE_WEEK] = self.total_water_usage_week
        data[ATTR_COLD_WATER_USAGE_MONTH] = self.cold_water_usage_month
        data[ATTR_NORMAL_WATER_USAGE_MONTH] = self.normal_water_usage_month
        data[ATTR_HOT_WATER_USAGE_MONTH] = self.hot_water_usage_month
        data[ATTR_TOTAL_WATER_USAGE_MONTH] = self.total_water_usage_month
        data[ATTR_COLD_WATER_USAGE_YEAR] = self.cold_water_usage_year
        data[ATTR_NORMAL_WATER_USAGE_YEAR] = self.normal_water_usage_year
        data[ATTR_HOT_WATER_USAGE_YEAR] = self.hot_water_usage_year
        data[ATTR_TOTAL_WATER_USAGE_YEAR] = self.total_water_usage_year
        data[ATTR_COCKCLEAN_STATE] = self.cockclean_status
        return data
    
    @property
    def cold_water_usage_day(self):
        data = self._wp.day_water_usage('C')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def normal_water_usage_day(self):
        data = self._wp.day_water_usage('N')
        usage = format((float(data) * 0.001), ".3f")
        return usage
      
    @property
    def hot_water_usage_day(self):
        data = self._wp.day_water_usage('H')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def total_water_usage_day(self):
        cold = self.cold_water_usage_day
        normal = self.normal_water_usage_day
        hot = self.hot_water_usage_day
        total = format((float(cold) + float(normal) + float(hot)), ".3f")
        return total

    @property
    def cold_water_usage_week(self):
        data = self._wp.week_water_usage('C')
        usage = format((float(data) * 0.001), ".3f")
        return usage
    
    @property
    def normal_water_usage_week(self):
        data = self._wp.week_water_usage('N')
        usage = format((float(data) * 0.001), ".3f")
        return usage
    @property
    def hot_water_usage_week(self):
        data = self._wp.week_water_usage('H')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def total_water_usage_week(self):
        cold = self.cold_water_usage_week
        normal = self.normal_water_usage_week
        hot = self.hot_water_usage_week
        total = format((float(cold) + float(normal) + float(hot)), ".3f")
        return total

    @property
    def cold_water_usage_month(self):
        data = self._wp.month_water_usage('C')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def normal_water_usage_month(self):
        data = self._wp.month_water_usage('N')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def hot_water_usage_month(self):
        data = self._wp.month_water_usage('H')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def total_water_usage_month(self):
        cold = self.cold_water_usage_month
        normal = self.normal_water_usage_month
        hot = self.hot_water_usage_month
        total = format((float(cold) + float(normal) + float(hot)), ".3f")
        return total

    @property
    def cold_water_usage_year(self):
        data = self._wp.year_water_usage('C')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def normal_water_usage_year(self):
        data = self._wp.year_water_usage('N')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def hot_water_usage_year(self):
        data = self._wp.year_water_usage('H')
        usage = format((float(data) * 0.001), ".3f")
        return usage

    @property
    def total_water_usage_year(self):
        cold = self.cold_water_usage_year
        normal = self.normal_water_usage_year
        hot = self.hot_water_usage_year
        total = format((float(cold) + float(normal) + float(hot)), ".3f")
        return total

    @property
    def cockclean_status(self):
        if self._state:
            mode = self._state.cockclean_state
            return COCKCLEANMODES[mode.name]

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._wp.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._wp.monitor_start()
                self._wp.monitor_start()
                self._wp.delete_permission()
                self._wp.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._wp.monitor_start()
                self._wp.monitor_start()
                self._wp.delete_permission()
                self._wp.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._wp.monitor_start()
        self._wp.monitor_start()
        self._wp.delete_permission()
        self._wp.delete_permission()
