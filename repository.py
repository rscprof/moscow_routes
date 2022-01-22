from abc import abstractmethod
from datetime import datetime

from model import Stop_builder, Stop, Route, Timetable
from model_impl import Stop_builder_impl


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
    def load_routes_info_by_number(self, num_route, direction):
        pass

    @abstractmethod
    def store_route_info_with_adding_stops(self, num_route: str, route_info: Timetable, date: datetime.date,
                                           direction: int) -> None:
        pass

