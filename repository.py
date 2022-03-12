from abc import abstractmethod
from datetime import datetime
from typing import Optional, Tuple

from moscow_routes_parser.model import Stop_builder, Route, Timetable_stop_builder, Stop
from moscow_routes_parser.model_impl import Stop_builder_impl, Timetable_stop_builder_t_mos_ru, \
    Timetable_builder_t_mos_ru

from model.model_with_id import Timetable_builder_decorator_with_id, Timetable_with_id, Stop_builder_decorator_with_id


class Repository:
    @abstractmethod
    def get_all_stops(self, builder: Stop_builder_decorator_with_id =
    Stop_builder_decorator_with_id(Stop_builder_impl())) -> [Stop]:
        pass

    @abstractmethod
    def get_last_snapshot(self, work_time: int) -> list[Route]:
        pass

    @abstractmethod
    def create_snapshot_routes(self, routes: list[Route], work_time: int):
        pass

    @abstractmethod
    def load_routes_info_by_number_and_date(self, num_route: str, direction: int, date: datetime.date,
                                            timetable_builder: Timetable_builder_decorator_with_id =
                                            Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                            ) -> \
            Optional[Timetable_with_id]:
        pass

    @abstractmethod
    def load_routes_info_by_number_and_type(self, num_route: str, type_route: int, direction: int,
                                            timetable_stop_builder: Timetable_stop_builder =
                                            Timetable_stop_builder_t_mos_ru(),
                                            timetable_builder: Timetable_builder_decorator_with_id =
                                            Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                            ) -> list[Timetable_with_id]:
        pass

    @abstractmethod
    def load_routes_info_by_number(self, num_route: int, direction: int,
                                   timetable_stop_builder: Timetable_stop_builder = Timetable_stop_builder_t_mos_ru(),
                                   timetable_builder: Timetable_builder_decorator_with_id =
                                   Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                   ) -> list[Timetable_with_id]:
        pass

    @abstractmethod
    def store_route_timetable_date(self, id_route: str, direction: int, date: datetime.date, id_timetable: int) -> None:
        pass

    @abstractmethod
    def store_routes(self, route_names: list[Tuple[str, Tuple[float, float]]]):
        pass

    @abstractmethod
    def store_route_info(self, date, direction, num_route, route_info) -> int:
        pass

    @abstractmethod
    def load_routes_info_by_number_type_and_date(self, num_route: str, type_route: int, direction: int,
                                                 date: datetime.date,
                                                 timetable_builder: Timetable_builder_decorator_with_id =
                                                 Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                                 ) -> \
            Optional[Timetable_with_id]:
        pass
