#! usr/bin/python
#coding=utf-8
"""
Support for baidu travel time sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.baidu_travel_time/
0：默认
3：不走高速
4：高速优先
5：躲避拥堵
6：少收费
7：躲避拥堵&高速优先
8：躲避拥堵&不走高速
9：躲避拥堵&少收费
10：躲避拥堵&不走高速&少收费
11：不走高速&少收费
"""
import logging
from homeassistant.const import (
    CONF_API_KEY, CONF_NAME, ATTR_ATTRIBUTION, CONF_ID
    )
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import json
import urllib
import urllib.request
import urllib.parse
import time
_Log=logging.getLogger(__name__)
CONF_ORIGIN = 'origin'
CONF_ORIGIN_REGION = 'origin_region'
CONF_DESTINATION = 'destination'
CONF_DESTINATION_REGION = 'destination_region'
CONF_TACTICS = 'tactics'
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_TACTICS): cv.positive_int
})
TRAFFIC_STATUS = {
0: "无路况",
1: "畅通",
2: "缓行",
3: "拥堵",
4: "非常拥堵"
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    origin = config.get(CONF_ORIGIN)
    destination = config.get(CONF_DESTINATION)
    tactics = config.get(CONF_TACTICS)

    ak = config.get(CONF_API_KEY,None)
    sensor_name = config.get(CONF_NAME)
    if ak == None:
        _Log.error('Pls enter api_key!')
        return False

    add_devices([baiduTravelSensor(hass,sensor_name,origin,destination,ak,tactics)])

class baiduTravelSensor(Entity):
    """Representation of a Sensor."""


    def __init__(self,hass,sensor_name,origin,destination,ak,tactics):
        self.attributes = {}
        self._state = None
        self._name = sensor_name
        self._hass = hass
        self._origin = origin
        self._destination = destination
        self._ak = ak
        self._tactics = tactics





    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "min"

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        origin_state = self._hass.states.get(self._origin)
        destination_state = self._hass.states.get(self._destination)
        origin_latitude = origin_state.attributes.get('latitude')
        origin_longitude = origin_state.attributes.get('longitude')
        destination_latitude = destination_state.attributes.get('latitude')
        destination_longitude = destination_state.attributes.get('longitude')
        geocoding = {'tactics': self._tactics,
                             'origin' : str(origin_latitude)+','+str(origin_longitude),
                             'destination' : str(destination_latitude)+','+str(destination_longitude),
                             'ak' : self._ak,
                             }
        geocoding =  urllib.parse.urlencode(geocoding)
        ret = urllib.request.urlopen("%s?%s" % ("http://api.map.baidu.com/direction/v2/driving", geocoding))
        if ret.status != 200:
            _Log.error('http get data Error StatusCode:%s' % ret.status)
            return
        res = ret.read().decode('utf-8')
        json_obj = json.loads(res)
        if not 'result' in json_obj:
            _Log.error('Json Status Error1!')
            _Log.error(str(geocoding))
            return
        if json_obj['status'] != 0:
            _Log.error('baidu_travel_time_v3:error_status'+json_obj['status'])
            return
        step = json_obj['result']['routes'][0]['steps']
        timecost = json_obj['result']['routes'][0]['duration']
        timecost = str(int(timecost)//60)
        road_dict = {}
        for i in range(len(step)):
            status = step[i]['traffic_condition'][0]['status']
            if status in TRAFFIC_STATUS:
                traffic_status = TRAFFIC_STATUS[status]
            else:
                traffic_status  = '未知'
            road_dict[i] = step[i]['road_name'] + ':' + traffic_status
        attr_dict = {}

        for key,value in road_dict.items():
            attr_dict[str(key)] = value
        self.attributes = attr_dict
        self._state = timecost
