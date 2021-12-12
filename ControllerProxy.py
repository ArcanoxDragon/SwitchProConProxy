import nxbt

from Controller import Controller

class ControllerProxy:
    def __init__(self, controller: Controller):
        self.nx = nxbt.Nxbt()
        self.controller = controller

        adapters = self.nx.get_available_adapters()

        if len(adapters) < 1:
            raise OSError("Unable to detect any Bluetooth adapters.")

        self.adapter = adapters[0]

        controllerIndex = self.nx.create_controller(
            nxbt.PRO_CONTROLLER,
            self.adapter,
            colour_body=[255, 0, 255],
            colour_buttons=[0, 255, 255]
        )
        self.nxController = controllerIndex

    def close(self):
        if not self.nxController:
            return

        self.nx.remove_controller(self.nxController)