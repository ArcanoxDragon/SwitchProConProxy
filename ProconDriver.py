import pexpect

from pexpect_strip_ansi import StripAnsiSpawn

class ProconDriver:
    def __init__(self):
        self.child = StripAnsiSpawn("./procon_driver -s", echo=False, encoding="utf-8")

        controllerState = self.child.expect(["Now entering calibration mode.", "Now entering input mode!", pexpect.EOF, pexpect.TIMEOUT])

        if controllerState not in [0, 1]:
            raise RuntimeError("Unable to start Pro Controller input driver!")

        self.needsCalibration = controllerState == 0

    def calibrate(self):
        result = self.child.expect(["Calibrated Controller!", pexpect.EOF, pexpect.TIMEOUT])

        return result == 0