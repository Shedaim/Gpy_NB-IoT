# Class that contains functions and parameters used for network
# technologies and interfaces. This class will be used to configure
# the different Interfaces and interact between them.
import logging
from networking.wifi import WLAN_AP
import messages
from network import LTE
from time import sleep
import re

log = logging.getLogger("LTE_Network")

class LTE_Network:

    def __init__(self, bands: []):
        self.lte = LTE()
        self.bands = bands
        #self.net_type = net_type
        self.cell = Cell()
        self.ip = None

    # Connect device to an LTE system
    def lte_connect_procedure(self):
        while not self.lte.isattached():
            self.lte_attach()
        if not self.lte.isconnected():
            self.lte_connect(cid=1)  # Need to check if it's possible to get a different cid
        # Wait untill connected to a network
        while not self.lte.isconnected():
            sleep(1)

    # Function used to attach and dettach from an LTE network
    # Use retries for a non-blocking attach
    def lte_attach(self, state=True, retries=30):
        if state is False:
            self.lte.dettach()
            log.info('Dettached from network')
        elif self.lte.isattached() is True:
            log.info('Device is already attached.')
        else:
            print("Trying to attach.", end='')
            retries_left = retries
            try:
                self.lte.attach()
            except OSError:
                log.exception("Error attaching to network\n")
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
                    while not self.get_cell_details() and self.lte.isattached():  # Keep trying to get network info
                        print('.', end='')
                        sleep(2)
                    print('')
                    self.get_ip()
                    if self.ip is not None:
                        print("IP address: " + self.ip)
                    self.cell.print_all()
                    return
            print('')
            log.info("Failed to attach after {0} retries".format(retries))

    # Function used to connect and disconnect from an LTE network
    # Use retries for a non-blocking connect
    def lte_connect(self, state=True, retries=30, cid=1):
        if not self.lte.isattached():
            log.warning("Cannot connect/disconnect to/from network because UE is not attached.")
        # Disconnect if state=False
        elif not state:
            self.lte.disconnect()
            if not self.lte.isconnected():
                log.info("Disconnected from network.")
            else:
                log.error("Failed to disconnect from network.")
        # Connect if state=True, but first check if already connected
        elif self.lte.isconnected():
            log.info("Device is already connected.")
        else:
            print("Info: Trying to connect.", end='')
            retries_left = retries
            self.lte.connect()
            while retries_left > 0:
                print('.', end='')
                retries_left = retries_left - 1
                if not self.lte.isconnected():
                    sleep(2)
                else:  # lte.isconnected() returned True
                    print('')
                    log.info("Connected successfully.")
                    return
            print('')
            log.info("Failed to connect after {0} retries".format(retries))


    # Initialize LTE network
    def initialize_lte(self):
        # Make initial configuration to modem
        self.p('AT!="setDbgPerm full"')
        self.configure_lte_network()
        log.info("LTE network initialized.")

    # Use the bands entered to re-configure the LTE modem
    def configure_lte_network(self):
        log.info("Configuring network with variables: Network = {0}, bands = {1}"
                 .format("LTE", str(self.bands)))
        if self.bands:
            # Delete existing bands from scan list
            self.lte.send_at_cmd('AT+CFUN=0')
            self.lte.send_at_cmd('AT!="clearscanconfig"')
            self.lte.send_at_cmd('AT+CGDCONT=1,"IP","secure.motolab.com"')
            # Add required bands to scan list
            for band in self.bands:
                self.lte.send_at_cmd('AT!="addscanband band={0}"'.format(band))
            # Restart modem with new configuration
            self.lte.send_at_cmd('AT+CFUN=1')
            # Put UE in "Try to register" mode
            self.lte.send_at_cmd('AT+CEREG=2')
        else:
            log.warning("No bands added to LTE scan list.")


    # Gets details of the serving cell indexes the valued data into the class
    def get_cell_details(self):
        if self.lte.isconnected():
            log.warning("Can't send AT commands while connected. Disconnect first and try again.")
            return False
        else:
            # TODO - implement in a world with more than one serving cell available
            info = self.lte.send_at_cmd('AT!="showDetectedCell"').split('|')
            retries = 15
            while len(info) <= 20 and retries > 0:
                sleep(1)
                print('.', end='')
                info = self.lte.send_at_cmd('AT!="showDetectedCell"').split('|')
                retries = retries - 1

            if len(info) > 20:
                info = [x.strip(" ") for x in info[18:32]]
                # Some of the answers contain many unnecessary spaces.
                # Strip to get rid of them.
            else:
                log.warning("Cell not found. Is the antenna connected?")
                return False

            self.cell.cell_type = info[0]
            self.cell.dlarfcn = info[1]
            self.cell.cpi = info[2]
            self.cell.rsrp = info[5]
            self.cell.reject_cause = info[13]
            # Return the register state of a subscriber
            info = self.lte.send_at_cmd('AT+CEREG?').split(',')
            if info[1] in ['1', '5']:  # Both states indicate "Registered"
                self.cell.registered = True
                try:
                    self.cell.tac = info[2].strip('"')
                    self.cell.cell_id = info[3].strip('"')
                except IndexError:
                    log.warning("Could not read TAC and Cell_ID from CEREG AT command")
            else:
                self.cell.registered = False
        return True

    # Gets the IP address of the device using AT-Commands
    def get_ip(self):
        # Get IP address
        try:
            self.ip = re.search(',[\"0-9\.]+', self.lte.send_at_cmd('AT+CGPADDR')).group(0).strip(',"')
        except AttributeError:
            log.exception("Could not get IP address from. Wait and try again later.")


    def print_info(self):
        print("Network type: " + self.net_type)
        print("Bands: " + ','.join([str(x) for x in self.lte_bands]))

    # Helper function to easily execute AT-commands and print it's contents.
    # Disconnects and connects to LTE network to become a non-blocking function.
    def p(self, cmd, delay=0):
        was_connected = self.lte.isconnected()
        if was_connected:
            self.lte.disconnect()
        response = self.lte.send_at_cmd(cmd)
        for i in [x for x in response.split('\r\n') if x]:  # take all lines of the response excluding empty lines
            print(i)
        if was_connected:
            self.lte.connect()

    # Create a list containing important data - Used if data
    # is needed to be sent to server/database
    def print_rf_details(self):
        self.get_cell_details()
        print ("[Cell ID:", self.cell.cell_id, ", DLarfcn:", self.cell.dlarfcn,
         ", RSRP:", self.cell.rsrp, "]")
        print ("[TAC:", self.cell.tac, ", Registered:", self.cell.registered,
         ", Reject Cause:", self.cell.reject_cause, "]")

class Cell:

    def __init__(self):
        #self.lte = lte
        self.cell_id = None
        self.cpi = None
        self.cell_type = None
        self.dlarfcn = None
        self.rsrp = None
        self.reject_cause = None
        self.registered = None
        self.tac = None

    # Print the cell details - for debugging purposes
    def print_all(self):
        if self.cell_id is not None:
            print("Cell ID:", self.cell_id)
            print("Cell Type:", self.cell_type)
            print("Tracking Area Code:", self.tac)
            print("Earfcn:", self.dlarfcn)
            print("RSRP:", self.rsrp)
            if self.registered:
                print("Status: Registered")
            else:
                print("Status: Not registered")
            print("Reject cause:", self.reject_cause)
        else:
            log.info("No data to display.")

# Initialize WiFi
def initialize_wifi(ue):
    # Check if WiFi is configured to be turned on
    if ue.wifi.mode == WLAN_AP:
        # Create access point for wifi
        ue.wifi.print_wifi()
    else: # Device needs to connect to a remote wifi gateway
        # Try to connect to wifi gateway and get ip adress and gw info
        ue.wifi.print_wifi()
    log.info("WiFi network initialized in mode: " + str(ue.wifi.mode))
