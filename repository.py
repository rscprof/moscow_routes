from abc import abstractmethod
from datetime import datetime
from typing import Optional, Tuple

from model import Stop_builder, Stop, Route, Timetable, Timetable_stop_builder, Timetable_builder
from model_impl import Stop_builder_impl, Timetable_stop_builder_t_mos_ru, Timetable_builder_t_mos_ru


class Repository:
    @abstractmethod
    def get_all_stops(self, builder: Stop_builder = Stop_builder_impl()) -> [Stop]:
        pass

    @abstractmethod
    def get_last_snapshot(self, work_time: int) -> list[Route]:
        pass

    @abstractmethod
    def create_snapshot_routes(self, routes: list[Route], work_time: int):
        pass

    @abstractmethod
    def load_routes_info_by_number(self, num_route: int, direction: int,
                                   timetable_stop_builder: Timetable_stop_builder = Timetable_stop_builder_t_mos_ru(),
                                   timetable_builder: Timetable_builder = Timetable_builder_t_mos_ru()
                                   ) -> list[Timetable]:
        pass

    @abstractmethod
    def store_route_timetable_date(self, id_route: int, direction: int, date: datetime.date, id_timetable: int) -> None:
        pass

    @abstractmethod
    def store_routes(self, route_names: list[Tuple[str]]):
        pass

    @abstractmethod
    def load_routes_info_by_number_and_date(self, num_route: int, direction: int, date: datetime.date,
                                            timetable_builder: Timetable_builder = Timetable_builder_t_mos_ru()
                                            ) -> \
            Optional[Timetable]:
        pass
