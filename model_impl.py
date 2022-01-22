from datetime import datetime
from itertools import groupby
from typing import Optional

from model import Timetable_stop_time, Timetable_stop, Timetable, Timetable_stop_builder, Timetable_builder, Stop, \
    Stop_builder


class Stop_impl(Stop):

    def get_name(self) -> str:
        return self.name


    def get_id(self) -> int:
        return self.id

    def __init__(self, id_stop: int, name: str):
        self.id = id_stop
        self.name = name


class Stop_builder_impl(Stop_builder):

    def __init__(self):
        self.name = None
        self.id = None

    def set_name(self, name: str) -> Stop_builder:
        self.name = name
        return self


    def set_id(self, id_stop: int) -> Stop_builder:
        self.id = id_stop
        return self

    def build(self) -> Stop:
        return Stop_impl(self.id, self.name)


class Timetable_stop_time_t_mos_ru(Timetable_stop_time):

    def __init__(self, time_flight: datetime.time, special_flight: Optional[str]):
        self.get_time = lambda: time_flight
        self.get_special_flight = lambda: special_flight

    def get_time(self) -> datetime.time:
        return self.get_time()

    def get_color_special_flight(self) -> Optional[str]:
        return self.get_special_flight()

    def __eq__(self, other):
        return self.get_time() == other.get_time() and \
               self.get_special_flight() == other.get_special_flight()

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        str_time = self.get_time().strftime("%H:%M")
        color = self.get_color_special_flight()
        if not (color is None):
            str_time += " ({})".format(color)
        return str_time


class Timetable_stop_t_mos_ru(Timetable_stop):

    def __init__(self, name: str, times: list[Timetable_stop_time_t_mos_ru]):
        self.name = name
        self.times = times

    def get_name(self) -> str:
        return self.name


    def get_times(self):
        return iter(self.times)

    def __eq__(self, other):
        return self.get_name() == other.get_name() and \
               list(sorted(self.get_times(), key=lambda x: x.get_time())) == list(
            sorted(other.get_times(), key=lambda x: x.get_time()))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        result = "{}: ".format(self.get_name() ) + "\n"
        time_by_hours = groupby(sorted(self.get_times(), key=lambda t: t.get_time()), key=lambda t: t.get_time().hour)
        for h in time_by_hours:
            result += str(h[0])+': ' + \
                      ' '.join(map(lambda t: str(t.get_time().minute), h[1]))+"\n"
        return result


class Timetable_t_mos_ru(Timetable):

    def get_date(self) -> datetime.date:
        return self.get_date()

    def __init__(self, data_services: int, id_route_t_mos_ru: str, direction: int, date: datetime.date,
                 stops: [Timetable_stop_t_mos_ru]):
        self.get_data_services = lambda: data_services
        self.get_id_route_t_mos_ru = lambda: id_route_t_mos_ru
        self.get_direction = lambda: direction
        self.get_stops = lambda: stops
        self.get_date = lambda: date

    def get_direction(self) -> int:
        return self.get_direction()

    def get_id_route_t_mos_ru(self) -> str:
        return self.get_id_route_t_mos_ru()

    def get_data_services(self) -> int:
        return self.get_data_services()

    def __iter__(self):
        return iter(self.get_stops())


class Timetable_stop_builder_t_mos_ru(Timetable_stop_builder):

    def add_item_timetable(self, time_flight: datetime.time, special_flight: Optional[str]):
        self.time_flights.append(Timetable_stop_time_t_mos_ru(time_flight, special_flight))

    def set_name(self, name: str) -> Timetable_stop_builder:
        self.name = name
        return self


    def __init__(self):
        self.name = None
        self.time_flights = []

    def build(self) -> Timetable_stop:
        return Timetable_stop_t_mos_ru(self.name, self.time_flights)


class Timetable_builder_t_mos_ru(Timetable_builder):

    def __init__(self):
        self.date = None
        self.direction = None
        self.id_route_t_mos_ru = None
        self.data_services = None
        self.stops = []

    def set_date(self, date: datetime.date) -> Timetable_builder:
        self.date = date
        return self

    def add_stop(self, name: str) -> Timetable_stop_builder:
        stop_builder = Timetable_stop_builder_t_mos_ru().set_name(name)
        self.stops.append(stop_builder)
        return stop_builder

    def set_data_services(self, data_services: int) -> Timetable_builder:
        self.data_services = data_services
        return self

    def build(self) -> Timetable:
        return Timetable_t_mos_ru(self.data_services,
                                  self.id_route_t_mos_ru,
                                  self.direction,
                                  self.date,
                                  list(map(lambda stop_builder: stop_builder.build(),
                                           self.stops)))

    def set_id_route_t_mos_ru(self, id_route_t_mos_ru: str) -> Timetable_builder:
        self.id_route_t_mos_ru = id_route_t_mos_ru
        return self

    def set_direction(self, direction: int) -> Timetable_builder:
        self.direction = direction
        return self
