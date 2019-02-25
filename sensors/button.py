from machine import Pin

class Button:

    def __init__(self, pin, controls: []):
        self.pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.controls = controls
