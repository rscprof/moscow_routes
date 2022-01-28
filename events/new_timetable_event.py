from event import Event
from model import Timetable, Route


class New_timetable_event(Event):
    def get_description(self, iso_lang="ru") -> str:
        from tools import Quality_calculator_max_interval
        quality_calculator = Quality_calculator_max_interval()
        quality = quality_calculator.calculate_qualities(self.timetable)[0]
        name_type_in_russian = ['автобус', 'трамвай', 'троллейбус']
        return "Обнаружено новое расписание на маршруте №{} ({}) с качеством {} (направление - {})\n" \
               "Подробности: https://transport.mos.ru/transport/schedule/route/{}". \
            format(self.route.get_name(), name_type_in_russian[self.route.get_equipment().to_number()],
                   quality, self.direction, self.route.get_id_mgt()
                   )

    def __init__(self, route: Route, timetable: Timetable, direction: int):
        self.route = route
        self.timetable = timetable
        self.direction = direction
