import time
import lib.logging as logging
from lib.dth import DTH
from machine import Pin

log = logging.getLogger("Sensor")
SENSOR_MODELS = {'dth11':['Temperature','Humidity']}

# Internal CPU temperature - No pins - Shows temperature in Farenheit.
INTERNAL_CPU_TEMPERATURE = "cpu_temp"
# DTH11 - Temperature and Humidity sensor - Requires Ground, VCC and data Pins
DTH11 = 'dth11'

class Sensor():

    def __init__(self, name, model, pins=0):
        self.name = name
        self.model = model
        self.pins = pins
        self.value = None
        self.get_types()

    def get_types(self):
        try:
            self.type = SENSOR_MODELS[self.model]
        except AttributeError:
            log.exception("Sensor model not found.")

    def print_info(self):
        print ("Name: {}, Type: {}, Model: {}, Pins: {}".format(self.name, self.type, self.model, self.pins))

    def power_pin_set(self):
        p_VCC = Pin(self.pins[1], mode=Pin.OUT)
        p_VCC.value(1)

    def ground_pin_set(self):
        p_GND = Pin(self.pins[0], mode=Pin.OUT)
        p_GND.value(0)

    def temperature_sensor_read_data(self):
        th = DTH(Pin(self.pins[2], mode=Pin.OPEN_DRAIN),0)
        time.sleep(1)
        result = th.read()
        if result.is_valid():
            value = [result.temperature, result.humidity]
            while value is None:
                time.sleep(0.2)
            log.info("got sensor values: " + str(value))
            return value
        else:
            log.warning("Could not extract data from sensor: " + self.name)

    def get_value(self):
        if self.model == DTH11:
            self.power_pin_set()
            self.ground_pin_set()
            self.value = self.temperature_sensor_read_data()
        if self.model == INTERNAL_CPU_TEMPERATURE: # Internal value required
            import machine
            self.value = machine.temperature()
        elif self.type == 'GPS':
            self.value = "No GPS support yet"
        elif self.type == 'Boolean':
            self.value = "No Boolean support yet"
