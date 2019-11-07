import wideq
import logging

"""General variables"""
REQUIREMENTS = ['wideq']
LOGGER = logging.getLogger(__name__)

"""Device specific imports"""
import datetime
from .LGDevice import LGDevice
from wideq import dryer as wideq_dryer

# Device specific dictionaries
DRYER_BIT_STATE = {
    'ON': 'On',
    'OFF': 'Off',
    'UNKNOWN': 'Unknown'
}

DRYER_STATE = {
    'UNKNOWN': 'Unknown',
    'POWER_OFF': 'Power Off',
    'INITIAL': 'Initial',
    'RUNNING': 'Running',
    'PAUSE': 'Paused',
    'COOLING': 'Cooling',
    'END': 'Complete',
    'ERROR': 'Error',
    'DRYING': 'Drying',
    'SMART_DIAGNOSIS': 'Smart diagnosis',
    'WRINKLE_CARE': 'Wrinkle care'
}

DRYER_ERROR = {
    'NO_ERROR': 'No error',
    'AE': 'Ae',
    'CE1': 'Ce1',
    'DE4': 'De4',
    'EMPTYWATER': 'Empty water',
    'DE': 'Door',
    'OE': 'Drainmotor',
    'F1': 'F1',
    'LE1': 'Le1',
    'LE2': 'Le2',
    'TE1': 'Te1',
    'TE2': 'Te2',
    'TE5': 'Te5',
    'TE6': 'Te6',
    'NOFILTER': 'No filter',
    'NP_GAS': 'Np',
    'PS': 'High power'
}

DRYER_IS_ON = {
    'YES': 'Yes',
    'NO': 'No'
}

DRYER_DRY_LEVEL = {
    'CUPBOARD': 'Cupboard',
    'DAMP': 'Damp',
    'EXTRA': 'Extra',
    'IRON': 'Iron',
    'LESS': 'Less',
    'MORE': 'More',
    'NORMAL': 'Normal',
    'VERY': 'Very'
}

DRYER_TEMPERATURE_CONTROL = {
    'OFF': 'Off',
    'ULTRA_LOW': 'Ultra low',
    'LOW': 'Low',
    'MEDIUM': 'Medium',
    'MID_HIGH': 'Mid high',
    'HIGH': 'High',
    'UNKNOWN': 'Unknown'
}

DRYER_TIME_DRY = {
    'OFF': 'Off',
    'TWENTY': '20',
    'THIRTY': '30',
    'FOURTY': '40',
    'FIFTY': '50',
    'SIXTY': '60',
    'UNKNOWN': 'Unknown'
}

DRYER_ECO_HYBRID = {
    'ECO': 'Eco',
    'NORMAL': 'Normal',
    'TURBO': 'Turbo'
}

DRYER_COURSE = {
    'COTTON_SOFT': 'Cotton Soft',
    'BULKY_ITEM': 'Bulky Item',
    'EASY_CARE': 'Easy Care',
    'COTTON': 'Cotton',
    'SPORTS_WEAR': 'Sportswear',
    'QUICK_DRY': 'Quick Dry',
    'WOOL': 'Wool',
    'RACK_DRY': 'Rack Dry',
    'COOL_AIR': 'Cool Air',
    'WARM_AIR': 'Warm Air',
    'BEDDING_BRUSH': 'Bedding Brush',
    'STERILIZATION': 'Sterilization',
    'REFRESH': 'Refresh',
    'POWER': 'Power',
    'NORMAL': 'Normal',
    'SPEED_DRY': 'Speed Dry',
    'HEAVY_DUTY': 'Heavy Duty',
    'TOWELS': 'Towels',
    'PERM_PRESS': 'Permenant Press',
    'DELICATES': 'Delicates',
    'BEDDING': 'Bedding',
    'AIR_DRY': 'Air Dry',
    'TIME_DRY': 'Time Dry',
    'ANTI_BACTERIAL': 'Anti Bacterial',
    'STEAM_FRESH': 'Steam Fresh',
    'STEAM_SANITARY': 'Steam Sanitary'
}

DRYER_SMART_COURSE = {
    'BABY_WEAR': 'Baby wear',
    'GYM_CLOTHES': 'Gym clothes',
    'BLANKET': 'Blanket',
    'BLANKET_REFRESH': 'Blanket refresh',
    'RAINY_SEASON': 'Rainy season',
    'SINGLE_GARMENTS': 'Single garments',
    'DEODORIZATION': 'Deodorization',
    'SMALL_LOAD': 'Small load',
    'LINGERIE': 'Lingerie',
    'EASY_IRON': 'Easy iron',
    'SUPER_DRY': 'Super dry',
    'ECONOMIC_DRY': 'Economic dry',
    'BIG_SIZE_ITEM': 'Big size item',
    'MINIMIZE_WRINKLES': 'Minimize wrinkles',
    'SHOES_FABRIC_DOLL': 'Shoes/Fabric Doll',
    'FULL_SIZE_LOAD': 'Full size load',
    'JEANS': 'Jeans'
}

DRYER_PROCESS_STATE = {
    'DETECTING': 'Detecting',
    'STEAM': 'Steam',
    'DRY': 'Dry',
    'COOLING': 'Cooling',
    'ANTI_CREASE': 'Anti-crease',
    'END': 'End',
    'OFF': 'Off'
}

# Class implementation
class LGDryerDevice(LGDevice):
    def __init__(self, client, max_retries, device):
        """Initialize an LG Dryer Device."""

        # Call LGDevice constructor
        super().__init__(client, max_retries, device, wideq_dryer.DryerDevice)

        # Overwrite variables
        self._name = "lg_dryer_" + device.id

    def bit_state(self, key, index):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            bit_value = int(self._status[key])
            bit_index = 2 ** index
            mode = bin(bit_value & bit_index)
            if mode == bin(0):
                key = 'OFF'
            else:
                key = 'ON'

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_BIT_STATE[key]
        except KeyError:
            return key

    @property
    def state_attributes(self):
        """Return the optional state attributes for the dishwasher."""
        data = {}
        data['state'] = self.state
        data['error'] = self.error
        data['is_on'] = self.is_on
        data['remaining_time'] = self.remaining_time
        data['remaining_time_in_minutes'] = self.remaining_time_in_minutes
        data['initial_time'] = self.initial_time
        data['initial_time_in_minutes'] = self.initial_time_in_minutes
        data['dry_level'] = self.dry_level
        data['temperature_control'] = self.temperature_control
        data['time_dry'] = self.time_dry
        data['eco_hybrid'] = self.eco_hybrid
        data['course'] = self.course
        data['smart_course'] = self.smart_course
        data['process_state'] = self.process_state
        data['anticrease_state'] = self.anticrease_state
        data['childlock_state'] = self.childlock_state
        data['selfcleaning_state'] = self.selfcleaning_state
        data['dampdrybeep_state'] = self.dampdrybeep_state
        data['handiron_state'] = self.handiron_state
        data['remotestart_state'] = self.remotestart_state
        data['initialbit_state'] = self.initialbit_state
        data['standby_state'] = self.standby_state
        return data

    @property
    def state(self):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            key = self._status.State.name
            if key.startswith('@WM_STATE_'):
                key = key[10:-2]

        # If we have a '-' state, it is off
        if key == '-':
            key = 'POWER_OFF'

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_STATE[key]
        except KeyError:
            return key

    @property
    def error(self):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            key = self._status.State.name
            if key.startswith('@WM_STATE_'):
                key = key[19:-2]

        # If we have a '-' state, it is off
        if key == '-' or key == 'No Error':
            key = 'NO_ERROR'

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_ERROR[key]
        except KeyError:
            return key

    @property
    def is_on(self):
        key = 'NO'
        if (self._status and self._status.is_on):
            key = 'YES'
        return DRYER_IS_ON[key]

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
    def dry_level(self):
        key = 'UNKNOWN'
        if self._status:
            key = self._status.DryLevel.name
            if key.startswith('@WM_DRY24_DRY_LEVEL_') or key.startswith('@WM_DRY27_DRY_LEVEL_'):
                key = key[20:-2]

        # If we have a '-' dry level, it is off
        if key == '-':
            key = 'OFF'

        try:
            return DRYER_DRY_LEVEL[key]
        except KeyError:
            return key

    @property
    def temperature_control(self):
        key = 'UNKNOWN'
        if self._status:
            key = self._status.TempControl.name

        if key == '-':
            key = 'OFF'

        try:
            return DRYER_TEMPERATURE_CONTROL[key]
        except KeyError:
            return key

    @property
    def time_dry(self):
        key = 'UNKNOWN'
        if self._status:
            key = self._status.TimeDry.name

        if key == '-':
            key = 'OFF'

        try:
            return DRYER_TIMEDRY[key]
        except KeyError:
            return key

    @property
    def eco_hybrid(self):
        key = 'UNKNOWN'
        if self._status:
            key = self._status.EcoHybrid.name
            if key.startswith('@WM_DRY'):
                key = key[20:-2]

        try:
            return DRYER_ECO_HYBRID[key]
        except KeyError:
            return key

    @property
    def course(self):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            key = self._status.Course.name
            if key.startswith('@WM_DRY'):
                key = key[17:-2]

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_COURSE[key]
        except KeyError:
            return key

    @property
    def smart_course(self):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            key = self._status.SmartCourse.name
            if key.startswith('@WM_WW_DRYER_SMARTCOURSE_'):
                key = key[25:-2]

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_SMART_COURSE[key]
        except KeyError:
            return key

    @property
    def process_state(self):
        key = 'UNKNOWN'

        # If we have a status
        if self._status:
            key = self._status.State.name
            if key.startswith('@WM_STATE_'):
                key = key[10:-2]

        # If we have a '-' state, it is off
        if key == '-':
            key = 'OFF'

        # Lookup the readable state representation, but if it fails, return the dryer returned value instead.
        try:
            return DRYER_PROCESS_STATE[key]
        except KeyError:
            return key

    @property
    def anticrease_state(self):
        return self.bit_state('Option1', 1)

    @property
    def childlock_state(self):
        return self.bit_state('Option1', 4)

    @property
    def selfcleaning_state(self):
        return self.bit_state('Option1', 5)

    @property
    def dampdrybeep_state(self):
        return self.bit_state('Option1', 6)

    @property
    def handiron_state(self):
        return self.bit_state('Option1', 7)

    @property
    def remotestart_state(self):
        return self.bit_state('Option2', 0)

    @property
    def initialbit_state(self):
        return self.bit_state('Option2', 1)

    @property
    def standby_state(self):
        return self.bit_state('Option2', 6)
