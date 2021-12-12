import os

from concurrent.futures import *
from time import sleep

from Controller import Controller
from ControllerProxy import ControllerProxy
from ProconDriver import ProconDriver

if __name__ == "__main__":
    # Set process priority first
    os.nice(-15)

    print("Opening input driver for Pro Controller...")

    proconDriver = ProconDriver()

    if proconDriver.needsCalibration:
        print(
            "The connected Pro Controller must be calibrated. Move both sticks slowly in a circle " +
            "(one at a time), and press the \"Share\" button when done.")

        if not proconDriver.calibrate():
            print("Calibration was not successful. Please run the program again.")
            exit(1)

    controller = Controller()
    proxy: ControllerProxy = None
    print("Pro Controller ready!")

    try:
        proxy = ControllerProxy(controller)
        proxy.startProcessing()

        print(
            "Now searching for a Nintendo Switch! If this is your first time connecting the " +
            "emulated controller to your Switch, make sure your Switch is at the \"Change Grip/Order\" " +
            "screen.")
        proxy.connect()
        print("Successfully connected to Nintendo Switch! Press Ctrl+C to exit.")

        while True:
            proxy.checkConnection()

            if proxy.crashed:
                print("The controller proxy crashed! Please run the program again.")
                exit(1)

            sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if proxy:
            try: # Hide exceptions while we clean up
                print("Disconnecting from Nintendo Switch...")
                proxy.close()
            except:
                pass