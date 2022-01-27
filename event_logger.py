from abc import abstractmethod

from event import Event


class Event_logger:
    @abstractmethod
    def register_event(self, event: Event):
        pass

    @abstractmethod
    def get_descriptions(self) -> list[str]:
        pass
