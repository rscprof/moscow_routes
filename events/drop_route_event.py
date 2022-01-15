from event import Event


class Drop_route_event(Event):
    def get_description(self, iso_lang="ru") -> str:
        name_type_in_russian = ['автобус', 'трамвай', 'троллейбус']
        return "Исчез маршрут №{} ({})".format(self.route_number,
                                               name_type_in_russian[self.route_type])

    def __init__(self, route_number: str, route_type: int):
        self.route_number = route_number
        self.route_type = route_type
