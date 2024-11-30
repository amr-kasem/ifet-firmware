class State:
    def __init__(self, machine):
        self.machine = machine

    def on_enter(self):
        self.machine.logger.info(f"Entering state: {self.__class__.__name__}")

    def on_exit(self):
        self.machine.logger.info(f"Exiting state: {self.__class__.__name__}")
