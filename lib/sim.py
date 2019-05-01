import re
import logging

log = logging.getLogger("Sim")

class Sim:

    def __init__(self):
        self.iccid = None
        self.imsi = None

    def get_sim_details(self, lte_obj):

        # Get ICCID
        try:
            self.iccid = lte_obj.iccid().strip('"')
        except AttributeError as e:
            log.exception("Could not extract ICCID details")

        # Get IMSI
        try:
            self.imsi = re.search('[0-9]+', lte_obj.send_at_cmd('AT+CIMI')).group(0)
        except AttributeError:
            log.exception("Could not extract IMSI from SIM card.")
