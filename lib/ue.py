from network import LTE
from lib.cell import Cell
import re
from time import sleep, time

class UE():

    def __init__(self):
        self.lte = LTE()
        self.imei = self.lte.imei()
        self.ip = None
        self.sim = False
        self.imsi = None
        self.iccid = None
        self.cell = Cell(self.lte)

    # Function used to attach and dettach from an LTE network
    # Use retries for a non-blocking attach
    def attach(self, state=True, retries=30):
        if state is False:
            self.lte.dettach()
            return ("Info: Dettached from network")
        if self.lte.isattached() is True:
            return ("Info: UE is already attached.")
        print("Info: Trying to attach.", end='')
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
                print('\nInfo: UE attached successfully.')
                print('Getting network info.', end='')
                while(self.cell.get_details() is False and self.lte.isattached() is True):
                    print('.', end='')
                    sleep(2)
                print('')
                return ("Info: Attach procedure ended successfully.")
        print('')
        return ("Info: Failed to attach after {0} retries".format(retries))

    # Function used to connect and disconnect from an LTE network
    # Use retries for a non-blocking connect
    def connect(self, state=True, retries=30):
        # Disconnect if state=False
        if state is False:
            self.lte.disconnect()
            return ("Info: Disconnected from network")
        # Conenct if state=True, but first check if already connected
        if self.lte.isconnected() is True:
            return ("Info: UE is already connected.")
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
                return ("Info: UE connected successfully.")
        print('')
        if self.lte.isattached() is False:
            return ("Warning: Cannot connect to network because UE is not attached.")
        return ("Info: Failed to connect after {0} retries".format(retries))


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
            print ("Warning: Could not get IP address from. Wait and try again later.")
        return self.ip

    # Function checks if there is a SIM card inserted by trying to get it's -
    # CCID and IMSI. On success, it saves the CCID and IMSI inside the class.
    def get_sim_details(self):
        self.iccid = self.lte.iccid()
        if self.iccid is None:
            self.sim = False
        else:
            self.iccid = self.iccid.strip('"')
            self.sim = True
        try:
            self.imsi = re.search('[0-9]+', self.lte.send_at_cmd('AT+CIMI')).group(0)
        except AttributeError:
            print("Warning: Could not extract IMSI from SIM card.")
        return self.sim

    # Prints UE static information: IMEI, IMSI, CCID.
    def print_info(self):
        print("---------------UE information----------------")
        print ("IMEI: " + self.imei)
        if self.get_sim_details() is not False:
            try:
                print ("ICCID: " + self.iccid)
                print ("IMSI: " + self.imsi)
            except TypeError:
                print ("Error: Error while printing SIM details.")
        print('---------------------------------------------')

    # Prints dynamic network infromation: IP address, Serving cell -
    # get_details (cell ID, TaC, RSRP, etc.)
    def print_network_info(self):
        print("---------------Network information----------------")
        if self.lte.isattached() is False:
            print ("Warning: UE not in attach mode, cannot fetch serving network data.")
            return False
        if self.cell.get_details() is True:
            if self.get_ip() is not None:
                print ("IP address: " + self.ip)
            self.cell.print_all()
            print('--------------------------------------------------')
            return True

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
