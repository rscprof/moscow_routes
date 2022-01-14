# This is a sample Python script.

import datetime
import sqlite3
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from abc import abstractmethod

import pandas

from logger import LoggerPrint, Logger
from model import Stop, Stop_builder, Route, Equipment, Timetable, Timetable_stop_builder
from model_impl import Stop_builder_impl, Timetable_stop_builder_t_mos_ru
from printer import Printer, PrinterConsole
from t_mos_ru import get_route, get_list_routes


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


class Repository_sqlite(Repository):
    def load_routes_info_by_number(self, num_route: int, direction: int,
                                   timetable_stop_builder: Timetable_stop_builder = Timetable_stop_builder_t_mos_ru
                                   ):
        cur = self.connection.cursor()
        cur.execute("SELECT MAX(rowid) FROM routes WHERE id=?", (num_route,))
        id_route = cur.fetchone()[0]
        result = []
        cur.execute("SELECT date,date_store,rowid FROM timetable WHERE route=? and direction=?",
                    (id_route, direction,))
        for timetable in cur.fetchall():
            id_timetable = timetable[2]
            cur2 = self.connection.cursor()
            cur2.execute(
                "SELECT stops.id_stop,stops.name,route_stop.rowid FROM route_stop INNER JOIN stops ON (stops.rowid=route_stop.id_stop) WHERE id_timetable=? ORDER BY ord",
                (id_timetable,))

            stops = []
            for stop in cur2.fetchall():
                builder = timetable_stop_builder()
                cur3 = self.connection.cursor()
                cur3.execute("SELECT time,red FROM route_stop_times where id_route_stop=? ORDER BY time", (stop[2],))
                for time_info in cur3.fetchall():
                    builder.add_item_timetable(datetime.time(time_info[0] // 60, time_info[0] % 60), bool(time_info[1]))
                builder.set_name(stop[1]).set_id_stop_t_mos_ru(stop[0])
                stops.append(builder.build())

            result.append({'date': datetime.datetime.fromtimestamp(timetable[0]),
                           'date_store': datetime.datetime.fromtimestamp(timetable[1]),
                           'stops': stops
                           })

        return result

    def create_snapshot_routes(self, routes: list[Route], work_time: int, datetime_create=datetime.datetime.now()):
        now = datetime_create.timestamp()
        cur = self.connection.cursor()
        cur.execute("INSERT INTO snapshot_list_routes(datetime,work_time) VALUES(?,?)", (now, work_time,))
        id_snapshot = cur.lastrowid
        routes_for_insert = [(id_snapshot, x.get_name(), x.get_equipment().to_number(), x.get_id_mgt()) for x in routes]
        cur.executemany('INSERT INTO routes(snapshot,name,type,id) VALUES (?,?,?,?)', routes_for_insert)
        self.connection.commit()

    def get_last_snapshot(self, work_time: int) -> list[Route]:
        cur = self.connection.cursor()
        cur.execute("SELECT MAX(rowid) FROM snapshot_list_routes WHERE work_time=?", (work_time,))
        last_id = cur.fetchone()[0]
        cur.execute("SELECT name,type,id FROM routes WHERE snapshot=?", (last_id,))

        return [Route(route[2], Equipment.by_number(route[1]), route[0]) for route in cur.fetchall()]

    def store_route_info(self, num_route: str, route_info: Timetable, date: datetime.date,
                         direction: int) -> None:
        cur = self.connection.cursor()
        new_stops = []
        stops = [(stop.get_id_stop_t_mos_ru(), stop.get_name()) for stop in route_info]
        old_stops = [(stop.get_id_stop_t_mos_ru(), stop.get_name()) for stop in self.get_all_stops()]
        for stop in stops:
            if not (stop in old_stops):
                # print("new stop: {}", stop)
                new_stops.append(stop)
        if new_stops:
            cur.executemany('INSERT INTO stops(id_stop,name) VALUES (?,?)', new_stops)
            self.connection.commit()

        stops = self.get_all_stops()

        cur.execute("SELECT MAX(rowid) FROM routes WHERE id=?", (num_route,))
        id_route = cur.fetchone()[0]

        cur.execute("INSERT INTO timetable(date,date_store,route,direction) VALUES (?,?,?,?)",
                    (
                        datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp(),
                        datetime.datetime.now().timestamp(), id_route, direction))
        id_timetable = cur.lastrowid

        num = 1
        for stop in route_info:
            id_stop = list(filter(lambda x: x.get_id_stop_t_mos_ru() == stop.get_id_stop_t_mos_ru(), stops))[
                -1].get_id()
            cur.execute("INSERT INTO route_stop(ord,id_stop,id_timetable) VALUES(?,?,?)", (num, id_stop, id_timetable))
            id_route_stop = cur.lastrowid
            cur.executemany("INSERT INTO route_stop_times(id_route_stop,time,red) VALUES(?,?,?)",
                            [(id_route_stop, time.get_time().minute + time.get_time().hour * 60,
                              time.check_special_flight()) for time in
                             stop.get_times()]
                            )
            num = num + 1
        self.connection.commit()

    def get_all_stops(self, builder: Stop_builder = Stop_builder_impl()) -> [Stop]:
        cur = self.connection.cursor()
        cur.execute("SELECT rowid,id_stop,name FROM stops")
        return [builder.set_id_stop_t_mos_ru(stop[1]).set_id(stop[0]).set_name(stop[2]).build() for stop in
                cur.fetchall()]

    def create_tables(self):
        self.connection.execute("CREATE TABLE IF NOT EXISTS snapshot_list_routes (datetime REAL,work_time INT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS routes (snapshot INT,name TEXT,type INT,id INT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS stops (id_stop TEXT,name TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS route_stop (ord INT,id_stop INT,id_timetable INT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS route_stop_times (id_route_stop INT,time INT,red INT)")

        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS timetable(data_services INT,date REAL,date_store REAL,route INT,direction INT)")

    def __init__(self, filename="mosgortrans.sqlite"):
        self.connection = sqlite3.connect(filename)
        self.create_tables()


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


def calculate_quality(route: Route, route_info: Timetable) -> (str, int, int):
    max_quality = -1
    if route_info:
        timetable = list(route_info)[0]
        prev_time = None
        for time in timetable.get_times():
            if datetime.time(7, 0, 0) <= time.get_time() <= datetime.time(21, 0, 0):
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
    qualities_pd.to_csv('qualities_' + date.strftime() + '.csv')


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
    qualities_pd.to_csv('qualities_' + date.strftime() + '.csv')


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
loading(datetime.date(2022, 1, 16), 1, 0, repository)
#routes_info = repository.load_routes_info_by_number(2130, 0)
#routes_filtered = list(filter(lambda timetable: timetable['date'].date() == datetime.date(2022, 1, 16), routes_info))
#print(routes_filtered)

# routed_data = pd.DataFrame(routes)
# routed_data.to_csv('routes.csv')
# routes_data=pd.read_csv('routes.csv')
# routes = routes_data.to_dict()
# print(routes)
# print([route for route in routes if route['type']==0])


# route_info = parse_route_info(example)

# store_route_info(connection, 393, route_info, datetime.date(2022, 1, 14), 0)
