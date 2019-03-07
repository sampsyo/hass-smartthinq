import logging
import threading
import voluptuous as vol
import json
from homeassistant.components import climate
from homeassistant.components.climate import (
	ClimateDevice)
from custom_components.smartthinq import (
	DOMAIN, LGE_DEVICES, LGEDevice)
from homeassistant.helpers.temperature import display_temp as show_temp
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant import const
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, TEMP_CELSIUS, CONF_NAME, CONF_TOKEN, CONF_ENTITY_ID,)
import time
import wideq

REQUIREMENTS = ['wideq_kr == 0.0.3']
DEPENDENCIES = ['smartthinq']

LGE_HVAC_DEVICES = 'lge_HVAC_devices'
LGE_REF_DEVICES = 'lge_REF_devices'
LGE_AIRPURIFIER_DEVICES = 'lge_AirPurifier_devices'
LGE_DEHUMIDIFIER_DEVICES = 'lge_dehumidifier_devices'

CONF_MAC = 'mac'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_MAC): cv.string,
})

# For HVAC
#-----------------------------------------------------------
SUPPORT_TARGET_TEMPERATURE = 1
SUPPORT_FAN_MODE = 64
SUPPORT_OPERATION_MODE = 128
SUPPORT_SWING_MODE = 512
SUPPORT_ON_OFF = 4096

CONF_AIRCLEAN_MODE = 'airclean_mode'
CONF_COOLPOWER_MODE = 'coolpower_mode'
CONF_AUTODRY_MODE = 'autodry_mode'
CONF_SMARTCARE_MODE = 'smartcare_mode'
CONF_POWERSAVE_MODE = 'powersave_mode'
CONF_LONGPOWER_MODE = 'longpower_mode'
CONF_WDIRUPDOWN_MODE = 'up_down_mode'
CONF_SENSORMON_MODE = 'sensormon_mode'
CONF_JET_MODE = 'jet_mode'
CONF_WDIRVSTEP_MODE = 'wdirvstep_mode'

ATTR_CURRENT_TEMPERATURE = 'current_temperature'
ATTR_MAX_TEMP = 'max_temp'
ATTR_MIN_TEMP = 'min_temp'
ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_HUMIDITY = 'humidity'
ATTR_SENSORPM1 = 'PM1'
ATTR_SENSORPM2 = 'PM2'
ATTR_SENSORPM10 = 'PM10'
ATTR_TOTALAIRPOLUTION = 'total_air_polution'
ATTR_FILTER_STATE = 'filter_state'
ATTR_MFILTER_STATE = 'mfilter_state'
ATTR_AIRPOLUTION = 'air_polution'
ATTR_OPERATION_MODE = 'operation_mode'
ATTR_OPERATION_LIST = 'operation_list'
ATTR_FAN_MODE = 'fan_mode'
ATTR_FAN_LIST = 'fan_list'
ATTR_SWING_MODE = 'swing_mode'
ATTR_SWING_LIST = 'swing_list'
ATTR_STATUS = 'current_status'
ATTR_AIRCLEAN_MODE = 'airclean_mode'
ATTR_COOLPOWER_MODE = 'coolpower_mode'
ATTR_AUTODRY_MODE = 'autodry_mode'
ATTR_SMARTCARE_MODE = 'smartcare_mode'
ATTR_POWERSAVE_MODE = 'powersave_mode'
ATTR_LONGPOWER_MODE = 'longpower_mode'
ATTR_UP_DOWN_MODE = 'up_down_mode'
ATTR_SENSORMON_MODE = 'sensormon_mode'
ATTR_JET_MODE = 'jet_mode'
ATTR_WDIRVSTEP_MODE = 'wdirvstep_mode'
ATTR_DEVICE_TYPE = 'device_type'

CONVERTIBLE_ATTRIBUTE = [
    ATTR_TEMPERATURE
]

SERVICE_SET_AIRCLEAN_MODE = 'lge_hvac_set_airclean_mode'
SERVICE_SET_COOLPOWER_MODE = 'lge_hvac_set_coolpower_mode'
SERVICE_SET_AUTODRY_MODE = 'lge_hvac_set_autodry_mode'
SERVICE_SET_SMARTCARE_MODE = 'lge_hvac_set_smartcare_mode'
SERVICE_SET_POWERSAVE_MODE = 'lge_hvac_set_powersave_mode'
SERVICE_SET_LONGPOWER_MODE = 'lge_hvac_set_longpower_mode'
SERVICE_SET_WDIRUPDOWN_MODE = 'lge_hvac_set_up_down_mode'
SERVICE_SET_SENSORMON_MODE = 'lge_hvac_set_sensormon_mode'
SERVICE_SET_JET_MODE = 'lge_hvac_set_jet_mode'
SERVICE_SET_WDIRVSTEP_MODE = 'lge_hvac_set_wdirvstep_mode'

MODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,
}

WITHFANMODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,
    'FAN': wideq.STATE_FAN,
}

RAC_SACMODES = {
    'COOL': wideq.STATE_COOL,
    'DRY': wideq.STATE_DRY,   
    'HEAT': wideq.STATE_HEAT,
    'AI': wideq.STATE_AI,
    'FAN': wideq.STATE_FAN,
}

FANMODES = {
    'LOW' : wideq.STATE_LOW,
    'MID' : wideq.STATE_MID,
    'HIGH' : wideq.STATE_HIGH,
    'RIGHT_ONLY_LOW': wideq.STATE_RIGHT_ONLY_LOW,
    'RIGHT_ONLY_MID': wideq.STATE_RIGHT_ONLY_MID,
    'RIGHT_ONLY_HIGH': wideq.STATE_RIGHT_ONLY_HIGH,
    'LEFT_ONLY_LOW': wideq.STATE_LEFT_ONLY_LOW,
    'LEFT_ONLY_MID': wideq.STATE_LEFT_ONLY_MID,
    'LEFT_ONLY_HIGH': wideq.STATE_LEFT_ONLY_HIGH,
    'RIGHT_LOW_LEFT_MID': wideq.STATE_RIGHT_LOW_LEFT_MID,
    'RIGHT_LOW_LEFT_HIGH': wideq.STATE_RIGHT_LOW_LEFT_HIGH,
    'RIGHT_MID_LEFT_LOW': wideq.STATE_RIGHT_MID_LEFT_LOW,
    'RIGHT_MID_LEFT_HIGH': wideq.STATE_RIGHT_MID_LEFT_HIGH,
    'RIGHT_HIGH_LEFT_LOW': wideq.STATE_RIGHT_HIGH_LEFT_LOW,
    'RIGHT_HIGH_LEFT_MID': wideq.STATE_RIGHT_HIGH_LEFT_MID,
}

SINGLE_FANMODES = {
    'SYSTEM_LOW': wideq.STATE_LOW,
    'SYSTEM_MID': wideq.STATE_MID,
    'SYSTEM_HIGH': wideq.STATE_HIGH,
}

RAC_SACFANMODES = {
    'SYSTEM_LOW': wideq.STATE_LOW,
    'SYSTEM_MID': wideq.STATE_MID,
    'SYSTEM_HIGH': wideq.STATE_HIGH,
    'SYSTEM_AUTO': wideq.STATE_AUTO,
    'SYSTEM_POWER': wideq.STATE_POWER,
}

SWINGMODES = {
    'LEFT_RIGHT': wideq.STATE_LEFT_RIGHT,
    'RIGHTSIDE_LEFT_RIGHT': wideq.STATE_RIGHTSIDE_LEFT_RIGHT,
    'LEFTSIDE_LEFT_RIGHT': wideq.STATE_LEFTSIDE_LEFT_RIGHT,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,
}

RAC_SACSWINGMODES = {
    'LEFT_RIGTH_ON': wideq.STATE_LEFT_RIGHT_ON,
    'LEFT_RIGHT_STOP': wideq.STATE_LEFT_RIGHT_STOP,
}

WDIRVSTEP = {
    'OFF': wideq.STATE_WDIRVSTEP_OFF,
    'FIRST': wideq.STATE_WDIRVSTEP_FIRST,
    'SECOND': wideq.STATE_WDIRVSTEP_SECOND,
    'THIRD': wideq.STATE_WDIRVSTEP_THIRD,
    'FOURTH': wideq.STATE_WDIRVSTEP_FOURTH,
    'FIFTH': wideq.STATE_WDIRVSTEP_FIFTH,
    'SIXTH': wideq.STATE_WDIRVSTEP_SIXTH,
}

ACETCMODES = {
    'ON': wideq.STATE_MODE_ON,
    'OFF': wideq.STATE_MODE_OFF,
}

LGE_HVAC_SET_AIRCLEAN_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRCLEAN_MODE): cv.string,
})

LGE_HVAC_SET_COOLPOWER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_COOLPOWER_MODE): cv.string,
})

LGE_HVAC_SET_AUTODRY_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AUTODRY_MODE): cv.string,
})

LGE_HVAC_SET_SMARTCARE_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SMARTCARE_MODE): cv.string,
})

LGE_HVAC_SET_POWERSAVE_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_POWERSAVE_MODE): cv.string,
})

LGE_HVAC_SET_LONGPOWER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_LONGPOWER_MODE): cv.string,
})

LGE_HVAC_SET_WDIRUPDOWN_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_WDIRUPDOWN_MODE): cv.string,
})
LGE_HVAC_SET_SENSORMON_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SENSORMON_MODE): cv.string,
})
LGE_HVAC_SET_JET_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_JET_MODE): cv.string,
})
LGE_HVAC_SET_WDIRVSTEP_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_WDIRVSTEP_MODE): cv.string,
})

TRANSIENT_EXP = 5.0  # Report set temperature for 5 seconds.
TEMP_MIN_C = 18
TEMP_MIN_HEAT_C = 16
TEMP_MAX_C = 26
TEMP_MAX_HEAT_C = 30

# For Refrigerator
#-----------------------------------------------------------

CONF_REFRIGERATOR_TEMPERATURE = 'refrigerator_temperature'
CONF_FREEZER_TEMPERATURE = 'freezer_temperature'
CONF_ICEPLUS_MODE = 'iceplus_mode'
CONF_FRESHAIRFILTER_MODE = 'freshairfilter_mode'

ATTR_REFRIGERATOR_TEMPERATURE = 'refrigerator_temperature'
ATTR_FREEZER_TEMPERATURE = 'freezer_temperature'
ATTR_ICEPLUS_STATE = 'iceplus_state'
ATTR_ICEPLUS_LIST = 'iceplus_list'
ATTR_FRESHAIRFILTER_STATE = 'freshairfilter_state'
ATTR_FRESHAIRFILTER_LIST = 'freshairfilter_list'
ATTR_SMARTSAVING_MODE = 'smartsaving_mode'
ATTR_WATERFILTER_STATE = 'waterfilter_state'
ATTR_DOOR_STATE = 'door_state'
ATTR_SMARTSAVING_STATE = 'smartsaving_state'
ATTR_LOCKING_STATE = 'locking_state'
ATTR_ACTIVESAVING_STATE = 'activesaving_state'

SERVICE_SET_REFRIGERATOR_TEMPERATURE = 'lge_ref_set_refrigerator_temperature'
SERVICE_SET_FREEZER_TEMPERATURE = 'lge_ref_set_freezer_temperature'
SERVICE_SET_ICEPLUS_MODE = 'lge_ref_set_iceplus_mode'
SERVICE_SET_FRESHAIRFILTER_MODE = 'lge_ref_set_freshairfilter_mode'

ICEPLUSMODES = {
    'ON': wideq.STATE_ICE_PLUS_ON,
    'OFF': wideq.STATE_ICE_PLUS_OFF,
    'ICE_PLUS': wideq.STATE_ICE_PLUS,
    'ICE_PLUS_FREEZE': wideq.STATE_ICE_PLUS_FREEZE,
    'ICE_PLUS_OFF': wideq.STATE_REF_MODE_OFF
}

FRESHAIRFILTERMODES = {
    'POWER' : wideq.STATE_FRESH_AIR_FILTER_POWER,
    'AUTO' : wideq.STATE_FRESH_AIR_FILTER_AUTO,
    'OFF' : wideq.STATE_FRESH_AIR_FILTER_OFF,
}

SMARTCAREMODES = {
    'SMARTCARE_ON' : wideq.STATE_FRESH_AIR_FILTER_SMART_CARE_ON,
    'SMARTCARE_OFF' : wideq.STATE_FRESH_AIR_FILTER_SMART_CARE_OFF,
    'SMARTCARE_WAIT' : wideq.STATE_FRESH_AIR_FILTER_SMART_CARE_WAIT,
    'REPLACE_FILTER' : wideq.STATE_FRESH_AIR_FILTER_REPLACE_FILTER,
}

SMARTSAVINGMODES = {
    'NIGHT' : wideq.STATE_SMART_SAVING_NIGHT,
    'CUSTOM' : wideq.STATE_SMART_SAVING_CUSTOM,
    'OFF' : wideq.STATE_SMART_SAVING_OFF,
}

LGE_REF_SET_REFRIGERATOR_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_REFRIGERATOR_TEMPERATURE): cv.string,
})

LGE_REF_SET_FREEZER_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_FREEZER_TEMPERATURE): cv.string,
})

LGE_REF_SET_ICEPLUS_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_ICEPLUS_MODE): cv.string,
})

LGE_REF_SET_FRESHAIRFILTER_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_FRESHAIRFILTER_MODE): cv.string,
})

# For Air Purifier
#-----------------------------------------------------------
CONF_CIRCULATEDIR_MODE = 'circulatedir_mode'
CONF_AIRREMOVAL_MODE = 'airremoval_mode'
CONF_SIGNALLIGHTING_MODE = 'signallighting_mode'
CONF_AIRFAST_MODE = 'airfast_mode'

ATTR_AIRREMOVAL_MODE = 'airremoval_mode'
ATTR_SIGNALLIGHTING_MODE = 'signallighting_mode'
ATTR_CIRCULATEDIR_MODE = 'circulatedir_mode'
ATTR_AIRFAST_MODE = 'airfast_mode'

SERVICE_SET_AIRREMOVAL_MODE = 'lge_airpurifier_set_airremoval_mode'
SERVICE_SET_SIGNALLIGHTING_MODE = 'lge_airpurifier_set_signallighting_mode'
SERVICE_SET_CIRCULATEDIR_MODE = 'lge_airpurifier_set_circulatedir_mode'
SERVICE_SET_AIRFAST_MODE = 'lge_airpurifier_set_airfast_mode'


APMODES = {
    'CLEANBOOSTER': wideq.STATE_AIRPURIFIER_CIRCULATOR_CLEAN,
    'SINGLECLEAN': wideq.STATE_AIRPURIFIER_BABY_CARE,
    'DUALCLEAN': wideq.STATE_AIRPURIFIER_DUAL_CLEAN,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO_MODE,
}

AP_AIR_910604_KR_MODES = {
    'CLEAN': wideq. STATE_AIRPURIFIER_CLEAN,
}

APFANMODES = {
    'LOW': wideq.STATE_AIRPURIFIER_LOW,
    'MID': wideq.STATE_AIRPURIFIER_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_HIGH,
    'POWER': wideq.STATE_AIRPURIFIER_POWER,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO,
}

AP_AIR_910604_KR_FANMODES ={
    'LOW': wideq.STATE_AIRPURIFIER_LOW,
    'MID': wideq.STATE_AIRPURIFIER_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_HIGH,
    'AUTO': wideq.STATE_AIRPURIFIER_AUTO,
}

APCIRCULATEMODES = {
    'LOW': wideq.STATE_AIRPURIFIER_CIR_LOW,
    'MID': wideq.STATE_AIRPURIFIER_CIR_MID,
    'HIGH': wideq.STATE_AIRPURIFIER_CIR_HIGH,
    'POWER': wideq.STATE_AIRPURIFIER_CIR_POWER,
    'AUTO': wideq.STATE_AIRPURIFIER_CIR_AUTO,
}

APETCMODES = {
    'NOT_SUPPORTED': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'ON': wideq.STATE_AIRPURIFIER_ON,
    'OFF': wideq.STATE_AIRPURIFIER_OFF,
}

APTOTALAIRPOLUTION = {
    'NOT_SUPPORT': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'GOOD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_GOOD,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'BAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_BAD,
    'VERYBAD': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_VERYBAD
}

APSMELL = {
    'NOT_SUPPORT': wideq.STATE_AIRPURIFIER_NOT_SUPPORTED,
    'WEEK': wideq.STATE_AIRPURIFIER_SMELL_WEEK,
    'NORMAL': wideq.STATE_AIRPURIFIER_TOTALAIRPOLUTION_NORMAL,
    'STRONG': wideq.STATE_AIRPURIFIER_SMELL_STRONG,
    'VERYSTRONG': wideq.STATE_AIRPURIFIER_SMELL_VERYSTRONG
}

LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRREMOVAL_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_CIRCULATEDIR_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_CIRCULATEDIR_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_SIGNALLIGHTING_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_SIGNALLIGHTING_MODE): cv.string,
})

LGE_AIRPURIFIER_SET_AIRFAST_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRFAST_MODE): cv.string,
})

# For Dehumidifier
#-----------------------------------------------------------
SUPPORT_TARGET_HUMIDITY = 8
SUPPORT_TARGET_HUMIDITY_HIGH = 16
SUPPORT_TARGET_HUMIDITY_LOW = 32

ATTR_MAX_HUMIDITY = 'max_humidity'
ATTR_MIN_HUMIDITY = 'min_humidity'
ATTR_TARGET_HUMIDITY_STEP = 'humidity_step'
ATTR_CURRENT_HUMIDITY = 'current_humidity'

SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE = 'lge_dehumidifier_set_airremoval_mode'

DEHUMMODES = {
    'SMART_DEHUM': wideq.STATE_DEHUM_OPMODE_SMART_DEHUM,
    'FAST_DEHUM': wideq.STATE_DEHUM_OPMODE_FAST_DEHUM,
    'SILENT_DEHUM': wideq.STATE_DEHUM_OPMODE_SILENT_DEHUM,
    'CONCENTRATION_DRY': wideq.STATE_DEHUM_OPMODE_CONCENTRATION_DRY,
    'CLOTHING_DRY': wideq.STATE_DEHUM_OPMODE_CLOTHING_DRY,
    'IONIZER' : wideq.STATE_DEHUM_OPMODE_IONIZER,
}

DEHUMFANMODES = {
    'LOW' : wideq.STATE_DEHUM_WINDSTRENGTH_LOW,
    'HIGH' : wideq.STATE_DEHUM_WIDESTRENGTH_HIGH,
}

DEHUMAIRREMOVALMODES = {
    'ON': wideq.STATE_DEHUM_AIRREMOVAL_ON,
    'OFF': wideq.STATE_DEHUM_AIRREMOVAL_OFF,
}

LGE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE_SCHEMA = vol.Schema({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Required(CONF_AIRREMOVAL_MODE): cv.string,
})
HUM_MIN = 30
HUM_MAX = 70
HUM_STEP = 5

MAX_RETRIES = 5
LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    import wideq
    refresh_token = hass.data[CONF_TOKEN]
    client = wideq.Client.from_token(refresh_token)
    name = config[CONF_NAME]
    conf_mac = config[CONF_MAC]

    """Set up the LGE entity."""
    for device_id in hass.data[LGE_DEVICES]:
        device = client.get_device(device_id)
        model = client.model_info(device)
        model_type = model.model_type
        mac = device.macaddress
        if device.type == wideq.DeviceType.AC:
            LGE_HVAC_DEVICES = []
            if mac == conf_mac.lower():
                LOGGER.debug("Creating new LGE HVAC")
                hvac_entity = LGEHVACDEVICE(client, device, name, model_type)
                LGE_HVAC_DEVICES.append(hvac_entity)
                add_entities(LGE_HVAC_DEVICES)
                LOGGER.debug("LGE HVAC is added")
        elif device.type == wideq.DeviceType.REFRIGERATOR:
            LGE_REF_DEVICES = []
            if mac == conf_mac.lower():
                LOGGER.debug("Creating new LGE Refrigerator")
                ref_entity = LGEREFDEVICE(client, device, name, model_type)
                LGE_REF_DEVICES.append(ref_entity)
                add_entities(LGE_REF_DEVICES)
                LOGGER.debug("LGE Refrigerator is added")
        elif device.type == wideq.DeviceType.AIR_PURIFIER:
            LGE_AIRPURIFIER_DEVICES = []
            if mac == conf_mac.lower():
                ap_entity = LGEAPDEVICE(client, device, name, model_type)
                LGE_AIRPURIFIER_DEVICES.append(ap_entity)
                add_entities(LGE_AIRPURIFIER_DEVICES)
                LOGGER.debug("LGE AirPurifier is added")
        elif device.type == wideq.DeviceType.DEHUMIDIFIER:
            LGE_DEHUMIDIFIER_DEVICES = []
            if mac == conf_mac.lower():
                dehum_entity = LGEDEHUMDEVICE(client, device, name, model_type)
                LGE_DEHUMIDIFIER_DEVICES.append(dehum_entity)
                add_entities(LGE_DEHUMIDIFIER_DEVICES)
                LOGGER.debug("LGE DEHUMIDIFIER is added")

    def hvac_service_handle(service):
        """Handle the HVAC services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        airclean_mode = service.data.get(CONF_AIRCLEAN_MODE)
        coolpower_mode = service.data.get(CONF_COOLPOWER_MODE)
        autodry_mode = service.data.get(CONF_AUTODRY_MODE)
        smartcare_mode = service.data.get(CONF_SMARTCARE_MODE)        
        powersave_mode = service.data.get(CONF_POWERSAVE_MODE)
        longpower_mode = service.data.get(CONF_LONGPOWER_MODE)
        up_down_mode = service.data.get(CONF_WDIRUPDOWN_MODE)
        sensormon_mode = service.data.get(CONF_SENSORMON_MODE)
        jet_mode = service.data.get(CONF_JET_MODE)
        wdirvstep_mode = service.data.get(CONF_WDIRVSTEP_MODE)


        if service.service == SERVICE_SET_AIRCLEAN_MODE:
            hvac_entity.airclean_mode(airclean_mode)
        elif service.service == SERVICE_SET_COOLPOWER_MODE:
            hvac_entity.coolpower_mode(coolpower_mode)
        elif service.service == SERVICE_SET_AUTODRY_MODE:
            hvac_entity.autodry_mode(autodry_mode)
        elif service.service == SERVICE_SET_SMARTCARE_MODE:
            hvac_entity.smartcare_mode(smartcare_mode)
        elif service.service == SERVICE_SET_POWERSAVE_MODE:
            hvac_entity.powersave_mode(powersave_mode)
        elif service.service == SERVICE_SET_LONGPOWER_MODE:
            hvac_entity.longpower_mode(longpower_mode)
        elif service.service == SERVICE_SET_WDIRUPDOWN_MODE:
            hvac_entity.up_down_mode(up_down_mode)    
        elif service.service == SERVICE_SET_SENSORMON_MODE:
            hvac_entity.sensormon_mode(sensormon_mode)
        elif service.service == SERVICE_SET_JET_MODE:
            hvac_entity.jet_mode(jet_mode)
        elif service.service == SERVICE_SET_WDIRVSTEP_MODE:
            hvac_entity.wdirvstep_mode(wdirvstep_mode)

    def ref_service_handle(service):
        """Handle the Refrigerator services."""
        entity_id = service.data.get(CONF_ENTITY_ID)
        refrigerator_temperature = service.data.get(CONF_REFRIGERATOR_TEMPERATURE)
        freezer_temperature = service.data.get(CONF_FREEZER_TEMPERATURE)
        iceplus_mode = service.data.get(CONF_ICEPLUS_MODE)
        freshairfilter_mode = service.data.get(CONF_FRESHAIRFILTER_MODE)
    
        if service.service == SERVICE_SET_REFRIGERATOR_TEMPERATURE:
            ref_entity.set_ref_temperature(refrigerator_temperature)
        elif service.service == SERVICE_SET_FREEZER_TEMPERATURE:
            ref_entity.set_freezer_temperature(freezer_temperature)
        elif service.service == SERVICE_SET_ICEPLUS_MODE:
            ref_entity.set_iceplus_mode(iceplus_mode)
        elif service.service == SERVICE_SET_FRESHAIRFILTER_MODE:
            ref_entity.set_fresh_air_filter_mode(freshairfilter_mode)
        
    def airpurifier_service_handle(service):
        """Handle the AirPurifier services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        airremoval_mode = service.data.get(CONF_AIRREMOVAL_MODE)
        circulatedir_mode = service.data.get(CONF_CIRCULATEDIR_MODE)
        signallighting_mode = service.data.get(CONF_SIGNALLIGHTING_MODE)
        airfast_mode = service.data.get(CONF_AIRFAST_MODE)

        if service.service == SERVICE_SET_AIRREMOVAL_MODE:
            ap_entity.airremoval_mode(airremoval_mode)
        elif service.service == SERVICE_SET_CIRCULATEDIR_MODE:
            ap_entity.circulatedir_mode(circulatedir_mode)
        elif service.service == SERVICE_SET_SIGNALLIGHTING_MODE:
            ap_entity.signallighting_mode(signallighting_mode)
        elif service.service == SERVICE_SET_AIRFAST_MODE:
            ap_entity.airfast_mode(airfast_mode)


    def dehum_service_handle(service):
        """Handle the DEHUMIDIFIER services."""
        entity_id = service.data.get(CONF_ENTITY_ID)
        airremoval_mode = service.data.get(CONF_AIRREMOVAL_MODE)
        
        if service.service == SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE:
            hvac_entity.airremoval_mode(airremoval_mode)

    # Register hvac service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRCLEAN_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_AIRCLEAN_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_COOLPOWER_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_COOLPOWER_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_AUTODRY_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_AUTODRY_MODE_SCHEMA) 
    hass.services.register(
        DOMAIN, SERVICE_SET_SMARTCARE_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_SMARTCARE_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_POWERSAVE_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_POWERSAVE_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_LONGPOWER_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_LONGPOWER_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_WDIRUPDOWN_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_WDIRUPDOWN_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_SENSORMON_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_SENSORMON_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_JET_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_JET_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_WDIRVSTEP_MODE, hvac_service_handle,
        schema=LGE_HVAC_SET_WDIRVSTEP_MODE_SCHEMA)
 
    # Register refrigerator service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_REFRIGERATOR_TEMPERATURE, ref_service_handle,
        schema=LGE_REF_SET_REFRIGERATOR_TEMPERATURE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_FREEZER_TEMPERATURE, ref_service_handle,
        schema=LGE_REF_SET_FREEZER_TEMPERATURE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_ICEPLUS_MODE, ref_service_handle,
        schema=LGE_REF_SET_ICEPLUS_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_FRESHAIRFILTER_MODE, ref_service_handle,
        schema=LGE_REF_SET_FRESHAIRFILTER_MODE_SCHEMA)

    # Register air purifier service(s)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRREMOVAL_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_AIRREMOVAL_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_CIRCULATEDIR_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_CIRCULATEDIR_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_SIGNALLIGHTING_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_SIGNALLIGHTING_MODE_SCHEMA)
    hass.services.register(
        DOMAIN, SERVICE_SET_AIRFAST_MODE, airpurifier_service_handle,
        schema=LGE_AIRPURIFIER_SET_AIRFAST_MODE_SCHEMA) 

    # Register dehumidifier service(s)
    hass.services.register(
        DOMAIN, SERVICE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE, dehum_service_handle,
        schema=LGE_DEHUMIDIFIER_SET_AIRREMOVAL_MODE_SCHEMA)

# HVAC Main
class LGEHVACDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name, model_type, celsius=True):
        """initialize a LGE HAVC Device."""
        LGEDevice.__init__(self, client, device)
        self._celsius = celsius

        import wideq
        self._ac = wideq.ACDevice(client, device)

        self._ac.monitor_start()
        self._ac.monitor_start()
        self._ac.delete_permission()
        self._ac.delete_permission()

        # The response from the monitoring query.
        self._state = None
        # Store a transient temperature when we've just set it. We also
        # store the timestamp for when we set this value.
        self._transient_temp = None
        self._transient_time = None
        self._name = name
        self._type = model_type
        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type

    @property
    def supported_features(self):
        return (
            SUPPORT_TARGET_TEMPERATURE |
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_SWING_MODE |
            SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {}
        data = {
            ATTR_CURRENT_TEMPERATURE: show_temp(
                self.hass, self.current_temperature, self.temperature_unit,
                self.precision),
            ATTR_MIN_TEMP: show_temp(
                self.hass, self.min_temp, self.temperature_unit,
                self.precision),
            ATTR_MAX_TEMP: show_temp(
                self.hass, self.max_temp, self.temperature_unit,
                self.precision),      
            ATTR_TEMPERATURE: show_temp(
                self.hass, self.target_temperature, self.temperature_unit,
                self.precision),
        }
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_TARGET_TEMPERATURE] = self.target_temperature
        data[ATTR_AIRCLEAN_MODE] = self.is_airclean_mode
        data[ATTR_COOLPOWER_MODE] = self.is_coolpower_mode
        data[ATTR_AUTODRY_MODE] = self.is_autodry_mode
        data[ATTR_SMARTCARE_MODE] = self.is_smartcare_mode
        data[ATTR_POWERSAVE_MODE] = self.is_powersave_mode
        data[ATTR_LONGPOWER_MODE] = self.is_longpower_mode
        data[ATTR_UP_DOWN_MODE] = self.is_up_down_mode
        data[ATTR_SENSORMON_MODE] = self.is_sensormon_mode
        data[ATTR_WDIRVSTEP_MODE] = self.is_wdirvstep_mode
        data[ATTR_HUMIDITY] = self.humidity
        data[ATTR_SENSORPM1] = self.sensorpm1
        data[ATTR_SENSORPM2] = self.sensorpm2
        data[ATTR_SENSORPM10] = self.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self.total_air_polution
        data[ATTR_AIRPOLUTION] = self.air_polution
        data[ATTR_STATUS] = self.current_status
        data[ATTR_FILTER_STATE] = self.filter_state
        data[ATTR_MFILTER_STATE] = self.mfilter_state
        supported_features = self.supported_features
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        if supported_features & SUPPORT_SWING_MODE:
            data[ATTR_SWING_MODE] = self.current_swing_mode
            if self.swing_list:
                data[ATTR_SWING_LIST] = self.swing_list
        return data

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def current_status(self):
        if self.is_on == True:
            return 'ON'
        elif self.is_on == False:
            return 'OFF'

    def turn_on(self):
        LOGGER.info('Turning on...')
        self._ac.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._ac.set_on(False)
        LOGGER.info('...done.') 

    @property
    def support_oplist(self):
        return self._state.support_oplist


    @property
    def operation_list(self):
        if self.device_type == 'PAC':
            if 'FAN' in self.support_oplist:
                return list(WITHFANMODES.values())  
            else:
                return list(MODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACMODES.values())
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACMODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return WITHFANMODES[mode.name]
                else:
                    return MODES[mode.name]
            if self.device_type == 'RAC':
                return RAC_SACMODES[mode.name]
            elif self.device_type == 'SAC_CST':
                return RAC_SACMODES[mode.name]
            
    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in MODES.items()}
        withfan_modes_inv = {v: k for k, v in WITHFANMODES.items()}
        rac_sacmodes_inv = {v: k for k, v in RAC_SACMODES.items()}
        
        if self.device_type == 'PAC':
            if 'FAN' in self.support_oplist:
                mode = wideq.ACMode[withfan_modes_inv[operation_mode]]
            else:
                mode = wideq.ACMode[modes_inv[operation_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.ACMode[rac_sacmodes_inv[operation_mode]]
        elif self.device_type == 'SAC_CST':
            mode = wideq.ACMode[rac_sacmodes_inv[operation_mode]]
        self._ac.set_mode(mode)

    @property
    def support_fanlist(self):
        mode = self._state.windstrength_state
        if mode.name in SINGLE_FANMODES.keys():
            return self._state.support_fanlist
        else:
            return mode.name

    @property
    def fan_list(self):
        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return list(SINGLE_FANMODES.values())  
            else:
                return list(FANMODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACFANMODES.values())            
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACFANMODES.values())

    @property
    def current_fan_mode(self):
        if self._state:
            mode = self._state.windstrength_state
            if self.device_type == 'PAC':
                if 'SYSTEM_LOW' in self.support_fanlist:
                    return SINGLE_FANMODES[mode.name]
                else: 
                    return FANMODES[mode.name]
            elif self.device_type == 'RAC':
                return RAC_SACFANMODES[mode.name]                
            elif self.device_type == 'SAC_CST':
                return RAC_SACFANMODES[mode.name]
                    
    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in FANMODES.items()}
        single_fanmodes_inv = {v: k for k, v in SINGLE_FANMODES.items()}
        rac_sacfanmodes_inv = {v: k for k, v in RAC_SACFANMODES.items()}

        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                mode = wideq.ACWindstrength[single_fanmodes_inv[fan_mode]]
            else:
                mode = wideq.ACWindstrength[fanmodes_inv[fan_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.ACWindstrength[rac_sacfanmodes_inv[fan_mode]]            
        elif self.device_type == 'SAC_CST':
            mode = wideq.ACWindstrength[rac_sacfanmodes_inv[fan_mode]]
        self._ac.set_windstrength(mode)

    @property
    def swing_list(self):
        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return '지원안함'
            else:
                return list(SWINGMODES.values())
        elif self.device_type == 'RAC':
            return list(RAC_SACSWINGMODES.values())
        elif self.device_type == 'SAC_CST':
            return list(RAC_SACSWINGMODES.values())

    @property
    def current_swing_mode(self):
        if self._state:
            mode = self._state.wdirleftright_state
            if self.device_type == 'PAC':
                if 'SYSTEM_LOW' in self.support_fanlist:
                    return '지원안함'
                else:
                    return SWINGMODES[mode.name]
            elif self.device_type == 'RAC':
                return RAC_SACSWINGMODES[mode.name]     
            elif self.device_type == 'SAC_CST':
                return RAC_SACSWINGMODES[mode.name]
            
    def set_swing_mode(self, swing_mode):

        import wideq
        swingmodes_inv = {v: k for k, v in SWINGMODES.items()}
        rac_sacswingmodes_inv = {v: k for k, v in RAC_SACSWINGMODES.items()}

        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return '지원안함'
            else:
                mode = wideq.WDIRLEFTRIGHT[swingmodes_inv[swing_mode]]
        elif self.device_type == 'RAC':
            mode = wideq.WDIRLEFTRIGHT[rac_sacswingmodes_inv[swing_mode]]
        elif self.device_type == 'SAC_CST':
            mode = wideq.WDIRLEFTRIGHT[rac_sacswingmodes_inv[swing_mode]]
        self._ac.set_wind_leftright(mode)

    @property
    def is_wdirvstep_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                return '지원안함'
            elif self.device_type == 'RAC':
                try:
                    mode = self._state.wdirvstep_state
                    return WDIRVSTEP[mode.name]
                except ValueError:
                    fourvain_mode = self._state.fourvain_wdirvstep_state
                    return WDIRVSTEP[fourvain_mode.name]
            elif self.device_type == 'SAC_CST':
                try:
                    mode = self._state.wdirvstep_state
                    return WDIRVSTEP[mode.name]
                except ValueError:
                    fourvain_mode = self._state.fourvain_wdirvstep_state
                    return WDIRVSTEP[fourvain_mode.name]

    def wdirvstep_mode(self, wdirvstep_mode):

        import wideq
        wdirvstepmodes_inv = {v: k for k, v in WDIRVSTEP.items()}

        if self.device_type == 'PAC':
            return '지원안함'
        elif self.device_type == 'RAC':
            vstep_state = self._state.wdirvstep_state
            if int(vstep_state.value) < 10:
                mode = wideq.WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
            elif int(vstep_state.value) > 10:
                mode = wideq.FOURVAIN_WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
        elif self.device_type == 'SAC_CST':
            vstep_state = self._state.wdirvstep_state
            if int(vstep_state.value) < 10:
                mode = wideq.WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
            elif int(vstep_state.value) > 10:
                mode = wideq.FOURVAIN_WDIRVSTEP[wdirvstepmodes_inv[wdirvstep_mode]]
        self._ac.set_wdirvstep(mode)

    @property
    def is_airclean_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return '지원안함'
                else:
                    mode = self._state.airclean_state
            elif self.device_type == 'RAC':
                mode = self._state.airclean_state
            elif self.device_type == 'SAC_CST':
                mode = self._state.sac_airclean_state
            return ACETCMODES[mode.name]
    
    def airclean_mode(self, airclean_mode):
        name = 'AirClean'
        if airclean_mode == 'ON':
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return '지원안함'
                else:
                    self._ac.set_airclean(True)
            elif self.device_type == 'RAC':
                self._ac.set_airclean(True)
            elif self.device_type == 'SAC_CST':
                self._ac.set_etc_mode(name, True)
        elif airclean_mode == 'OFF':
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return '지원안함'
                else:
                    self._ac.set_airclean(False)
            elif self.device_type == 'RAC':
                self._ac.set_airclean(False)
            elif self.device_type == 'SAC_CST':
                self._ac.set_etc_mode(name, False)

    @property
    def is_autodry_mode(self):
        if self._state:
            mode = self._state.autodry_state
            return ACETCMODES[mode.name]


    def autodry_mode(self, autodry_mode):
        name = 'AutoDry'
        if autodry_mode == 'ON':
            self._ac.set_etc_mode(name, True)
        elif autodry_mode == 'OFF':
            self._ac.set_etc_mode(name, False)

    @property
    def is_smartcare_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return '지원안함'
                else:
                    mode = self._state.smartcare_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    def smartcare_mode(self, smartcare_mode):
        name = 'SmartCare'
        if self.device_type == 'PAC':
            if 'FAN' in self.support_oplist:
                return '지원안함'
            else:
                if smartcare_mode == 'ON':
                    self._ac.set_etc_mode(name, True)
                elif smartcare_mode == 'OFF':
                    self._ac.set_etc_mode(name, False)
            

    @property
    def is_powersave_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'FAN' in self.support_oplist:
                    return '지원안함'
                else:
                    mode = self._state.powersave_state
            else:
                mode = self._state.powersave_state                    
            return ACETCMODES[mode.name]


    def powersave_mode(self, powersave_mode):
        name = 'PowerSave'
        if self.device_type == 'PAC':
            if 'FAN' in self.support_oplist:
                return '지원안함'
            else:
                if powersave_mode == 'ON':
                    self._ac.set_etc_mode(name, True) 
        else:
            if powersave_mode == 'ON':
                self._ac.set_etc_mode(name, True)

    @property
    def is_coolpower_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'SYSTEM_LOW' in self.support_fanlist:
                    return '지원안함'
                else:
                    mode = self._state.icevalley_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    def coolpower_mode(self, coolpower_mode):
        name = 'IceValley'
        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return '지원안함'
            else:
                if coolpower_mode == 'ON':
                    self._ac.set_etc_mode(name, True)
                elif coolpower_mode == 'OFF':
                    self._ac.set_etc_mode(name, False)

    @property
    def is_longpower_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'SYSTEM_LOW' in self.support_fanlist:
                    return '지원안함'
                else:
                    mode = self._state.longpower_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    def longpower_mode(self, longpower_mode):
        name = 'FlowLongPower'
        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return '지원안함'
            else:
                if longpower_mode == 'ON':
                    self._ac.set_etc_mode(name, True)
                elif longpower_mode == 'OFF':
                    self._ac.set_etc_mode(name, False)

    @property
    def is_up_down_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                if 'SYSTEM_LOW' in self.support_fanlist:
                    return '지원안함'
                else:
                    mode = self._state.wdirupdown_state
                    return ACETCMODES[mode.name]

    def up_down_mode(self, up_down_mode):
        name = 'WDirUpDown'
        if self.device_type == 'PAC':
            if 'SYSTEM_LOW' in self.support_fanlist:
                return '지원안함'
            else:
                if up_down_mode == 'ON':
                    self._ac.set_etc_mode(name, True)
                elif up_down_mode == 'OFF':
                    self._ac.set_etc_mode(name, False)

    @property
    def is_sensormon_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.sensormon_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    def sensormon_mode(self, sensormon_mode):
        name = 'SensorMon'
        if self.device_type == 'PAC':
            if sensormon_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif sensormon_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

    @property
    def is_jet_mode(self):
        if self._state:
            if self.device_type == 'PAC':
                return '지원안함'
            elif self.device_type == 'RAC':
                mode = self._state.jet_state
                return ACETCMODES[mode.name]
            elif self.device_type == 'SAC_CST':
                mode = self._state.jet_state
                return ACETCMODES[mode.name]

    def jet_mode(self, jet_mode):
        name = 'Jet'
        if self.device_type == 'RAC':
            if jet_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif jet_mode == 'OFF':
                self._ac.set_etc_mode(name, False)
        elif self.device_type == 'SAC_CST':
            if jet_mode == 'ON':
                self._ac.set_etc_mode(name, True)
            elif jet_mode == 'OFF':
                self._ac.set_etc_mode(name, False)

    @property
    def filter_state(self):
        data = self._ac.get_filter_state()
        usetime = data['UseTime']
        changeperiod = data['ChangePeriod']
        use = int(usetime)/int(changeperiod)
        remain = (1 - use)*100

        if changeperiod == '0':
            return 'No Filter'
        else:
            return int(remain)

    @property
    def mfilter_state(self):
        data = self._ac.get_mfilter_state()

        remaintime = data['RemainTime']
        changeperiod = data['ChangePeriod']
        remain = int(remaintime)/int(changeperiod)

        if changeperiod == '0':
            return 'No mFilter'
        else:
            return int(remain * 100)

    @property
    def humidity(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.humidity
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'
    
    @property
    def sensorpm1(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm1
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    @property
    def sensorpm2(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm2
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    @property
    def sensorpm10(self):
        if self._state:
            if self.device_type == 'PAC':
                return self._state.sensorpm10
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    @property
    def air_polution(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.air_polution
                return APSMELL[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    @property
    def total_air_polution(self):
        if self._state:
            if self.device_type == 'PAC':
                mode = self._state.total_air_polution
                return APTOTALAIRPOLUTION[mode.name]
            elif self.device_type == 'RAC':
                return '지원안함'
            elif self.device_type == 'SAC_CST':
                return '지원안함'

    @property
    def temperature_unit(self):
        if self._celsius:
            return const.TEMP_CELSIUS
        else:
            return const.TEMP_FAHRENHEIT

    @property
    def min_temp(self):
        if self._celsius:
            if self.device_type == 'PAC':
                return TEMP_MIN_C
            elif self.device_type == 'RAC':
                return TEMP_MIN_HEAT_C
            elif self.device_type == 'SAC_CST':
                return TEMP_MIN_HEAT_C
        return climate.ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        if self._celsius:
            if self.device_type == 'PAC':
                return TEMP_MAX_C
            elif self.device_type == 'RAC':
                return TEMP_MAX_HEAT_C
            elif self.device_type == 'SAC_CST':
                return TEMP_MAX_HEAT_C
        return climate.ClimateDevice.max_temp.fget(self)

    @property
    def current_temperature(self):
        if self._state:
            if self._celsius:
                return self._state.temp_cur_c

    @property
    def target_temperature(self):
        # Use the recently-set target temperature if it was set recently
        # (within TRANSIENT_EXP seconds ago).
        if self._transient_temp:
            interval = time.time() - self._transient_time
            if interval < TRANSIENT_EXP:
                return self._transient_temp
            else:
                self._transient_temp = None

        # Otherwise, actually use the device's state.
        if self._state:
            if self._celsius:
                return self._state.temp_cfg_c
            else:
                return self._state.temp_cfg_f

    def set_temperature(self, **kwargs):
        temperature = kwargs['temperature']
        self._transient_temp = temperature
        self._transient_time = time.time()

        LOGGER.info('Setting temperature to %s...', temperature)
        if self._celsius:
            self._ac.set_celsius(temperature)
        else:
            self._ac.set_fahrenheit(temperature)
        LOGGER.info('Temperature set.')

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ac.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ac.monitor_start()
                self._ac.monitor_start()
                self._ac.delete_permission()
                self._ac.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ac.monitor_start()
                self._ac.monitor_start()
                self._ac.delete_permission()
                self._ac.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ac.monitor_start()
        self._ac.monitor_start()
        self._ac.delete_permission()
        self._ac.delete_permission()


# Refrigerator Main
class LGEREFDEVICE(LGEDevice):
    def __init__(self, client, device, name, model_type):
        
        """initialize a LGE Refrigerator Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._ref = wideq.RefDevice(client, device)

        self._ref.monitor_start()
        self._ref.monitor_start()
        self._ref.delete_permission()
        self._ref.delete_permission()

        # The response from the monitoring query.
        self._state = None
        # Store a transient temperature when we've just set it. We also
        # store the timestamp for when we set this value.
        self._transient_temp = None
        self._transient_time = None
        self._name = name
        self._type = model_type

        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type
            
    @property
    def supported_features(self):
        """ none """

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_REFRIGERATOR_TEMPERATURE] = self.current_reftemp
        data[ATTR_FREEZER_TEMPERATURE] = self.current_freezertemp
        data[ATTR_ICEPLUS_STATE] = self.ice_plus_state
        data[ATTR_ICEPLUS_LIST] = self.ice_plus_list
        data[ATTR_FRESHAIRFILTER_STATE] = self.fresh_air_filter_state
        data[ATTR_FRESHAIRFILTER_LIST] = self.fresh_air_filter_list
        data[ATTR_SMARTSAVING_MODE] = self.smart_saving_mode
        data[ATTR_SMARTSAVING_STATE] = self.smart_saving_state
        data[ATTR_WATERFILTER_STATE] = self.water_filter_state
        data[ATTR_DOOR_STATE] = self.door_state
        data[ATTR_SMARTSAVING_STATE] = self.smart_saving_state
        data[ATTR_LOCKING_STATE] = self.locking_state
        data[ATTR_ACTIVESAVING_STATE] = self.active_saving_state
        return data

    @property
    def state(self):
        if self._state:
            return '켜짐'
        else:
            return '꺼짐'
            
    @property
    def current_reftemp(self):
        if self._state:
            return self._state.current_reftemp

    def set_ref_temperature(self, refrigerator_temperature):
        self._ref.set_reftemp(refrigerator_temperature)

    @property
    def current_freezertemp(self):
        if self._state:
            return self._state.current_freezertemp

    def set_freezer_temperature(self, freezer_temperature):
        self._ref.set_freezertemp(freezer_temperature)

    @property
    def ice_plus_list(self):
        return list(ICEPLUSMODES.values())

    @property
    def ice_plus_state(self):
        if self._state:
            mode = self._state.iceplus_state
            return ICEPLUSMODES[mode.name]

    def set_iceplus_mode(self, iceplus_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in ICEPLUSMODES.items()}

        mode = wideq.ICEPLUS[modes_inv[iceplus_mode]]
        self._ref.set_iceplus(mode)

    @property
    def fresh_air_filter_list(self):
        if self._state:
            mode = self._state.freshairfilter_state
            if mode.name in FRESHAIRFILTERMODES:
                return list(FRESHAIRFILTERMODES.values())
            elif mode.name in SMARTCAREMODES:
                return list(SMARTCAREMODES.values())

    @property
    def fresh_air_filter_state(self):
        if self._state:
            mode = self._state.freshairfilter_state
            if mode.name in FRESHAIRFILTERMODES:
                return FRESHAIRFILTERMODES[mode.name]
            elif mode.name in SMARTCAREMODES:
                return SMARTCAREMODES[mode.name]

    def set_fresh_air_filter_mode(self, freshairfilter_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in FRESHAIRFILTERMODES.items()}
        smartmodes_inv = {v: k for k, v in SMARTCAREMODES.items()}

        if freshairfilter_mode in modes_inv:
            mode = wideq.FRESHAIRFILTER[modes_inv[freshairfilter_mode]]
        elif freshairfilter_mode in smartmodes_inv:
            mode = wideq.FRESHAIRFILTER[smartmodes_inv[freshairfilter_mode]]
        self._ref.set_freshairfilter(mode)

    @property
    def smart_saving_mode(self):
        if self._state:
            data = self._state.smartsaving_mode
            if data == "@RE_SMARTSAVING_MODE_NIGHT_W":
                return 'NIGHT'
            elif data == "@RE_SMARTSAVING_MODE_CUSTOM_W":
                return 'CUSTOM'
            elif data == "@CP_TERM_USE_NOT_W":
                return 'OFF'
            else:
                return '지원안함'

    @property
    def water_filter_state(self):
        if self._state:
            data = self._state.waterfilter_state
            if data == '255':
                return 'NO FILTER'
            else:
                return data
    @property
    def door_state(self):
        if self._state:
            return self._state.door_state

    @property
    def smart_saving_state(self):
        if self._state:
            data = self._state.smartsaving_state
            if data == '255':
                return '지원안함'
            else:
                return self._state.smartsaving_state

    @property
    def locking_state(self):
        if self._state:
            return self._state.locking_state

    @property
    def active_saving_state(self):
        if self._state:
            data = self._state.activesaving_state
            if data == '255':
                return '지원안함'
            else:
                return data

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ref.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ref.monitor_start()
                self._ref.monitor_start()
                self._ref.delete_permission()
                self._ref.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ref.monitor_start()
                self._ref.monitor_start()
                self._ref.delete_permission()
                self._ref.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ref.monitor_start()
        self._ref.monitor_start()
        self._ref.delete_permission()
        self._ref.delete_permission()

# Air Purifier Main
class LGEAPDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name, model_type, celsius=True):
        """initialize a LGE Air Purifier Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._ap = wideq.APDevice(client, device)

        self._ap.monitor_start()
        self._ap.monitor_start()
        self._ap.delete_permission()
        self._ap.delete_permission()

        # The response from the monitoring query.
        self._state = None
        self._name = name
        self._type = model_type

        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type

    @property
    def supported_features(self):
        return (
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_SWING_MODE |
            SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        supported_features = self.supported_features
        data = {}
        data[ATTR_DEVICE_TYPE] = self.device_type
        data[ATTR_STATUS] = self.current_status
        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list
        if supported_features & SUPPORT_SWING_MODE:
            data[ATTR_SWING_MODE] = self.current_circulate_mode
            if self.circulate_list:
                data[ATTR_SWING_LIST] = self.circulate_list            
        data[ATTR_AIRREMOVAL_MODE] = self.is_airremoval_mode
        data[ATTR_CIRCULATEDIR_MODE] = self.is_circulatedir_mode
        data[ATTR_SIGNALLIGHTING_MODE] = self.is_signallighting_mode
        data[ATTR_AIRFAST_MODE] = self.is_airfast_mode
        data[ATTR_SENSORPM1] = self.sensorpm1
        data[ATTR_SENSORPM2] = self.sensorpm2
        data[ATTR_SENSORPM10] = self.sensorpm10
        data[ATTR_TOTALAIRPOLUTION] = self.total_air_polution
        data[ATTR_AIRPOLUTION] = self.air_polution
        data[ATTR_FILTER_STATE] = self.filter_state

        return data

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def current_status(self):
        if self.is_on == True:
            return 'ON'
        elif self.is_on == False:
            return 'OFF'

    def turn_on(self):
        LOGGER.info('Turning on...')
        self._ap.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._ap.set_on(False)
        LOGGER.info('...done.') 

    @property
    def operation_list(self):
        if self._model_name == 'AIR_910604_KR':
            return list(AP_AIR_910604_KR_MODES.values())
        else:
            return list(APMODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            if self._model_name == 'AIR_910604_KR':
                return AP_AIR_910604_KR_MODES[mode.name]
            else:
                return APMODES[mode.name]
            
    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in APMODES.items()}
        ap_air_910604_kr_modes_inv = {v: k for k, v in AP_AIR_910604_KR_MODES.items()}

        if self._model_name == 'AIR_910604_KR':
            mode = wideq.APOPMode[ap_air_910604_kr_modes_inv[operation_mode]]
        else:
            mode = wideq.APOPMode[modes_inv[operation_mode]]
        self._ap.set_mode(mode)

    @property
    def fan_list(self):
        if self._model_name == 'AIR_910604_KR':
            return list(AP_AIR_910604_KR_FANMODES.values())
        else:
            return list(APFANMODES.values())


    @property
    def current_fan_mode(self):
        if self._state:
            mode = self._state.windstrength_state
            if self._model_name == 'AIR_910604_KR':
                return AP_AIR_910604_KR_FANMODES[mode.name]
            else:
                return APFANMODES[mode.name]

    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in APFANMODES.items()}
        air_91604_kr_fanmodes_inv = {v: k for k, v in AP_AIR_910604_KR_FANMODES.items()}

        if self._model_name == 'AIR_910604_KR':
            mode = wideq.APWindStrength[air_91604_kr_fanmodes_inv[fan_mode]]
        else:
            mode = wideq.APWindStrength[fanmodes_inv[fan_mode]]
        self._ap.set_windstrength(mode)

    @property
    def circulate_list(self):
        if self._model_name == 'AIR_910604_KR':
            return '지원안함'
        else:
            return list(APCIRCULATEMODES.values())

    @property
    def current_circulate_mode(self):
        if self._state:
            if self._model_name == 'AIR_910604_KR':
                return '지원안함'
            else:
                mode = self._state.circulatestrength_state
            return APCIRCULATEMODES[mode.name]

    def set_swing_mode(self, circulate_mode):

        import wideq
        circulatemodes_inv = {v: k for k, v in APCIRCULATEMODES.items()}
        if self._model_name == 'AIR_910604_KR':
            return '지원안함'
        else:
            mode = wideq.APCirculateStrength[circulatemodes_inv[circulate_mode]]
        self._ap.set_circulatestrength(mode)

    @property
    def is_airremoval_mode(self):
        if self._state:
            mode = self._state.airremoval_state
            return APETCMODES[mode.name]
    
    def airremoval_mode(self, airremoval_mode):
        if airremoval_mode == '켜짐':
            self._ap.set_airremoval(True)
        elif airremoval_mode == '꺼짐':
            self._ap.set_airremoval(False)

    @property
    def is_circulatedir_mode(self):
        if self._state:
            if self._model_name == 'AIR_910604_KR':
                return '지원안함'
            else:
                mode = self._state.circulatedir_state
            return APETCMODES[mode.name]
    
    def circulatedir_mode(self, circulatedir_mode):
        if self._model_name == 'AIR_910604_KR':
            return '지원안함'
        else:
            if circulatedir_mode == '켜짐':
                self._ap.set_circulatedir(True)
            elif circulatedir_mode == '꺼짐':
                self._ap.set_circulatedir(False)

    @property
    def is_signallighting_mode(self):
        if self._state:
            if self._model_name == 'AIR_910604_KR':
                return '지원안함'
            else:
                mode = self._state.signallighting_state
            return APETCMODES[mode.name]

    @property
    def is_airfast_mode(self):
        if self._state:
            if self._model_name == 'AIR_910604_KR':
                mode = self._state.airfast_state
            else:
                return '지원안함'
            return APETCMODES[mode.name]
    
    def airfast_mode(self, airfast_mode):
        if self._model_name == 'AIR_910604_KR':
            if airfast_mode == '켜짐':
                self._ap.set_airfast(True)
            elif airfast_mode == '꺼짐':
                self._ap.set_airfast(False)
        else:
            return '지원안함'


    @property
    def filter_state(self):
        data = self._ap.get_filter_state()
        usetime = data['UseTime']
        changeperiod = data['ChangePeriod']
        use = int(usetime)/int(changeperiod)
        remain = (1 - use)*100

        if changeperiod == '0':
            return 'No Filter'
        else:
            return int(remain)

    @property
    def sensorpm1(self):
        if self._state:
            return self._state.sensorpm1

    @property
    def sensorpm2(self):
        if self._state:
            return self._state.sensorpm2


    @property
    def sensorpm10(self):
        if self._state:
            return self._state.sensorpm10

    @property
    def air_polution(self):
        if self._state:
            mode = self._state.air_polution
            return APSMELL[mode.name]
            
    @property
    def total_air_polution(self):
        if self._state:
            mode = self._state.total_air_polution
            return APTOTALAIRPOLUTION[mode.name]

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._ap.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._ap.monitor_start()
                self._ap.monitor_start()
                self._ap.delete_permission()
                self._ap.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._ap.monitor_start()
                self._ap.monitor_start()
                self._ap.delete_permission()
                self._ap.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._ap.monitor_start()
        self._ap.monitor_start()
        self._ap.delete_permission()
        self._ap.delete_permission()

# Dehumidifier Main
class LGEDEHUMDEVICE(LGEDevice, ClimateDevice):

    def __init__(self, client, device, name, model_type):
        """initialize a LGE Dehumidifer Device."""
        LGEDevice.__init__(self, client, device)

        import wideq
        self._dehum = wideq.DehumDevice(client, device)

        self._dehum.monitor_start()
        self._dehum.monitor_start()
        self._dehum.delete_permission()
        self._dehum.delete_permission()

        # The response from the monitoring query.
        self._state = None

        self._transient_hum = None
        self._transient_time = None
        self._name = name
        self._type = model_type

        self.update()

    @property
    def name(self):
    	return self._name

    @property
    def device_type(self):
        return self._type

    @property
    def supported_features(self):
        return (
            SUPPORT_TARGET_HUMIDITY |
            SUPPORT_TARGET_HUMIDITY_HIGH |
            SUPPORT_TARGET_HUMIDITY_LOW |
            SUPPORT_OPERATION_MODE |
            SUPPORT_FAN_MODE |
            SUPPORT_ON_OFF
        )

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {}
        data[ATTR_AIRREMOVAL_MODE] = self.is_airremoval_mode
        data[ATTR_STATUS] = self.current_status

        if self.target_humidity_step is not None:
            data[ATTR_TARGET_HUMIDITY_STEP] = self.target_humidity_step
            
        supported_features = self.supported_features
        if supported_features & SUPPORT_FAN_MODE:
            data[ATTR_FAN_MODE] = self.current_fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        if supported_features & SUPPORT_OPERATION_MODE:
            data[ATTR_OPERATION_MODE] = self.current_operation
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        if supported_features & SUPPORT_TARGET_HUMIDITY:
            data[ATTR_HUMIDITY] = self.target_humidity
            data[ATTR_CURRENT_HUMIDITY] = self.current_humidity

        if supported_features & SUPPORT_TARGET_HUMIDITY_LOW:
            data[ATTR_MIN_HUMIDITY] = self.min_humidity

        if supported_features & SUPPORT_TARGET_HUMIDITY_HIGH:
            data[ATTR_MAX_HUMIDITY] = self.max_humidity

        return data

    @property
    def is_on(self):
        if self._state:
            return self._state.is_on

    @property
    def current_status(self):
        if self._state.is_on == True:
            return 'ON'
        elif self._state.is_on == False:
            return 'OFF'

    def turn_on(self):
        LOGGER.info('Turning on...')
        self._dehum.set_on(True)
        LOGGER.info('...done.')
        
    def turn_off(self):
        LOGGER.info('Turning off...')
        self._dehum.set_on(False)
        LOGGER.info('...done.') 


    @property
    def operation_list(self):
        return list(DEHUMMODES.values())

    @property
    def current_operation(self):
        if self._state:
            mode = self._state.mode
            return DEHUMMODES[mode.name]
            
    def set_operation_mode(self, operation_mode):
        import wideq

        # Invert the modes mapping.
        modes_inv = {v: k for k, v in DEHUMMODES.items()}

        mode = wideq.DEHUMOPMode[modes_inv[operation_mode]]
        self._dehum.set_mode(mode)

    @property
    def fan_list(self):
        return list(DEHUMFANMODES.values())

    @property
    def current_fan_mode(self):
        if self._state:
            mode = self._state.windstrength_state
            return DEHUMFANMODES[mode.name]
                    
    def set_fan_mode(self, fan_mode):
        import wideq
        # Invert the modes mapping.
        fanmodes_inv = {v: k for k, v in DEHUMFANMODES.items()}

        mode = wideq.DEHUMWindStrength[fanmodes_inv[fan_mode]]
        self._dehum.set_windstrength(mode)

    @property
    def is_airremoval_mode(self):
        if self._state:
            mode = self._state.airremoval_state
            return DEHUMAIRREMOVALMODES[mode.name]
    
    def airremoval_mode(self, airremoval_mode):
        if airremoval_mode == '켜짐':
            self._dehum.set_airremoval(True)
        elif airremoval_mode == '꺼짐':
            self._dehum.set_airremoval(False)

    @property
    def min_humidity(self):
        return HUM_MIN

    @property
    def max_humidity(self):
        return HUM_MAX
        
    @property
    def target_humidity_step(self):
        return HUM_STEP

    @property
    def current_humidity(self):
        if self._state:
            return self._state.current_humidity

    @property
    def target_humidity(self):
        if self._state:
            return self._state.target_humidity
                               
    def set_humidity(self, humidity):

        LOGGER.info('Setting humidity to %s...', humidity)
        self._dehum.set_humidity(humidity)

        LOGGER.info('humidity set.')

    def update(self):

        import wideq

        LOGGER.info('Updating %s.', self.name)
        for iteration in range(MAX_RETRIES):
            LOGGER.info('Polling...')

            try:
                state = self._dehum.poll()
            except wideq.NotLoggedInError:
                LOGGER.info('Session expired. Refreshing.')
                self._client.refresh()
                self._dehum.monitor_start()
                self._dehum.monitor_start()
                self._dehum.delete_permission()
                self._dehum.delete_permission()

                continue

            if state:
                LOGGER.info('Status updated.')
                self._state = state
                self._client.refresh()
                self._dehum.monitor_start()
                self._dehum.monitor_start()
                self._dehum.delete_permission()
                self._dehum.delete_permission()
                return

            LOGGER.info('No status available yet.')
            time.sleep(2 ** iteration)

        # We tried several times but got no result. This might happen
        # when the monitoring request gets into a bad state, so we
        # restart the task.
        LOGGER.warn('Status update failed.')

        self._dehum.monitor_start()
        self._dehum.monitor_start()
        self._dehum.delete_permission()
        self._dehum.delete_permission()
