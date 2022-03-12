from abc import ABC, abstractmethod
from datetime import datetime

from moscow_routes_parser.model import Timetable_builder, Timetable, Timetable_stop, Timetable_stop_builder, \
    Stop_builder, Stop


class Timetable_with_id(Timetable, ABC):

    @abstractmethod
    def get_id_timetable(self) -> int:
        pass


class Timetable_decorator_with_id(Timetable_with_id):
    def __init__(self, timetable: Timetable, timetable_id: int):
        self.id = timetable_id
        self.timetable = timetable

    def get_id_timetable(self) -> int:
        return self.id

    def __iter__(self):
        return iter(self.timetable)

    def get_direction(self) -> int:
        return self.timetable.get_direction()

    def get_id_route_t_mos_ru(self) -> str:
        return self.timetable.get_id_route_t_mos_ru()

    def get_date(self) -> datetime.date:
        return self.timetable.get_date()

    def get_stops(self) -> list[Timetable_stop]:
        return self.timetable.get_stops()


class Stop_with_id(Stop,ABC):

    @abstractmethod
    def get_id(self)->int:
        pass


class Stop_decorator_with_id(Stop_with_id):
    def get_id(self) -> int:
        return self.id

    def get_name(self) -> str:
        return self.stop.get_name()

    def get_coords(self) -> (float, float):
        return self.stop.get_coords()

    def __init__(self,stop: Stop,id_stop:int):
        self.id = id_stop
        self.stop = stop


class Stop_builder_decorator_with_id:

    def __init__(self, stop_builder: Stop_builder):
        self.id = None
        self.stop_builder = stop_builder

    def set_id(self,stop_id:int)-> 'Stop_builder_decorator_with_id':
        self.id = stop_id
        return self

    def set_name(self, name: str) -> 'Stop_builder_decorator_with_id':
        self.stop_builder.set_name(name)
        return self

    def set_coords(self, coords: (float, float)) -> 'Stop_builder_decorator_with_id':
        self.stop_builder.set_coords(coords)
        return self

    def build(self) -> Stop_with_id:
        return Stop_decorator_with_id(self.stop_builder.build(),self.id)


class Timetable_builder_decorator_with_id:

    def add_stop(self) -> Timetable_stop_builder:
        return self.timetable_builder.add_stop()

    def set_id_route_t_mos_ru(self, id_route_t_mos_ru: str) -> 'Timetable_builder_decorator_with_id':
        self.timetable_builder.set_id_route_t_mos_ru(id_route_t_mos_ru)
        return self

    def set_direction(self, direction: int) -> 'Timetable_builder_decorator_with_id':
        self.timetable_builder.set_direction(direction)
        return self

    def set_date(self, date: datetime.date) -> 'Timetable_builder_decorator_with_id':
        self.timetable_builder.set_date(date)
        return self

    def __init__(self, timetable_builder: Timetable_builder):
        self.id = None
        self.timetable_builder = timetable_builder

    def set_id_timetable(self, id_timetable: int) -> 'Timetable_builder_decorator_with_id':
        self.id = id_timetable
        return self

    def build(self) -> Timetable_with_id:
        timetable = self.timetable_builder.build()
        timetable_with_id = Timetable_decorator_with_id(timetable, self.id)
        return timetable_with_id
