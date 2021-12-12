import nxbt

from collections import defaultdict
from evdev import ecodes
from evdev.events import InputEvent
from threading import Thread
from time import time, sleep

from utils import mapRange
from Controller import Controller

BUTTON_MAP = {}
BUTTON_MAP[ecodes.BTN_A] = ["A"]
BUTTON_MAP[ecodes.BTN_B] = ["B"]
BUTTON_MAP[ecodes.BTN_X] = ["X"]
BUTTON_MAP[ecodes.BTN_Y] = ["Y"]
BUTTON_MAP[ecodes.BTN_START] = ["PLUS"]
BUTTON_MAP[ecodes.BTN_SELECT] = ["MINUS"]
BUTTON_MAP[ecodes.BTN_MODE] = ["HOME"]
# BUTTON_MAP[ecodes.BTN_EXTRA] = ["CAPTURE"]
BUTTON_MAP[ecodes.BTN_TL] = ["L"]
BUTTON_MAP[ecodes.BTN_TR] = ["R"]
BUTTON_MAP[ecodes.BTN_TL2] = ["ZL"]
BUTTON_MAP[ecodes.BTN_TR2] = ["ZR"]
BUTTON_MAP[ecodes.BTN_THUMBL] = ["L_STICK", "PRESSED"]
BUTTON_MAP[ecodes.BTN_THUMBR] = ["R_STICK", "PRESSED"]
BUTTON_MAP[ecodes.BTN_DPAD_UP] = ["DPAD_UP"]
BUTTON_MAP[ecodes.BTN_DPAD_DOWN] = ["DPAD_DOWN"]
BUTTON_MAP[ecodes.BTN_DPAD_LEFT] = ["DPAD_LEFT"]
BUTTON_MAP[ecodes.BTN_DPAD_RIGHT] = ["DPAD_RIGHT"]

AXIS_MAP = {}
AXIS_MAP[ecodes.ABS_X] = ["L_STICK", "X_VALUE"]
AXIS_MAP[ecodes.ABS_Y] = ["L_STICK", "Y_VALUE"]
AXIS_MAP[ecodes.ABS_RX] = ["R_STICK", "X_VALUE"]
AXIS_MAP[ecodes.ABS_RY] = ["R_STICK", "Y_VALUE"]

TURBO_FREQUENCY = 20 # Hz
TURBO_INTERVAL = 1.0 / TURBO_FREQUENCY
TURBO_TOGGLE_INTERVAL = TURBO_INTERVAL / 2 # Rate at which input must toggle between pressed/unpressed

class ControllerProxy:
    running = False
    crashed = False
    connected = False
    buttonState = defaultdict(lambda: False)
    buttonTurbo: 'dict[int, bool]' = {}
    turboState: 'dict[int, bool]' = {}
    lastTurboTime = 0.0

    def __init__(self, controller: Controller):
        self.nx = nxbt.Nxbt()
        self.controller = controller
        self.inputPacket = self.nx.create_input_packet()

        adapters = self.nx.get_available_adapters()

        if len(adapters) < 1:
            raise OSError("Unable to detect any Bluetooth adapters.")

        self.adapter = adapters[0]

    def connect(self):
        reconnectAddresses = self.nx.get_switch_addresses()
        controllerIndex = self.nx.create_controller(
            nxbt.PRO_CONTROLLER,
            self.adapter,
            colour_body=[255, 0, 255],
            colour_buttons=[0, 255, 255],
            reconnect_address=reconnectAddresses
        )
        self.nx.wait_for_connection(controllerIndex)
        self.nxController = controllerIndex
        self.connected = True

    def disconnect(self):
        if self.nxController == None:
            return

        self.connected = False
        self.nx.remove_controller(self.nxController)

    def startProcessing(self):
        if self.running:
            return

        self.running = True
        self.workerThread = Thread(target=self._workFunction)
        self.workerThread.start()

    def checkConnection(self):
        if self.nx.state[self.nxController]["state"] == "crashed":
            print("The emulated controller crashed:")
            print(self.nx.state[self.nxController]["errors"])
            print("Controller state:", self.inputPacket)
            sleep(3)
            print("Reconnecting...")

            reconnected = False
            attempts = 0

            while not reconnected:
                attempts += 1

                if attempts > 5:
                    raise ConnectionError("Could not reconnect controller after 5 attempts")

                try:
                    self.disconnect()
                    self.connect()
                    reconnected = True
                except ValueError as e:
                    if e.args[0] == "Specified adapter in use":
                        sleep(3)
                    else:
                        raise

    def close(self, join=True):
        if self.running:
            self.running = False

            if join:
                self.workerThread.join(timeout=5.0)

        self.disconnect()

    def _workFunction(self):
        interval = 1.0 / 120.0 # Must run at 120 Hz
        event: InputEvent
        self.lastTurboTime = time()

        while self.running and not self.crashed:
            startTime = time()

            try:
                while True: # Process as many events as we can
                    event = self.controller.input.read_one()

                    if not event:
                        break

                    self._processEvent(event)

                self._processTurbo(startTime)

                if self.connected:
                    self.nx.set_controller_input(self.nxController, self.inputPacket)

                endTime = time()
                sleep(max(0, interval - (endTime - startTime)))
            except KeyboardInterrupt:
                self.close(join=False)
            except:
                self.crashed = True
                self.close(join=False)
                raise

    def _processTurbo(self, startTime):
        if startTime - self.lastTurboTime >= TURBO_TOGGLE_INTERVAL:
            self.lastTurboTime = startTime

            for button, state in self.turboState.items():
                # Invert the state if the physical button is pressed down, or just make it False if the button is released
                newState = (not state) if self.buttonState[button] else False

                # Invert internal button turbo state
                self.turboState[button] = newState

                # Update the input packet
                packetKey = BUTTON_MAP[button]
                self._updatePacket(packetKey, newState)

    def _processEvent(self, event: InputEvent):
        if event.type == ecodes.EV_KEY:
            pressed = event.value > 0

            if self.buttonState[event.code] != pressed:
                if pressed and event.code in BUTTON_MAP and self.buttonState[ecodes.BTN_EXTRA]:
                    # Toggle turbo for the pressed button
                    name = ecodes.KEY[event.code] if event.code in ecodes.KEY else ecodes.BTN[event.code]

                    if event.code in self.buttonTurbo:
                        print("Disabling turbo for %s button" % (name))
                        self.buttonTurbo.pop(event.code)
                        self.turboState.pop(event.code)

                    else:
                        print("Enabling turbo for %s button" % (name))
                        self.buttonTurbo[event.code] = True
                        self.turboState[event.code] = False

                self.buttonState[event.code] = pressed

            if event.code in BUTTON_MAP and not event.code in self.buttonTurbo:
                packetKey = BUTTON_MAP[event.code]
                self._updatePacket(packetKey, pressed)

                # name = ecodes.KEY[event.code] if event.code in ecodes.KEY else ecodes.BTN[event.code]
                # print("Button %d (%s) was %s" % (event.code, name, "pressed" if pressed else "released"))
        elif event.type == ecodes.EV_ABS:
            axisValue = mapRange(event.value, 0, 255, -100, 100)

            if event.code in AXIS_MAP:
                packetKey = AXIS_MAP[event.code]
                self._updatePacket(packetKey, axisValue)

            # print("Axis %d (%s) = %f" % (event.code, ecodes.ABS[event.code], event.value))

    def _updatePacket(self, key: 'list[str]', value):
        obj = self.inputPacket

        for i in range(len(key)):
            entry = key[i]

            if i == len(key) - 1:
                obj[entry] = value
            else:
                obj = obj[entry]
