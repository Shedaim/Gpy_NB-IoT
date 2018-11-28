from network import LTE
from lib.network_iot import Cell
from lib.configuration import Configuration
import re
from time import sleep, time
import lib.logging as logging
import ujson

log = logging.getLogger("UE")

class UE():

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

    # Function used to attach and dettach from an LTE network
    # Use retries for a non-blocking attach
    def attach(self, state=True, retries=30):
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
        while(retries_left > 0):
            print('.', end='')
            retries_left = retries_left - 1
            if self.lte.isattached() is False:
                sleep(2)
            else: # lte.isattached() returned True
                # After successful attach, it's necessary to wait-
                # untill cell details are available.
                print('')
                log.info('Device attached successfully.')
                print('\nGetting network info.', end='')
                while(self.cell.get_details() is False and self.lte.isattached() is True):
                    print('.', end='')
                    sleep(2)
                print('')
                log.info('Attach procedure ended successfully.')
                return True
        print('')
        log.info('Failed to attach after {0} retries".format(retries)')
        return False

    # Function used to connect and disconnect from an LTE network
    # Use retries for a non-blocking connect
    def connect(self, state=True, retries=30, cid=1):
        # Disconnect if state=False
        if state is False:
            self.lte.disconnect()
            log.info("Disconnected from network.")
            return False
        # Conenct if state=True, but first check if already connected
        if self.lte.isconnected() is True:
            log.info("Device is already connected.")
            return True
        print("Info: Trying to connect.", end='')
        retries_left = retries
        if self.lte.isattached() is True:
            self.lte.connect()
        while(retries_left > 0):
            print('.', end='')
            retries_left = retries_left - 1
            if self.lte.isconnected() is False:
                sleep(2)
            else: # lte.isconnected() returned True
                print('')
                log.info("Connected successfully.")
                return True
        print('')
        if self.lte.isattached() is False:
            log.warning("Cannot connect to network because UE is not attached.")
            return False
        log.info("Failed to connect after {0} retries".format(retries))
        return False


    # Create a list containing important data - Used if
    # data is needed to be sent to server/database
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

    # Take a list of sensor objects and turn into a single json string.
    def sensors_into_message(self):
        self.sensors_dict = {}
        for sensor in self.config.sensors:
            sensor.get_value()
            if len(sensor.type) == 1:
                self.add_to_dict(sensor.type[0], sensor.value)
            else:
                for i in range(len(sensor.type)):
                    if sensor.value is None:
                        self.add_to_dict(sensor.type[i], None)
                    else:
                        self.add_to_dict(sensor.type[i], sensor.value[i])
        http_payload = ujson.dumps(self.sensors_dict)
        return http_payload

    def add_to_dict(self, key, value):
        if key in self.sensors_dict:  # Key already in dictionary
            key = key + "_" + self.name
        self.sensors_dict[key] = value

    # Prints UE static information: IMEI, IMSI, CCID.
    def print_info(self):
        print("---------------UE information----------------")
        print ("IMEI: " + self.imei)
        if self.get_sim_details() is not False:
            try:
                print ("ICCID: " + self.iccid)
                print ("IMSI: " + self.imsi)
            except TypeError:
                log.exception("Error while printing SIM details.")
        print('---------------------------------------------')

    # Prints dynamic network infromation: IP address, Serving cell -
    # get_details (cell ID, TaC, RSRP, etc.)
    def print_network_info(self):
        print("---------------Network information----------------")
        if self.lte.isattached() is False:
            log.warning("not in attach mode, cannot fetch serving network data.")
            return False
        if self.cell.get_details() is True:
            if self.get_ip() is not None:
                print ("IP address: " + self.ip)
            self.cell.print_all()
            print('--------------------------------------------------')
            return True

    # Print all available sensors configured
    def print_sensors_info(self):
        for sensor in self.config.sensors:
            sensor.print_info()

    # Helper function to easily ping a remote server.
    def ping(self, ip):
        self.p('AT!="IP::ping {0}"'.format(ip))

    # Helper function to easily execute AT-commands and print it's contents.
    # Disconnects and connectes to LTE network to become a non-blocking function.
    def p(self, cmd, delay=0):
        was_connected = self.lte.isconnected()
        if was_connected is True:
            self.lte.disconnect()
        response = self.lte.send_at_cmd(cmd, delay=delay)
        for i in [x for x in response.split('\r\n') if x]:
            print (i)
        if was_connected is True and self.lte.isconnected() is False:
            self.lte.connect()
