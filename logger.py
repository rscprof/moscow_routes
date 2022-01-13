from abc import abstractmethod


class Logger:
    """"Abstract class for logging results"""

    @abstractmethod
    def print(self, message: str):
        """"this methods get non-error messages from class"""
        pass

    @abstractmethod
    def error(self, message: str):
        """"this methods get error messages from class"""
        pass


class LoggerIgnore(Logger):
    """"Logger implementation ignoring all messages"""

    def print(self, message: str):
        pass

    def error(self, message: str):
        pass


class LoggerPrint(Logger):
    """"Logger implementation printing to console all messages"""

    def print(self, message: str):
        print(message)

    def error(self, message: str):
        print(message)