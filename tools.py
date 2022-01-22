import datetime

import pandas

from events.drop_route_event import Drop_route_event
from events.new_route_event import New_route_event
from events.new_stop_event import New_stop_event

from events.new_timetable_event import New_timetable_event
from logger import LoggerPrint, Logger

from model import Route, Timetable
from printer import Printer, PrinterConsole
from repository import Repository
from service_locator import Service_locator
from t_mos_ru import get_route, get_list_routes


class Quality_storage:
    def __init__(self, segments=None
                 ):
        if segments is None:
            segments = [
                {'from': datetime.time(7, 0, 0), 'to': datetime.time(21, 0, 0), 'description': '7-21', },
                {'from': datetime.time(7, 0, 0), 'to': datetime.time(10, 0, 0), 'description': '7-10', },
                {'from': datetime.time(16, 0, 0), 'to': datetime.time(20, 0, 0), 'description': '16-20', },
            ]
        self.segments = segments
        self.data = [['number', 'type', 'direction']]
        for segment in self.segments:
            self.data[0].append(segment['description'])

    def store_quality(self, route: Route, route_info: Timetable):
        quality_route = [route.get_name(), route.get_equipment().to_number(), route_info.get_direction()]
        for segment in self.segments:
            quality_route.append(calculate_quality(route_info, segment['from'], segment['to']))
        self.data.append(quality_route)

    def save(self, filename: str):
        qualities_pd = pandas.DataFrame(self.data)
        qualities_pd.to_csv(filename, index=None, header=False)


def calculate_quality(route_info: Timetable, start_time=datetime.time(7, 0, 0),
                      end_time=datetime.time(21, 0, 0)) -> (str, int, int, int):
    max_quality = -1
    for timetable in route_info:
        prev_time = None
        for time in sorted(timetable.get_times(), key=lambda t: t.get_time()):
            if start_time <= time.get_time() <= end_time:
                if not (prev_time is None):
                    diff = time.get_time().minute + time.get_time().hour * 60 - (prev_time.minute + prev_time.hour * 60)
                    if diff > max_quality:
                        max_quality = diff
                prev_time = time.get_time()
    return max_quality


def store_route_new_info(repository: Repository, route: Route, route_info: Timetable, date: datetime.date,
                         direction: int,
                         printer: Printer() = PrinterConsole()):
    prepared_route_info = list(route_info)
    routes_info = repository.load_routes_info_by_number(route.get_id_mgt(), direction)

    for candidate in routes_info:
        if candidate.get_stops() == prepared_route_info:
            return
    printer.print("New timetable for route with id {}".format(route_info.get_id_route_t_mos_ru()))

    event_logger = Service_locator.get_instance().get_service('event_logger')
    event_logger.register_event(New_timetable_event(route, route_info, direction))

    store_route_info_with_adding_stops(repository, route.get_id_mgt(), route_info, date, direction)


def loading(date: datetime.date, work_time: int, direction: int, repository: Repository,
            quality_storage: Quality_storage) -> object:
    routes = get_and_store_routes_list(repository, work_time=work_time, logger=LoggerPrint(), printer=PrinterConsole())
    for route in routes:
        route_info = get_route(date, route.get_id_mgt(), direction, logger=LoggerPrint())
        if route_info:
            quality_storage.store_quality(route, route_info)
            store_route_new_info(repository, route, route_info, date, direction)


def loading_continue(date: datetime.date, work_time: int, direction: int, repository: Repository,
                     quality_storage: Quality_storage):
    routes = repository.get_last_snapshot(work_time=work_time)

    for route in routes:
        routes_info = repository.load_routes_info_by_number(route.get_id_mgt(), direction)
        routes_filtered = list(filter(lambda timetable: timetable.get_date().date() == date, routes_info))
        if len(routes_filtered) > 0:
            route_info = routes_filtered[0]
            print("Route {} load from database".format(route.get_name()))
        else:
            route_info = get_route(date, route.get_id_mgt(), direction, logger=LoggerPrint())
            print("Route {} load got from service".format(route.get_name()))
            if route_info:
                store_route_new_info(repository, route, route_info, date, direction)
        if route_info:
            quality_storage.store_quality(route, route_info)


def get_and_store_routes_list(repository: Repository, work_time: int, logger: Logger, printer: Printer):
    list_routes = get_list_routes(direction=0, work_time=work_time, logger=logger)

    routes_old = repository.get_last_snapshot(work_time=work_time)
    event_logger = Service_locator.get_instance().get_service('event_logger')
    change = False
    for route in list_routes:
        if not (route in routes_old):
            printer.print("New route: {}".format(route.get_name()))
            event_logger.register_event(New_route_event(route))
            change = True
    for route in routes_old:
        if not (route in list_routes):
            printer.print("Drop route: {}".format(route.get_name()))
            event_logger.register_event(Drop_route_event(route.get_name(), route.get_equipment().to_number()))
            change = True

    if change:
        repository.create_snapshot_routes(list_routes, work_time=work_time)
    return list_routes


def store_route_info_with_adding_stops(repository: Repository, num_route: str, route_info: Timetable,
                                       date: datetime.date,
                                       direction: int) -> None:
    new_stops = []
    stops = [(stop.get_name(),) for stop in route_info]
    old_stops = [(stop.get_name(),) for stop in repository.get_all_stops()]

    event_logger = Service_locator.get_instance().get_service('event_logger')

    for stop in stops:
        if not (stop in old_stops):
            event_logger.register_event(New_stop_event(stop[0]))
            new_stops.append(stop)
    if new_stops:
        repository.store_routes(new_stops)

    repository.store_route_info(date, direction, num_route, route_info)
