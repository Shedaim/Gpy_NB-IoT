import time
import lib.logging as logging
from lib.dth import DTH
from main import send_sensors_via_http
from machine import Pin

log = logging.getLogger("Sensor")

# Internal CPU temperature - No pins - Shows temperature in Farenheit.
INTERNAL_CPU_TEMPERATURE = "cpu_temp"
# DTH11 - Temperature and Humidity sensor - Requires Ground, VCC and data Pins
DTH11 = 'dth11'
# REED - Redd switch for Door opening - Requires Ground, VCC and data Pins
REED = 'reed'

SENSOR_MODELS = {DTH11:['Temperature','Humidity'], REED:['Boolean'], INTERNAL_CPU_TEMPERATURE:['Temperature']}

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


    def external_interrupts(arg):
        if arg():
            log.info("The Door is Open!!")
            send_sensors_via_http(alarm=True, {self.type:1})
        else:
            log.info("The Door is Closed!!")
            send_sensors_via_http(alarm=True, {self.type:0})


    def door_sensor_read_data(self):
        p_Data = Pin(self.pins[2], mode=Pin.IN, pull=Pin.PULL_UP)
        p_Data.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, self.external_interrupts)

    def get_value(self):
        if self.model == DTH11:
            self.power_pin_set()
            self.ground_pin_set()
            self.value = self.temperature_sensor_read_data()
        if self.model == INTERNAL_CPU_TEMPERATURE: # Internal value required
            import machine
            self.value = machine.temperature()
        if self.model == REED:
            self.power_pin_set()
            self.ground_pin_set()
            self.door_sensor_read_data()
        if self.type == 'GPS':
            self.value = "No GPS support yet"
        if self.type == 'Boolean':
            self.value = "No Boolean support yet"
