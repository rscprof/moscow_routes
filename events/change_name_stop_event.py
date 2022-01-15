from event import Event


class Change_name_stop_event(Event):
    """Event: change name of bus's stop"""

    def get_description(self, iso_lang="ru") -> str:
        return "Изменено название остановки с {} на {}".format(self.old_name, self.stop)

    def __init__(self, stop: str, old_name: str):
        self.stop = stop
        self.old_name = old_name
