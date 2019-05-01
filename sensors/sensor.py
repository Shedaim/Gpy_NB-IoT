import time
import logging
import messages
from sensors.dth import DTH
from sensors.pyb_gpio_lcd import GpioLcd
from machine import Pin
from sensors.pytrack import Pytrack
from sensors.onewire import OneWire, DS18X20

log = logging.getLogger("Sensor")

# Internal CPU temperature - No pins - Shows temperature in Farenheit.
INTERNAL_CPU_TEMPERATURE = "cpu_temp"
# DTH11 - Temperature and Humidity sensor - Requires Ground, VCC and data Pins
DTH11 = 'dth11'
# REED - Reed switch for Door opening - Requires Ground, VCC and data Pins
REED = 'reed'
# LCD display - Show message sent by remote server
LCD_1602a = '1602a'
VIBRATOR = 'vibrator'
# Location from Pytrack development board
PYTRACK = 'pytrack'
DS18X20_MODEL = 'ds18x20'
PASSIVE_BUZZER = 'passive_buzzer'
ACTIVE_DUAL_BEAM_IR = 'abt_100'

SENSOR_MODELS = {DTH11: ['Temperature', 'Humidity'],
                 REED: ['Alarm'],
                 INTERNAL_CPU_TEMPERATURE: ['Temperature'],
                 LCD_1602a: ['lcd'],
                 VIBRATOR: ['vibrator'],
                 PYTRACK: ['latitude', 'longitude'],
                 DS18X20_MODEL: ['Temperature'],
                 PASSIVE_BUZZER: ['buzzer'],
                 ACTIVE_DUAL_BEAM_IR: ['fence']
                 }

class Sensor:

    def __init__(self, name, model, pins: []):
        self.name = name
        self.model = model
        self.pins = pins
        self.value = None
        self.type = None
        self.get_types()
        self.ue = None

    def get_types(self):
        try:
            self.type = SENSOR_MODELS[self.model]
        except AttributeError:
            log.exception("Sensor model not found.")

    def print_info(self):
        print("Name: {}, Type: {}, Model: {}, Pins: {}".format(self.name, self.type, self.model, self.pins))

    def power_pin_set(self):
        p_vcc = Pin(self.pins[1], mode=Pin.OUT)
        p_vcc.value(1)

    def ground_pin_set(self):
        p_gnd = Pin(self.pins[0], mode=Pin.OUT)
        p_gnd.value(0)

    def temperature_sensor_read_data(self):
        th = DTH(Pin(self.pins[2], mode=Pin.OPEN_DRAIN), 0)
        time.sleep(1)
        result = th.read()
        if result.is_valid():
            value = [result.temperature, result.humidity]
            while value is None:
                time.sleep(0.2)
            log.info("Reading sensor {0} values: {1}".format(self.name, str(value)))
            return value
        else:
            result = result.get_error_data()
            log.warning("Could not extract data from sensor: " + self.name
             + "\n Error data: " + result)

    def door_state_interrupt(self, arg):
        if arg():
            value = 1
        else:
            value = 0
        data = {'_'.join(['Alarm', self.name]): value}
        log.info("Door state has changed. Sending alarm.")
        if self.ue.config.mqtt is not None:
            messages.send_sensors_via_mqtt(self.ue, alarm=True, data=data)
        elif self.ue.config.http is not None:
            messages.send_sensors_via_http(self.ue, alarm=True, data=data)

    def door_sensor_read_data(self):
        p_Data = Pin(self.pins[2], mode=Pin.IN, pull=Pin.PULL_UP)
        p_Data.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, self.door_state_interrupt)

    def get_value(self):
        if self.model == DTH11:
            self.power_pin_set()
            self.ground_pin_set()
            self.value = self.temperature_sensor_read_data()
        elif self.model == INTERNAL_CPU_TEMPERATURE:  # Internal value required
            import machine
            self.value = machine.temperature()
        elif self.model == REED:
            pass  # Nothing to do
        elif self.model == PYTRACK:
            py = Pytrack();
            self.value = py.get_location()
        elif self.model == DS18X20_MODEL:
            ow = OneWire(Pin(self.pins[0]))
            temp = DS18X20(ow)
            temp.start_conversion()
            time.sleep(1)
            self.value = temp.read_temp_async()
        elif self.model == ACTIVE_DUAL_BEAM_IR:
            if self.pins.value():
                self.value = "obscured"
            else:
                self.value = "clear"
        return self.value

    def fence(self, arg):
        if arg():
            value = 1
        else:
            value = 0
        data = {'Fence': 'triggered'}
        messages.send_sensors_via_mqtt(self.ue, alarm=True, data=data)
        log.info("Fence state changed")

    def start_sensor(self, ue):
        self.ue = ue
        if self.model == REED:
            self.value = 0
            self.power_pin_set()
            self.ground_pin_set()
            self.door_sensor_read_data()
        elif self.model == ACTIVE_DUAL_BEAM_IR:
            log.info("starting fence sensor")
            self.pins = Pin(self.pins[0], mode=Pin.IN)
            self.pins.callback(Pin.IRQ_RISING, self.fence)

    def initiate_lcd(self):
        self.lcd = GpioLcd(rs_pin=Pin(self.pins[0], mode=Pin.OUT),
                      enable_pin=Pin(self.pins[1], mode=Pin.OUT),
                      d0_pin=Pin(self.pins[2], mode=Pin.OUT),
                      d1_pin=Pin(self.pins[3], mode=Pin.OUT),
                      d2_pin=Pin(self.pins[4], mode=Pin.OUT),
                      d3_pin=Pin(self.pins[5], mode=Pin.OUT),
                      d4_pin=Pin(self.pins[6], mode=Pin.OUT),
                      d5_pin=Pin(self.pins[7], mode=Pin.OUT),
                      d6_pin=Pin(self.pins[8], mode=Pin.OUT),
                      d7_pin=Pin(self.pins[9], mode=Pin.OUT),
                      backlight_pin=Pin(self.pins[10], mode=Pin.OUT),
                      num_lines=2, num_columns=16)
        self.alarm = False

    def alarm_to_lcd(self, value):
        self.alarm = True
        self.lcd.clear()
        self.lcd.hal_backlight_on()
        self.lcd.display_on()
        self.lcd.putstr(value)

    def invert_display_state(self):
        assert isinstance(self.lcd, GpioLcd), "Invert display called before initialization"
        if self.lcd.display:
            self.lcd.hal_backlight_off()
            self.lcd.display_off()
        else:
            self.lcd.display_on()
            self.lcd.hal_backlight_on()

    def start_vibrator(self):
        self.pins.value(1)

    def stop_vibrator(self):
        self.pins.value(0)

    def start_buzzer(self):
        self.pins.value(1)
        time.sleep(5)
        self.pins.value(0)
