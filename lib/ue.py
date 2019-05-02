import logging
import ujson
import networking.wifi as wifi
from networking.network_iot import LTENetwork
from machine import Pin
from sim import Sim
from networking.remoteserver import RemoteServer
from sensors.sensor import Sensor
from sensors.button import Button
from variable_functions import list_string_to_list
import validate
from time import sleep
import messages

log = logging.getLogger("UE")

DEFAULT_UPLOAD_FREQUENCY = 10
DEFAULT_NAME = "PycomDevice"

# Modes of operation
TELEMTRY_MODE = 1
HTTP_RELAY_MODE = 2
WARNING_MODE_ONLY = 3


class UE:

    def __init__(self):
        self.sim = Sim()
        self.button = None
        self.lte = None
        self.wifi = None
        self.bt = None
        self.sensors = set()
        self.token = None
        self.remote_server = None
        self.attributes = {'uploadFrequency': DEFAULT_UPLOAD_FREQUENCY,
                           'deviceName': DEFAULT_NAME}
        self.shared_attributes = ['sharedKeys']
        self.client_attributes = None
        self.server_attributes = None
        self.config_message = False
        self.operation_mode = TELEMTRY_MODE

        self.__post_init__()

    def __post_init__(self):
        self.get_config(initial=True)
        sleep(2)
        # Wait untill initial configuration has been updated
        self.start_sensors()
        self.sim.get_sim_details(self.lte.lte)
        self.start_operation_mode()

    # Create HTTP message to download configurations or read from saved file
    def get_config(self, initial=False):
        if initial is True:
            with open('Initial_configuration.json', 'r') as f:
                result = f.read()
            dictionary = ujson.loads(result)
            # Get token on first time
            try:
                if validate.is_valid_string(dictionary['Token'], 'token'):
                    self.token = dictionary['Token']
                    del dictionary['Token']
                else:
                    log.error("Token input is not valid")
            except AttributeError:
                log.exception("Could not read 'token' from configuration file.")
            log.info('Read initial configuration: ' + result)
        else:
            # TODO Get all attributes
            dictionary = dict()
        self.turn_dict_to_config(dictionary)

    # Convert dictionary to specific object configurations
    def turn_dict_to_config(self, dictionary):
        if "shared" in dictionary.keys():
            assert isinstance(dictionary["shared"], dict), \
                              "shared attributes recieved not as a dictionary"
            for attr in dictionary["shared"]:
                self.value_to_config(attr, dictionary["shared"][attr])
            del dictionary['shared']
        for key in dictionary:
            self.value_to_config(key, dictionary[key])

    def value_to_config(self, key, val):
        log.info("Updating attribute '{0}' to value '{1}'".format(key, val))

        if key == "deviceName":
            if validate.is_valid_string(val, 'name'):
                self.attributes["deviceName"] = val
            else:
                log.error("Device Name input is not valid, using default name")
                self.attributes["deviceName"] = DEFAULT_NAME

        elif key == "uploadFrequency":
            if validate.is_valid_type(val, "int"):
                self.attributes["uploadFrequency"] = int(val)
            else:
                log.error("Upload Frequency input is not valid, \
                using default value")
                self.attributes["uploadFrequency"] = DEFAULT_UPLOAD_FREQUENCY
            # NEED to add implementation of sleep (eDRX?)

        elif key == "remoteServer":
            if validate.is_valid_remote_server(val):
                # Data in the form 'Protocol:IP:port'
                self.config_remote(val.split(":"))
            else:
                log.error("Remote Server input is not valid, " \
                "using default values")
                from networking.remoteserver import DEFAULT_REMOTE_SERVER
                self.config_remote(DEFAULT_REMOTE_SERVER)

        elif key == "LTE":
            if validate.is_valid_lte_bands(val):
                if self.lte is None:
                    self.lte = LTENetwork(bands=val)
                else:
                    self.lte.bands = val
            else:
                log.error("LTE bands input is not valid." \
                "Bands were not updated.")

        elif key == "WIFI":
            if validate.is_valid_wifi(val):
                if self.wifi is not None:
                    self.wifi = None
                self.config_wifi(val)
            else:
                log.error("WIFI configuration is not valid." \
                "WIFI configuration was not updated.")

        elif key == "BT":
            self.bt = True
            pass  # TODO to parse variables.

        elif key == "Sensors":
            if validate.is_valid_sensor(val):
                for sensor in val:
                    self.config_sensor(sensor.split(','))
            else:
                log.error("Sensors input is not valid. Sensors not configured.")

        elif key == "Button":
            self.button = Button(val[0], val[1:])
            self.button.pin.callback(Pin.IRQ_RISING, self.button_pressed)

        elif key == "operation_mode":
            if validate.is_valid_operation_mode(val):
                self.operation_mode = val
            else:
                self.operation_mode = TELEMTRY_MODE

        elif key == 'sharedKeys':
            self.shared_attributes = list_string_to_list(val)

        elif key == 'clientKeys':
            self.client_attributes = list_string_to_list(val)

        elif key == 'serverKeys':
            self.server_attributes = list_string_to_list(val)

        elif key == 'alarm_message':
            # TODO - display alarm only on required sensors
            for s in self.sensors:
                if 'lcd' in s.type:
                    s.alarm_to_lcd(val)
                if 'vibrator' in s.type:
                    s.start_vibrator()
                if 'buzzer' in s.type:
                    s.start_buzzer()
        else:
            log.warning("Key '{0}' does not match any configure key." \
            .format(key))

    def start_operation_mode(self, operation_mode):
        if operation_mode == 1:
            self.start_lte()
            self.start_mqtt()
            # AS long as the device is connected to the LTE network,
            # send telemetry
            while self.lte.lte.isconnected():
                if self.remote_server.mqtt is not None:
                    self.send_telemetry_mqtt()
                    self.remote_server.mqtt.check_msg()
                elif self.remote_server.http is not None:
                    pass
                    # TODO - add HTTP support for telemetry communication
                sleep(self.attributes['uploadFrequency'])
        elif operation_mode == 2:
            pass

        elif operation_mode == 3:
            self.start_lte()
            self.start_mqtt()
            while self.lte.lte.isconnected():
                if self.remote_server.mqtt is not None:
                    self.start_mqtt()
                    self.remote_server.mqtt.wait_msg()
                elif self.remote_server.http is not None:
                    pass
                    # TODO - add HTTP support for telemetry communication
        # Restart op_mode if disconnected
        self.start_operation_mode(self.operation_mode)

    def start_lte(self):
        if self.lte and self.sim.iccid:
            self.lte.initialize_lte()
            self.lte.lte_connect_procedure()
            sleep(1)  # Making sure we wait a second before sending data
        else:
            log.error("LTE start was unsuccessful.")

    def start_mqtt(self):
        if self.remote_server.mqtt.sock is not None:
            try:
                self.mqtt.disconnect()
            except OSError:
                log.debug("MQTT object failed to disconnect.")
        self.remote_server.mqtt.set_callback(_callback_message_to_config)
        log.info("Running mqtt first time")
        self.remote_server.initialize_mqtt(self.attributes["uploadFrequency"] * 3)
        # Initial configuration - ask for shared attributes
        messages.request_attributes(self.remote_server, self.client_attributes,
                                    self.server_attributes, self.shared_attributes)
        self.remote_server.mqtt.wait_msg()
        # Get shared attributes for initial configuration
        messages.request_attributes(self.remote_server, self.client_attributes,
                                    self.server_attributes, self.shared_attributes)
        self.remote_server.mqtt.wait_msg()

    def send_telemetry_mqtt(self):
        log.info("Trying to send sensor")
        messages.send_sensors_via_mqtt(self)

    # Config the remote server details given configuration data
    def config_remote(self, data):
        protocol = data[0]
        ip = data[1]
        port = int(data[2])
        self.remote_server = RemoteServer(protocol, ip, port, self.token)

    # Config the Wifi module
    def config_wifi(self, data):
        # 0 - mode         # 1 - ssid                       # 2 - password
        # 3 - channel      # 4 - antenna pin or internal    # 5 - Default GW
        # 6 - GW subnet    # 7 - ip address                 # 8 - subnet
        try:
            self.wifi = wifi.WIFI(data[0], data[1],
             (wifi.WLAN_WPA2, data[2]), data[3], data[4])
            if data[0] == wifi.WLAN_AP:  # WiFi in AP mode
                self.wifi.ip_configuration(data[5], data[6])
            else:  # WiFi in Station mode
                self.wifi.ip_configuration(data[5], data[6],
                 data[0], data[7], data[8])
        except AttributeError:
            log.exception("WiFi configuration is wrong.")

    # Config a sensor given it's configuration data
    def config_sensor(self, data):
        # Name, Model, Pins
        # Pins = 0 --> internal sensor
        # Pins = [Ground, VCC, Data]
        for sensor in self.sensors:
            # Sensor already configured.
            if (sensor.name == data[0] and sensor.model == data[1] and
                    sensor.pins == data[2:]):
                log.info("Sensor {0} already exists. No changes done."
                         .format(sensor.name))
                return
            # Sensor already configured but changes need to be done.
            # Found sensor with the same name but different configuration.
            elif sensor.name == data[0]:
                log.warning("Sensor with the same name ({0}), already exists," \
                "changing sensor values.".format(sensor.name))
                self.delete_sensor(data[0])  # Delete old sensor details
                self.add_sensor(data[0], data[1], data[2:])
                return
        # No similar sensor found.
        self.add_sensor(data[0], data[1], data[2:])

    # Function used to configure a new sensor
    def add_sensor(self, name, model, pins: []):
        assert isinstance(pins, list), "Pins are not of type list"
        sensor = Sensor(name, model, pins)
        self.sensors.add(sensor)
        log.info("Sensor {0} added successfully.".format(name))

    # Function used to remove an old sensor - Also used if sensor's type
    # or pins need to change, as there is no update_sensor method
    def delete_sensor(self, name):
        for sensor in self.sensors:
            if sensor.name == name:
                self.sensors.remove(sensor)
                log.info("Sensor {0} removed successfully.".format(name))
                return
        log.info("Sensor {0} not found.".format(name))

    # Create a list containing important data -
    # Used if data is needed to be sent to server/database
    def create_info_list(self):
        info_list = [self.imei, self.iccid, self.imsi, self.ip]
        info_list.extend(self.cell.create_info_list())
        return info_list

    # Return True if there is an "alarm" sensor configured
    def has_alarms(self):
        for sensor in self.config.sensors:
            if "Alarm" in sensor.type:
                return True
        return False

    # Some sensors must be initiated
    def start_sensors(self):
        for sensor in self.sensors:
            if "Alarm" in sensor.type:
                sensor.start_sensor(self)
            elif "vibrator" in sensor.type:
                sensor.pins = Pin(sensor.pins[0], mode=Pin.OUT)
                sensor.pins.value(0)
            elif "lcd" in sensor.type:
                sensor.initiate_lcd()
            elif "buzzer" in sensor.type:
                sensor.pins = Pin(sensor.pins[0], mode=Pin.OUT)
                sensor.pins.value(0)
            elif "fence" in sensor.type:
                sensor.start_sensor(self)

    def button_pressed(self, arg):
        log.info("Button pressed.")
        if arg():
            if "vibrator" in self.button.controls:
                vibrators = [sensor for sensor in self.sensors if "vibrator" in sensor.type]
            if "lcd" in self.button.controls:
                lcds = [sensor for sensor in self.sensors if "lcd" in sensor.type]
            for sensor in vibrators:
                sensor.stop_vibrator()
            for sensor in lcds:
                # Dont turn off display if an alarm just occurred
                if not sensor.alarm:
                    sensor.invert_display_state()
                else:
                    sensor.alarm = False

    # Prints UE static information: IMEI, IMSI, CCID.
    def print_info(self):
        print("---------------UE information----------------")
        print("IMEI: " + self.lte.lte.imei())
        if self.sim.iccid and self.sim.imsi:  # SIM card was found
            print("ICCID: " + self.sim.iccid)
            print("IMSI: " + self.sim.imsi)
        else:
            log.exception("Error while printing SIM details.")
        print('---------------------------------------------')

    # Print all available sensors configured
    def print_sensors_info(self):
        for sensor in self.config.sensors:
            sensor.print_info()

    # Helper function to easily ping a remote server.
    def ping(self, ip):
        self.p('AT!="IP::ping {0}"'.format(ip))


def _callback_message_to_config(topic, message):
    from main import this_device as ue
    remote = ue.remote_server
    message = message.decode('UTF-8')
    topic = topic.decode('UTF-8')
    log.info("Recieved message {1} to topic {0}".format(topic, message))
    ue.turn_dict_to_config(ujson.loads(message))
    if ue.remote_server != remote:
        if ue.remote_server.mqtt is not None: # Server is communicating via MQTT
            ue.remote_server.mqtt.set_callback(_callback_message_to_config)
            ue.remote_server.initialize_mqtt(ue.attributes["uploadFrequency"] * 3)
    # We successfully recieved one message, check if another is waiting.
    ue.remote_server.mqtt.check_msg()
