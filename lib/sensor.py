SENSOR_TYPES = ['Temperature', 'GPS', 'Boolean']
class Sensor():

    def __init__(self, name, type, pins=0):
        self.name = name
        self.type = type
        self.pins = pins
        self.value = None

    def print_info(self):
        print ("Name: {}, Type: {}, Pins: {}".format(self.name, self.type, self.pins))

    def get_value(self):
        if self.type not in SENSOR_TYPES:
            return False
        if self.type == 'Temperature': # Temperature
            if self.pins == 0: # Internal value required
                import machine
                self.value = machine.temperature()
            else:
                pass # Read data from external sensor
        elif self.type == 'GPS':
            self.value = "No GPS support yet"
        elif self.type == 'Boolean':
            self.value = "No Boolean support yet"
