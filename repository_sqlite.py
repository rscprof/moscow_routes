import datetime
import sqlite3

from model import Timetable_stop_builder, Route, Equipment, Timetable, Stop_builder, Stop
from model_impl import Timetable_stop_builder_t_mos_ru, Stop_builder_impl
from repository import Repository


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
                cur3.execute("SELECT time,color FROM route_stop_times where id_route_stop=? ORDER BY time", (stop[2],))
                for time_info in cur3.fetchall():
                    builder.add_item_timetable(datetime.time(time_info[0] // 60, time_info[0] % 60), time_info[1])
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
            cur.executemany("INSERT INTO route_stop_times(id_route_stop,time,color) VALUES(?,?,?)",
                            [(id_route_stop, time.get_time().minute + time.get_time().hour * 60,
                              time.get_color_special_flight()) for time in
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
        self.connection.execute("CREATE TABLE IF NOT EXISTS route_stop_times (id_route_stop INT,time INT,color TEXT)")

        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS timetable(data_services INT,date REAL,date_store REAL,route INT,direction INT)")

    def __init__(self, filename="mosgortrans.sqlite"):
        self.connection = sqlite3.connect(filename)
        self.create_tables()
