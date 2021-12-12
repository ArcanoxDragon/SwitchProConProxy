import time

from bluetoothctl import Bluetoothctl

class ControllerManager:
    def __init__(self):
        self.bt = Bluetoothctl()

    def getPairedControllers(self):
        devices = self.bt.get_paired_devices()

        return [device for device in devices if device["name"] == "Pro Controller"]

    def discoverControllers(self, scanTime=5):
        self.bt.start_scan()
        time.sleep(scanTime)

        return self.bt.get_discoverable_devices()

    def pairController(self, controller):
        if not self.bt.pair(controller["mac_address"]):
            return False

        return self.bt.trust(controller["mac_address"])

    def connectController(self, controller, attempts=3):
        devInfo = self.bt.get_device_info(controller["mac_address"])

        if devInfo["Connected"] == "yes":
            return True

        if not self.bt.trust(controller["mac_address"]):
            return False

        attempt = 1

        while attempt <= attempts:
            attempt += 1

            if self.bt.connect(controller["mac_address"]):
                return True

        return False