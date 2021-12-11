import cli_ui as ui
import re
import time

from ControllerManager import *
from concurrent.futures import *

cm = ControllerManager()

def formatControllerChoice(choice):
    if isinstance(choice, str):
        return choice

    return "%s (%s)" % (choice["name"], choice["mac_address"])

def pairNewController(scanTime=8):
    with ThreadPoolExecutor() as exec:
        controllerToPair = None

        while not controllerToPair:
            ui.info_progress("Scanning for new devices...", 0, scanTime)
            startTime = time.time()
            scanFuture = exec.submit(cm.discoverControllers, scanTime=scanTime)

            while scanFuture.running():
                curTime = time.time()
                elapsed = min(scanTime, curTime - startTime)
                ui.info_progress("Scanning for new devices...", elapsed, scanTime)
                time.sleep(0.25)

            newControllers = [controller for controller in scanFuture.result() if not re.match(r"^(RSSI|TxPower):", controller["name"])]
            choices = newControllers + ["Scan again", "Cancel", "Exit"]
            chosen = ui.ask_choice("Select a controller to pair with:", choices=choices, func_desc=formatControllerChoice, sort=False)

            if chosen == "Exit":
                exit(0)
            elif chosen == "Cancel":
                return None
            elif chosen == "Scan again":
                continue
            else:
                controllerToPair = chosen

        print("Pairing with \"%s\" (%s)..." % (controllerToPair["name"], controllerToPair["mac_address"]), end="", flush=True)

        if not cm.pairController(controllerToPair):
            print()
            raise ConnectionError("Could not pair with the selected controller")

        print("Pairing successful!")
        return controllerToPair


def promptForController():
    chosenController = None
    pairedControllers = cm.getPairedControllers()
    choices = pairedControllers + ["Pair new controller", "Exit"]

    while not chosenController:
        chosen = ui.ask_choice("Select a controller to use:", choices=choices, func_desc=formatControllerChoice, sort=False)

        if chosen == "Exit":
            exit(0)
        elif chosen == "Pair new controller":
            chosenController = pairNewController()

            if not chosenController:
                print("No controller was paired.")
        else:
            chosenController = chosen

    return chosenController


if __name__ == "__main__":
    controller = promptForController()

    if not controller:
        exit(0)

    print("Connecting to \"%s\" (%s) (press L+R)..." % (controller["name"], controller["mac_address"]), end="", flush=True)

    if not cm.connectController(controller):
        print()
        raise ConnectionError("Could not connect to the selected controller")

    print("Connected!")

    # TODO: Do controllery stuffs