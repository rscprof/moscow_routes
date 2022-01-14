from abc import abstractmethod


class Printer:
    """Class can print or save messages"""

    @abstractmethod
    def print(self, message: str = "", end: str = "\n"):
        pass


class PrinterConsole(Printer):
    """"Implementation for printer, to show on console"""

    def print(self, message: str = "", end: str = "\n"):
        print(message, end=end)


class PrinterDoNothing(Printer):
    """"Implementation for printer, do nothing"""

    def print(self, message: str = "", end: str = "\n"):
        pass
