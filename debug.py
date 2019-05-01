from ue import UE

class debug():
    def __init__(self):
        self.ue_obj = UE()

    def ue(self):
        self.ue_obj.print_info()

    def cell(self, full=False):
        if full:
            self.ue_obj.lte.lte.send_at_cmd('AT!="showDetectedCell"')
        else:
            self.ue_obj.lte.print_rf_details()
