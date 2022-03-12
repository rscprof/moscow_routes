from event import Event
from moscow_routes_parser.model import Route


class New_route_event(Event):
    def get_description(self, iso_lang="ru") -> str:
        name_type_in_russian = ['автобус', 'трамвай', 'троллейбус']
        return "Появился новый маршрут №{} ({})".format(self.route.get_name(),
                                                        name_type_in_russian[self.route.get_equipment().to_number()])

    def __init__(self, route: Route):
        self.route = route
