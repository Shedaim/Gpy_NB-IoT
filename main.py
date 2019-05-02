from ue import UE
import logging

log = logging.getLogger("Main")


def start():
    # Initialize ue object and print it's data
    ue = UE()
    ue.print_info()
    return ue


this_device = start()
