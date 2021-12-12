import evdev
import re

class Controller:
    input: evdev.InputDevice

    def __init__(self):
        self.input = self._findInputDevice()

        if not self.input:
            raise RuntimeError("Input device for Pro Controller not found")

    def _findInputDevice(self):
        allInputDevices = [evdev.InputDevice(path) for path in evdev.list_devices()]

        for device in allInputDevices:
            if device.name == "Switch Pro Controller":
                return device

        return None