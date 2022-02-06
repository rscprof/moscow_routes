from abc import abstractmethod

from event import Event


class Event_logger:
    @abstractmethod
    def register_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def get_descriptions(self) -> list[str]:
        pass

    @abstractmethod
    def register_listener(self, listener) -> None:
        pass
