from abc import abstractmethod


class Event:
    @abstractmethod
    def get_description(self, iso_lang="ru") -> str:
        """Return description of event using language"""
        pass

