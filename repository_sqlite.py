import copy
import datetime
import sqlite3
from typing import Optional, Tuple

from moscow_routes_parser.model import Timetable_builder, Timetable, Timetable_stop_builder, Route, Equipment, \
    Stop_builder, Stop
from moscow_routes_parser.model_impl import Timetable_builder_t_mos_ru, Timetable_stop_builder_t_mos_ru, \
    Stop_builder_impl

from model.model_with_id import Timetable_builder_decorator_with_id, Timetable_with_id, Stop_builder_decorator_with_id
from repository import Repository


# Тут есть и логика репозитория и логика обновления в store_route_info -> надо отделить одно от другого при рефакторинге


class Repository_sqlite(Repository):
    def load_routes_info_by_number_type_and_date(self, num_route: str, type_route: int, direction: int,
                                                 date: datetime.date,
                                                 timetable_builder: Timetable_builder_decorator_with_id =
                                                 Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                                 ) -> \
            Optional[Timetable_with_id]:
        cur = self.connection.cursor()

        cur.execute("SELECT route_timetable_date.id_timetable,timetable.date FROM route_timetable_date INNER JOIN "
                    "timetable "
                    "ON (timetable.rowid = route_timetable_date.id_timetable) INNER JOIN routes ON "
                    "(routes.rowid=route_timetable_date.id_route)"
                    "WHERE routes.name=? and routes.type=? and route_timetable_date.direction=? and "
                    "route_timetable_date.date=?",
                    (num_route, type_route, direction,
                     datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp()))
        id_timetables = list(cur.fetchall())
        if len(id_timetables) == 0:
            result = None
        else:

            id_timetable = id_timetables[0][0]
            date = id_timetables[0][1]
            result = self.load_timetable(direction, id_timetable,
                                         datetime.datetime.fromtimestamp(date),
                                         timetable_builder)

        return result

    def load_routes_info_by_number_and_date(self, num_route: int, direction: int, date: datetime.date,
                                            timetable_builder: Timetable_builder = Timetable_builder_t_mos_ru()
                                            ) -> \
            Optional[Timetable]:
        cur = self.connection.cursor()

        cur.execute("SELECT route_timetable_date.id_timetable,timetable.date FROM route_timetable_date INNER JOIN "
                    "timetable "
                    "ON (timetable.rowid = route_timetable_date.id_timetable) INNER JOIN routes ON "
                    "(routes.rowid=route_timetable_date.id_route)"
                    "WHERE routes.id=? and route_timetable_date.direction=? and "
                    "route_timetable_date.date=?",
                    (num_route, direction, datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp()))
        id_timetables = list(cur.fetchall())
        if len(id_timetables) == 0:
            result = None
        else:

            id_timetable = id_timetables[0][0]
            date = id_timetables[0][1]
            result = self.load_timetable(direction, id_timetable,
                                         datetime.datetime.fromtimestamp(date),
                                         timetable_builder)

        return result

    def store_route_timetable_date(self, num_route: str, direction: int, date: datetime.date,
                                   id_timetable: int) -> None:
        # store version of timetable of route/direction for date
        cur = self.connection.cursor()
        cur.execute("SELECT MAX(rowid) FROM routes WHERE id=?", (num_route,))
        id_route = cur.fetchone()[0]

        cur.execute("SELECT id_timetable FROM route_timetable_date WHERE id_route=? and direction=? and date=?",
                    (id_route, direction, datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp()))
        if len(list(cur.fetchall())) == 0:
            cur.execute("INSERT INTO route_timetable_date (id_route, direction, date, id_timetable) VALUES (?,?,?,?)",
                        (
                            id_route, direction,
                            datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp(),
                            id_timetable))
        else:
            cur.execute("UPDATE route_timetable_date SET id_timetable=? WHERE id_route=? and direction=? and date=?",
                        (id_timetable,
                         id_route, direction,
                         datetime.datetime.combine(date, datetime.time(0, 0, 0)).timestamp(),
                         ))
        self.connection.commit()

    def load_routes_info_by_number(self, num_route: int, direction: int,
                                   timetable_stop_builder: Timetable_stop_builder = Timetable_stop_builder_t_mos_ru(),
                                   timetable_builder: Timetable_builder_decorator_with_id =
                                   Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                   ) -> list[Timetable_with_id]:
        cur = self.connection.cursor()
        result = []
        cur.execute(
            "SELECT date,date_store,timetable.rowid FROM timetable INNER JOIN routes ON (routes.rowid=timetable.route) WHERE routes.id=? and direction=?",
            (num_route, direction,))
        for timetable in cur.fetchall():
            id_timetable = timetable[2]
            loaded_timetable = self.load_timetable(direction, id_timetable,
                                                   datetime.datetime.fromtimestamp(timetable[0]),
                                                   timetable_builder)

            result.append(loaded_timetable)
        return result

    def load_routes_info_by_number_and_type(self, num_route: str, type_route: int, direction: int,
                                            timetable_stop_builder: Timetable_stop_builder = Timetable_stop_builder_t_mos_ru(),
                                            timetable_builder: Timetable_builder_decorator_with_id =
                                            Timetable_builder_decorator_with_id(Timetable_builder_t_mos_ru())
                                            ) -> list[Timetable_with_id]:
        cur = self.connection.cursor()
        result = []
        cur.execute(
            "SELECT date,date_store,timetable.rowid FROM timetable INNER JOIN routes ON (routes.rowid=timetable.route) WHERE routes.name=? and routes.type=? and direction=?",
            (num_route, type_route, direction,))
        for timetable in cur.fetchall():
            id_timetable = timetable[2]
            loaded_timetable = self.load_timetable(direction, id_timetable,
                                                   datetime.datetime.fromtimestamp(timetable[0]),
                                                   timetable_builder)

            result.append(loaded_timetable)
        return result

    def load_timetable(self, direction: int, id_timetable: int,
                       date, timetable_builder: Timetable_builder_decorator_with_id) -> Timetable_with_id:
        cur2 = self.connection.cursor()
        cur2.execute(
            "SELECT stops.name,stops.coord0, stops.coord1, route_stop.rowid FROM route_stop INNER JOIN stops ON (stops.rowid=route_stop.id_stop) WHERE id_timetable=? ORDER BY ord",
            (id_timetable,))
        # stops = []
        timetable_builder = copy.deepcopy(timetable_builder)
        timetable_builder.set_direction(direction).set_date(
            date).set_id_timetable(id_timetable)
        for stop in cur2.fetchall():
            builder = timetable_builder.add_stop()
            builder.set_name(stop[0])
            builder.set_coords(
                (None if stop[1] is None else float(stop[1]), None if stop[2] is None else float(stop[2])))

            cur3 = self.connection.cursor()
            cur3.execute("SELECT time,color FROM route_stop_times where id_route_stop=? ORDER BY time", (stop[3],))
            for time_info in cur3.fetchall():
                builder.add_item_timetable(datetime.time(time_info[0] // 60, time_info[0] % 60), time_info[1])
        return timetable_builder.build()

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

    def store_routes(self, route_names: list[Tuple[str, Tuple[float, float]]]):
        cur = self.connection.cursor()
        route_names = map(lambda t: (t[0], t[1][0], t[1][1]), route_names)
        cur.executemany('INSERT INTO stops(name,coord0,coord1) VALUES (?,?,?)', route_names)
        self.connection.commit()

    def store_route_info(self, date, direction, num_route, route_info) -> int:
        cur = self.connection.cursor()
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
            id_stop = list(filter(lambda x: x.get_name() == stop.get_name() and
                                            x.get_coords() == stop.get_coords()
                                  , stops))[
                -1].get_id()
            cur.execute("INSERT INTO route_stop(ord,id_stop,id_timetable) VALUES(?,?,?)", (num, id_stop, id_timetable))
            id_route_stop = cur.lastrowid
            cur.executemany("INSERT INTO route_stop_times(id_route_stop,time,color) VALUES(?,?,?)",
                            [(id_route_stop, time.get_time().minute + time.get_time().hour * 60,
                              time.get_color_special_flight()) for time in
                             stop.get_times()]
                            )
            num = num + 1
        self.connection.commit()
        return id_timetable

    def get_all_stops(self, builder: Stop_builder_decorator_with_id =
    Stop_builder_decorator_with_id(Stop_builder_impl())) -> [Stop]:
        cur = self.connection.cursor()
        cur.execute("SELECT rowid,name,coord0,coord1 FROM stops")
        return [builder.set_id(stop[0]).set_name(stop[1]).set_coords(
            [None if stop[2] is None else float(stop[2]), None if stop[3] is None else float(stop[3])]).build() for stop
                in
                cur.fetchall()]

    # id was int, now - string
    def create_tables(self):
        self.connection.execute("CREATE TABLE IF NOT EXISTS snapshot_list_routes (datetime REAL,work_time INT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS routes (snapshot INT,name TEXT,type INT,id TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS stops (name TEXT, coord0 REAL, coord1 REAL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS route_stop (ord INT,id_stop INT,id_timetable INT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS route_stop_times (id_route_stop INT,time INT,color TEXT)")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS route_timetable_date (id_route TEXT,direction INT,date REAL,id_timetable INT)")

        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS timetable(data_services INT,date REAL,date_store REAL,route INT,direction INT)")
        self.connection.execute(
            "create index if not exists timetable_index on route_stop(id_timetable);")
        self.connection.execute(
            "create index if not exists times_index on route_stop_times(id_route_stop);")
        self.connection.execute(
            "create index if not exists route_index on timetable(route,direction);")
        self.connection.execute(
            "create index if not exists route_timetable_date_index on route_timetable_date(id_route,direction,date);")

    def __init__(self, filename="mosgortrans.sqlite"):
        self.connection = sqlite3.connect(filename)
        self.create_tables()
