import evdev

class Controller:
    def __init__(self, controller):
        self.controller = controller
        self.input = self._findInputDevice(controller)

        if not self.input:
            raise RuntimeError("Input device for controller \"%s\" not found" % (controller["mac_address"]))

    def _findInputDevice(self, controller):
        allInputDevices = [evdev.InputDevice(path) for path in evdev.list_devices()]

        for device in allInputDevices:
            if device.name == controller["name"]:
                return device

        return None