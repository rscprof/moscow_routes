from event import Event
from model import Timetable, Route


class New_timetable_event(Event):
    def get_description(self, iso_lang="ru") -> str:
        from tools import calculate_quality
        quality = calculate_quality(self.route, self.timetable)
        name_type_in_russian = ['автобус', 'трамвай', 'троллейбус']
        return "Обнаружено новое расписание на маршруте №{} ({}) с качеством {} (направление - {})\n" \
               "Подробности: https://transport.mos.ru/transport/schedule/route/{}". \
            format(self.route.get_name(), name_type_in_russian[self.route.get_equipment().to_number()],
                   quality[2], self.direction, self.route.get_id_mgt()
                   )

    def __init__(self, route: Route, timetable: Timetable, direction: int):
        self.route = route
        self.timetable = timetable
        self.direction = direction
