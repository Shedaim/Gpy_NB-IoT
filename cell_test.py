from network import LTE
from lib.ue import UE
from lib.network_iot import Network
import time
import re

ue = UE()
ue.lte.send_at_cmd('AT!="setDbgPerm full"')
ue.get_sim_details()

network = Network(ue, "LTE", bands=[28])
