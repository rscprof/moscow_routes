import datetime

from event import Event
from moscow_routes_parser.model import Route, Timetable


class New_timetable_event(Event):
    def get_description(self, iso_lang="ru") -> str:
        name_type_in_russian = ['автобус', 'трамвай', 'троллейбус']
        string = "Обнаружено новое расписание на маршруте №{} с id={} ({}) (направление - {})\n" \
                 "Подробности: https://transport.mos.ru/transport/schedule/route/{}\n\n". \
            format(self.route.get_name(), self.route.get_id_mgt(),
                   name_type_in_russian[self.route.get_equipment().to_number()],
                   self.direction, self.route.get_id_mgt()
                   )
        new_quality_description = ""
        for quality in self.qualities:
            descriptions = quality.get_descriptions()
            quality_descriptions = quality.calculate_qualities(self.timetable)
            for (name, description) in zip(descriptions, quality_descriptions):
                new_quality_description += "{}: {}\n".format(name, description)

        from service_locator import Service_locator
        repository = Service_locator.get_instance().get_service('repository')
        date = self.date - datetime.timedelta(days=7)
        old_timetable = repository.load_routes_info_by_number_type_and_date(self.route.get_name(),
                                                                            self.route.get_equipment().to_number(),
                                                                            self.direction, date)
        old_quality_description = ""
        if not (old_timetable is None):

            for quality in self.qualities:
                descriptions = quality.get_descriptions()
                quality_descriptions = quality.calculate_qualities(old_timetable)
                for (name, description) in zip(descriptions, quality_descriptions):
                    old_quality_description += "{}: {}\n".format(name, description)
            if new_quality_description == old_quality_description:
                string += "Изменения незначительные (не вляют на параметры качества)\n"
            else:
                string += "Новые параметры качества: \n"
                string += new_quality_description
                string += "\nСтарые параметры качества за {}: \n".format(date.strftime("%Y%m%d"))
                string += old_quality_description
        else:
            string += "Новые параметры качества: \n"
            string += new_quality_description

        return string

    def __init__(self, route: Route, timetable: Timetable, direction: int, date: datetime.date, qualities=None):
        self.route = route
        self.timetable = timetable
        self.date = date
        self.direction = direction
        if qualities is None:
            from tools import Quality_calculator_max_interval
            from tools import Quality_calculator_set_good_quality
            from tools import Quality_calculator_count
            qualities = [Quality_calculator_max_interval(datetime.time(7, 0, 0), datetime.time(21, 0, 0)),
                         Quality_calculator_max_interval(datetime.time(7, 0, 0), datetime.time(10, 0, 0)),
                         Quality_calculator_max_interval(datetime.time(16, 0, 0), datetime.time(20, 0, 0)),
                         Quality_calculator_set_good_quality(10),
                         Quality_calculator_set_good_quality(15),
                         Quality_calculator_set_good_quality(20),
                         Quality_calculator_set_good_quality(30),
                         Quality_calculator_count()
                         ]

        self.qualities = qualities
