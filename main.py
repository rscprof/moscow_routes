# This is a sample Python script.

import datetime
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas

from logger import LoggerPrint, Logger
from model import Route, Timetable
from printer import Printer, PrinterConsole
from repository import Repository
from repository_sqlite import Repository_sqlite
from t_mos_ru import get_route, get_list_routes


def get_and_store_routes_list(repository: Repository, work_time: int, logger: Logger, printer: Printer):
    list_routes = get_list_routes(direction=0, work_time=work_time, logger=logger)

    routes_old = repository.get_last_snapshot(work_time=work_time)

    change = False
    for route in list_routes:
        if not (route in routes_old):
            printer.print("New route: {}".format(route.get_name()))
            change = True
    for route in routes_old:
        if not (route in list_routes):
            printer.print("Drop route: {}".format(route.get_name()))
            change = True

    if change:
        repository.create_snapshot_routes(list_routes, work_time=work_time)
    return list_routes


def calculate_quality(route: Route, route_info: Timetable, start_time=datetime.time(7, 0, 0),
                      end_time=datetime.time(21, 0, 0)) -> (str, int, int):
    max_quality = -1
    if route_info:
        timetable = list(route_info)[0]
        prev_time = None
        for time in filter(lambda t: t.get_color_special_flight() is None,
                           sorted(timetable.get_times(), key=lambda t: t.get_time())):
            if start_time <= time.get_time() <= end_time:
                if not (prev_time is None):
                    diff = time.get_time().minute + time.get_time().hour * 60 - (prev_time.minute + prev_time.hour * 60)
                    if diff > max_quality:
                        max_quality = diff
                prev_time = time.get_time()
        print("Route {} ({}) has quality {}".format(route.get_name(), route.get_equipment().to_str(), max_quality))
    return route.get_name(), route.get_equipment().to_number(), max_quality


# for route in routes:
#     routes_info = load_routes_info_by_number(connection,route['num'],0)
#     print(routes_info)
# #    qualities.append(test_quality(route,route_info))
# #    if route_info:
# #        store_route_info(connection,route['num'],route_info,datetime.date(2022, 1, 14),0)
# qualities_pd = pandas.DataFrame(qualities)
# qualities_pd.to_csv('qualities.csv')


#
#
def store_route_new_info(repository: Repository, num_route: str, route_info: Timetable, date: datetime.date,
                         direction: int,
                         printer: Printer() = PrinterConsole()):
    prepared_route_info = list(route_info)
    routes_info = repository.load_routes_info_by_number(num_route, direction)

    for candidate in routes_info:
        if candidate['stops'] == prepared_route_info:
            return
    printer.print("New timetable for route with id {}".format(route_info.get_id_route_t_mos_ru()))
    repository.store_route_info(num_route, route_info, date, direction)


def loading(date: datetime.date, work_time: int, direction: int, repository: Repository):
    routes = get_and_store_routes_list(repository, work_time=work_time, logger=LoggerPrint(), printer=PrinterConsole())
    # routes = repository.get_last_snapshot(work_time=1)

    qualities = []
    for route in routes:
        route_info = get_route(date, route.get_id_mgt(), direction, logger=LoggerPrint())
        qualities.append(calculate_quality(route, route_info))
        if route_info:
            store_route_new_info(repository, route.get_id_mgt(), route_info, date, direction)
    qualities_pd = pandas.DataFrame(qualities)
    qualities_pd.to_csv('qualities_' + date.strftime("%Y%m%d") + '.csv')


def loading_continue(date: datetime.date, work_time: int, direction: int, repository: Repository):
    # routes = get_and_store_routes_list(repository, work_time=work_time, logger=LoggerPrint(), printer=PrinterConsole())
    routes = repository.get_last_snapshot(work_time=work_time)

    qualities = []
    for route in routes:
        routes_info = repository.load_routes_info_by_number(route.get_id_mgt(), direction)
        routes_filtered = list(filter(lambda timetable: timetable['date'].date() == date, routes_info))
        if len(routes_filtered) > 0:
            route_info = routes_filtered[0]['stops']
            print("Route {} load from database".format(route.get_name()))
        else:
            route_info = get_route(date, route.get_id_mgt(), direction, logger=LoggerPrint())
            print("Route {} load got from service".format(route.get_name()))
            if route_info:
                store_route_new_info(repository, route.get_id_mgt(), route_info, date, direction)
        qualities.append(calculate_quality(route, route_info))
    qualities_pd = pandas.DataFrame(qualities)
    qualities_pd.to_csv('qualities_' + date.strftime("%Y%m%d") + '.csv')


repository = Repository_sqlite('mosgrortrans_20220114.sqlite')
loading_continue(datetime.date(2022, 1, 16), 1, 0, repository)

# routes_info = repository.load_routes_info_by_number(2198, 0)

# routes_filtered = list(filter(lambda timetable: timetable['date'].date() == datetime.date(2022, 1, 16), routes_info))
# print(routes_filtered)


# routed_data = pd.DataFrame(routes)
# routed_data.to_csv('routes.csv')
# routes_data=pd.read_csv('routes.csv')
# routes = routes_data.to_dict()
# print(routes)
# print([route for route in routes if route['type']==0])


# route_info = parse_route_info(example)

# store_route_info(connection, 393, route_info, datetime.date(2022, 1, 14), 0)
