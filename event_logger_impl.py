from event import Event
from event_logger import Event_logger


class Event_logger_impl(Event_logger):

    def register_listener(self, listener) -> None:
        self.listeners.append(listener)

    def __init__(self):
        self.events = []
        self.listeners = []

    def register_event(self, event: Event):
        self.events.append(event)
        for listener in self.listeners:
            listener(event)

    def get_descriptions(self) -> list[str]:
        return list(map(lambda event: event.get_description(), self.events))
