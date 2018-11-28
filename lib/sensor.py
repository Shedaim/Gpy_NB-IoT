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

    def power_pin_set(self):
        p_VCC = Pin(self.pins[1], mode=Pin.OUT)
        p_VCC.value(1)

    def ground_pin_set(self):
        p_GND = Pin(self.pins[0], mode=Pin.OUT)
        p_GND.value(0)

    def temperature_sensor_read_data(self):
        th = DTH(Pin(self.pins[2], mode=Pin.OPEN_DRAIN),0)
        result = th.read()
        if result.is_valid():
            value = str({"Temperature":str(result.temperature) + "C", "Humidity":result.humidity})
            while True:
                try:
                    t = self.value
                    break
                except NameError:
                    pass
            return value

    def get_value(self):
        if self.type not in SENSOR_TYPES:
            log.error("Sensor type undefined.")
            return False
        if self.type == 'Temperature': # Temperature
            if self.model not in TEMPERATURE_SENSORS:
                log.error("Sensor model undefined.")
                return False
            if self.model == 'dth11':
                self.power_pin_set()
                self.ground_pin_set()
                self.value = self.temperature_sensor_read_data()
            if self.model == 'internal': # Internal value required
                import machine
                self.value = machine.temperature()

        elif self.type == 'GPS':
            self.value = "No GPS support yet"
        elif self.type == 'Boolean':
            self.value = "No Boolean support yet"
