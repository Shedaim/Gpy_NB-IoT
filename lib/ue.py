import re
import lib.logging as logging
from network import LTE
from lib.network_iot import Cell
from lib.configuration import Configuration
from time import sleep
from lib.wifi import WLAN_AP

log = logging.getLogger("UE")


class UE:

    def __init__(self):
        self.lte = LTE()
        self.imei = self.lte.imei()
        self.ip = None
        self.sim = False
        self.imsi = None
        self.iccid = None
        self.cell = Cell(self.lte)
        self.config = Configuration()
        self.config.get_config(initial=True)
        self.alarms = False
        self.sensors_dict = None

    # Used to check connectivity status of the ue to an external destination
    def isconnected(self):
        if self.config.lte:  # LTE is configured --> primary connection
            if self.lte.isconnected() is True:  # LTE connected
                return True
            else:
                return False
        # Check if wifi is configured on Access-Point mode
        elif self.config.wifi is not None and self.config.wifi.mode == WLAN_AP:
            # Check connectivity to remote server
            pass
        else:
            return False

    # Function used to attach and dettach from an LTE network
    # Use retries for a non-blocking attach
    def lte_attach(self, state=True, retries=30):
        if state is False:
            self.lte.dettach()
            log.info('Dettached from network')
            return False
        if self.lte.isattached() is True:
            log.info('Device is already attached.')
            return True
        print("Trying to attach.", end='')
        retries_left = retries
        self.lte.attach()
        while retries_left > 0:
            print('.', end='')
            retries_left = retries_left - 1
            if not self.lte.isattached():
                sleep(2)
            else:  # lte.isattached() returned True
                # After successful attach, it's necessary to wait-
                # until cell details are available.
                print('')
                log.info('Device attached successfully.')
                print('\nGetting network info.', end='')
                while not self.cell.get_details() and self.lte.isattached():  # Keep trying to get network info
                    print('.', end='')
                    sleep(2)
                print('')
                log.info('Attach procedure ended successfully.')
                return True
        print('')
        log.info("Failed to attach after {0} retries".format(retries))
        return False

    # Function used to connect and disconnect from an LTE network
    # Use retries for a non-blocking connect
    def lte_connect(self, state=True, retries=30, cid=1):
        if not self.lte.isattached():
            log.warning("Cannot connect/disconnect to/from network because UE is not attached.")
            return False
        # Disconnect if state=False
        if not state:
            self.lte.disconnect()
            log.info("Disconnected from network.")
            return False
        # Connect if state=True, but first check if already connected
        if self.lte.isconnected():
            log.info("Device is already connected.")
            return True
        print("Info: Trying to connect.", end='')
        retries_left = retries
        if self.lte.isattached():
            self.lte.connect()
        while retries_left > 0:
            print('.', end='')
            retries_left = retries_left - 1
            if not self.lte.isconnected():
                sleep(2)
            else:  # lte.isconnected() returned True
                print('')
                log.info("Connected successfully.")
                return True
        print('')
        log.info("Failed to connect after {0} retries".format(retries))
        return False

    # Create a list containing important data - Used if data is needed to be sent to server/database
    def create_info_list(self):
        info_list = [self.imei, self.iccid, self.imsi, self.ip]
        info_list.extend(self.cell.create_info_list())
        return info_list

    # Gets the IP address of the device using AT-Commands
    def get_ip(self):
        # Get IP address
        try:
            self.ip = re.search(',[\"0-9\.]+', self.lte.send_at_cmd('AT+CGPADDR')).group(0).strip(',"')
        except AttributeError:
            log.exception("Could not get IP address from. Wait and try again later.")
        return self.ip

    # Function checks if there is a SIM card inserted by trying to get it's -
    # CCID and IMSI. On success, it saves the CCID and IMSI inside the class.
    def get_sim_details(self):
        try:
            self.iccid = self.lte.iccid()
        except OSError as e:
            log.exception(e)
        if self.iccid is None:
            self.sim = False
        else:
            self.iccid = self.iccid.strip('"')
            self.sim = True
        try:
            self.imsi = re.search('[0-9]+', self.lte.send_at_cmd('AT+CIMI')).group(0)
        except AttributeError:
            log.exception("Could not extract IMSI from SIM card.")
        return self.sim

    # Add (key, value) to sensors dictionary
    def add_sensor_to_dict(self, name, key, value):
        if key in self.sensors_dict:  # Key already in dictionary
            key = key + "_" + name
        self.sensors_dict[key] = value

    # Return True if there is an "alarm" sensor configured
    def has_alarms(self):
        for sensor in self.config.sensors:
            if "Alarm" in sensor.type:
                return True
        return False

    # Sensor alarms must be initiated
    def start_sensors(self):
        for sensor in self.config.sensors:
            if "Alarm" in sensor.type:
                sensor.start_sensor(self)

    # Prints UE static information: IMEI, IMSI, CCID.
    def print_info(self):
        print("---------------UE information----------------")
        print("IMEI: " + self.imei)
        if self.get_sim_details():  # SIM card was found
            try:
                print("ICCID: " + self.iccid)
                print("IMSI: " + self.imsi)
            except TypeError:
                log.exception("Error while printing SIM details.")
        print('---------------------------------------------')

    # Prints dynamic network information: IP address, Serving cell -
    # get_details (cell ID, TaC, RSRP, etc.)
    def print_network_info(self):
        print("---------------Network information----------------")
        if not self.lte.isattached():
            log.warning("not in attach mode, cannot fetch serving network data.")
        if self.cell.get_details():
            if self.get_ip() is not None:
                print("IP address: " + self.ip)
            self.cell.print_all()
            print('--------------------------------------------------')

    # Print all available sensors configured
    def print_sensors_info(self):
        for sensor in self.config.sensors:
            sensor.print_info()

    # Helper function to easily ping a remote server.
    def ping(self, ip):
        self.p('AT!="IP::ping {0}"'.format(ip))

    # Helper function to easily execute AT-commands and print it's contents.
    # Disconnects and connects to LTE network to become a non-blocking function.
    def p(self, cmd, delay=0):
        was_connected = self.lte.isconnected()
        if was_connected:
            self.lte.disconnect()
        response = self.lte.send_at_cmd(cmd, delay=delay)
        for i in [x for x in response.split('\r\n') if x]:  # take all lines of the response excluding empty lines
            print(i)
        if was_connected:
            self.lte.connect()
