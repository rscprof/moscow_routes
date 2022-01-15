from event import Event


class New_stop_event(Event):
    """Event: find new stop in parseable data"""
    def get_description(self, iso_lang="ru") -> str:
        return "Появилась новая остановка: {}".format(self.stop)

    def __init__(self, stop: str):
        self.stop = stop
