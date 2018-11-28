import time
from lib.dth import DTH
from machine import Pin
import lib.logging as logging

log = logging.getLogger("Sensor")
SENSOR_TYPES = ['Temperature', 'GPS', 'Boolean']
TEMPERATURE_SENSORS = ['internal', 'dth11']
GPS_SENSORS = []
BOOLEAN_SENSORS = []

class Sensor():

    def __init__(self, name, type, model, pins=0):
        self.name = name
        self.type = type
        self.model = model
        self.pins = pins
        self.value = None

    def print_info(self):
        print ("Name: {}, Type: {}, Model: {}, Pins: {}".format(self.name, self.type, self.model, self.pins))

    def get_value(self):
        if self.type not in SENSOR_TYPES:
            return False
        if self.type == 'Temperature': # Temperature
            if self.model not in TEMPERATURE_SENSORS:
                log.error()
            if self.model == 'dth11':
                power_pin_set()
                ground_pin_set()
                self.value = temperature_sensor_read_data()
            if self.model == 'internal': # Internal value required
                import machine
                self.value = machine.temperature()

        elif self.type == 'GPS':
            self.value = "No GPS support yet"
        elif self.type == 'Boolean':
            self.value = "No Boolean support yet"

    def power_pin_set(self):
        p_VCC = Pin(self.pin[1], mode=Pin.OUT)
        p_VCC.value(1)

    def ground_pin_set(self):
        p_GND = Pin(self.pin[0], mode=Pin.OUT)
        p_GND.value(0)

    def temperature_sensor_read_data(self):
        th = DTH(Pin(self.pin[2], mode=Pin.OPEN_DRAIN),0)
        result = th.read()
        if result.is_valid():
            value = "{\"Temperature\":%dC, \"Humidity\":%d}" % (result.temperature result.humidity)
            return value
