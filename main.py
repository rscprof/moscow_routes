# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import re
from time import sleep

import pandas
import pandas as pd

import requests
import sqlite3
import datetime

get_routes_url = 'https://transport.mos.ru/ru/ajax/App/ScheduleController/getRoutesList'
get_route_url = 'https://transport.mos.ru/ru/ajax/App/ScheduleController/getRoute'

type_route_bus = 0
type_route_tramway = 1
type_route_trolleybus = 2


def parse_routes(text):
    result = re.finditer(r'<a.*?href=.*?route/(\d+).*?<div.*?ic[ ]([a-z-]+).*?</i>\s*(\S+?)\s*</div>', text,
                         re.M + re.S)
    list_routes = []

    for route in result:
        num = int(route.group(1))
        type_route = route.group(2)
        if type_route.find('-bus') >= 0:
            type_route = type_route_bus
        elif type_route.find('tramway') >= 0:
            type_route = type_route_tramway
        elif type_route.find('trolleybus') >= 0:
            type_route = type_route_trolleybus
        else:
            print("Debug: {}".format(type_route))
            type_route = None
        name = route.group(3)
        list_routes.append({'num': num, 'type': type_route, 'name': name})
    return list_routes


def get_routes():
    try:
        page = 1
        result_routes = []
        while True:
            sleep(1)
            response = requests.get(get_routes_url,
                                    params={
                                        'mgt_schedule[search]': '',
                                        'mgt_schedule[filters]': '',
                                        'mgt_schedule[work_time]': 1,
                                        'mgt_schedule[page]': page,
                                        'mgt_schedule[direction]': 0,
                                    }
                                    )
            if response.status_code == 200:
                print("Get page #{}".format(page))
                routes = parse_routes(response.text)
                result_routes += routes
                if not routes:
                    break
            else:
                print("Error status: {}".format(response.status_code))
            page = page + 1
    except Exception:
        print("Error")
        result_routes = None

    return result_routes


def create_tables(connection):
    connection.execute("CREATE TABLE IF NOT EXISTS snapshot_list_routes (datetime REAL)")
    connection.execute("CREATE TABLE IF NOT EXISTS routes (snapshot INT,name TEXT,type INT,id INT)")
    connection.execute("CREATE TABLE IF NOT EXISTS stops (id_stop TEXT,name TEXT)")
    connection.execute("CREATE TABLE IF NOT EXISTS route_stop (ord INT,id_stop INT,id_timetable INT)")
    connection.execute("CREATE TABLE IF NOT EXISTS route_stop_times (id_route_stop INT,time INT,red INT)")

    connection.execute(
        "CREATE TABLE IF NOT EXISTS timetable(data_services INT,date REAL,date_store REAL,route INT,direction INT)")


def get_all_stops(connection):
    cur = connection.cursor()
    cur.execute("SELECT rowid,id_stop,name FROM stops")
    return [{'id': stop[0], 'id_stop': stop[1], 'name': stop[2]} for stop in cur.fetchall()]


def store_route_info(connection, num_route, route_info, date, direction):
    cur = connection.cursor()
    new_stops = []
    stops = [(stop['id'], stop['name']) for stop in route_info]
    old_stops = [(stop['id_stop'], stop['name']) for stop in get_all_stops(connection)]
    for stop in stops:
        if not (stop in old_stops):
            # print("new stop: {}", stop)
            new_stops.append(stop)
    if new_stops:
        cur.executemany('INSERT INTO stops(id_stop,name) VALUES (?,?)', new_stops)
        connection.commit()

    stops = get_all_stops(connection)

    cur.execute("SELECT MAX(rowid) FROM routes WHERE id=?", (num_route,))
    id_route = cur.fetchone()[0]

    cur.execute("INSERT INTO timetable(data_services,date,date_store,route,direction) VALUES (?,?,?,?,?)",
                (route_info[0]['data-services'], datetime.datetime.combine(date,datetime.time(0,0,0)).timestamp(), datetime.datetime.now().timestamp(), id_route, direction))
    id_timetable = cur.lastrowid

    num = 1
    for stop in route_info:
        id_stop = list(filter(lambda x: x['id_stop'] == stop['id'], stops))[-1]['id']
        cur.execute("INSERT INTO route_stop(ord,id_stop,id_timetable) VALUES(?,?,?)",(num,id_stop,id_timetable))
        id_route_stop = cur.lastrowid
        cur.executemany("INSERT INTO route_stop_times(id_route_stop,time,red) VALUES(?,?,?)",
                        [(id_route_stop,time['time'].minute+time['time'].hour*60,time['red']) for time in stop['timetable']]
                        )
        num=num+1
    connection.commit()

def create_snapshot_routes(connection, routes):
    now = datetime.datetime.now().timestamp()
    cur = connection.cursor()
    cur.execute("INSERT INTO snapshot_list_routes(datetime) VALUES(?)", (datetime.datetime.now().timestamp(),))
    id_snapshot = cur.lastrowid
    routes_for_insert = [(id_snapshot, x['name'], x['type'], x['num']) for x in routes]
    cur.executemany('INSERT INTO routes(snapshot,name,type,id) VALUES (?,?,?,?)', routes_for_insert)
    connection.commit()


def get_last_snapshot(connection):
    cur = connection.cursor()
    cur.execute("SELECT MAX(rowid) FROM snapshot_list_routes")
    id = cur.fetchone()[0]
    cur.execute("SELECT name,type,id FROM routes WHERE snapshot=?", (id,))
    return [{'name': route[0], 'type': route[1], 'num': route[2]} for route in cur.fetchall()]


def test_routes_list(connection):
    routes = get_routes()
    routes_old = get_last_snapshot(connection)
    change = False
    for route in routes:
        if not (route in routes_old):
            print("New route: {}".format(route))
            change = True
    for route in routes_old:
        if not (route in routes):
            print("Drop route: {}".format(route))
            change = True

    if change:
        create_snapshot_routes(connection, routes)
    return routes


def parse_route_info(text):
    result_stops = []
    stops = re.finditer(r'data-stop="(.*?)".*?data-services="(.*?)".*?d-inline.*?\>(.*?)<(.*?)</li>', text, re.M + re.S
                        )

    for stop in stops:
        id_stop = stop.group(1)
        data_services = stop.group(2)
        name_stop = stop.group(3)
        description = stop.group(4)
        # print(name_stop)
        hours = re.finditer(r'dt1.*?(\d\d):(.*?)</div>\s*</div>\s*</div>', description, re.M + re.S)
        timetable = []
        for hour in hours:
            num_hour = int(hour.group(1))
            minutes_text = hour.group(2)
            # print(num_hour, end=": ")
            minutes = re.finditer(r'div10([^>]*)>\s*(\d\d)', minutes_text, re.M + re.S)
            for minute in minutes:
                num_minute = int(minute.group(2))
                if minute.group(1).find('red') >= 0:
                    min_red = True
                else:
                    min_red = False
                if min_red:
                    # print("{}red".format(num_minute), end=" ")
                    pass
                else:
                    # print(num_minute, end=" ")
                    pass
                time = datetime.time(num_hour, num_minute)
                timetable.append({'time': time, 'red': min_red})
            # print()
        result_stops.append(
            {'id': id_stop, 'data-services': data_services, 'name': name_stop, 'timetable': timetable})
    return result_stops


def get_route(date, route, direction):
    try:
        response = requests.get(get_route_url,
                                params={
                                    'mgt_schedule[date]': date.strftime("%d.%m.%Y"),
                                    'mgt_schedule[route]': route,
                                    'mgt_schedule[page]': '',
                                    'mgt_schedule[direction]': direction,
                                }
                                )
        if response.status_code == 200:
            print("Get route #{}".format(route))
            route_info = parse_route_info(response.text)
        else:
            print("Error status: {}".format(response.status_code))
    except Exception:
        print("Error")
        route_info = None

    return route_info

def test_quality(route, route_info):
    max = -1
    if route_info:
        timetable = route_info[0]['timetable']
        prevtime = None
        for time in timetable:
            if datetime.time(7, 0, 0) <= time['time'] <= datetime.time(21, 0, 0):
                if not (prevtime is None):
                    diff = time['time'].minute + time['time'].hour * 60 - (prevtime.minute + prevtime.hour * 60)
                    if diff > max:
                        max = diff
                prevtime = time['time']
        print("Route {} ({}) has quality {}".format(route['name'], route['type'], max))
    return (route['name'], route['type'],max)

def load_routes_info_by_number(connection, num_route,direction):
    cur = connection.cursor()
    cur.execute("SELECT MAX(rowid) FROM routes WHERE id=?", (num_route,))
    id_route = cur.fetchone()[0]
    result = []
    cur.execute("SELECT data_services,date,date_store,rowid FROM timetable WHERE route=? and direction=?",(id_route,direction,))
    for timetable in cur.fetchall():
        id_timetable = timetable[3]
        cur2 = connection.cursor()
        cur2.execute("SELECT stops.id_stop,stops.name,route_stop.rowid FROM route_stop INNER JOIN stops ON (stops.rowid=route_stop.id_stop) WHERE id_timetable=? ORDER BY ord",(id_timetable,))
        stops = []
        for stop in cur2.fetchall():
            cur3 = connection.cursor()
            cur3.execute("SELECT time,red FROM route_stop_times where id_route_stop=?",(stop[2],))
            times = list(map((lambda timeinfo: {'time': datetime.time(timeinfo[0]//60,timeinfo[0]%60),'red': timeinfo[1]}),list(cur3.fetchall())))
            stops.append({'timetable':times,'name': stop[1],'id': stop[0]})


        result.append({'data-services': timetable[0],'date': datetime.datetime.fromtimestamp(timetable[1]),
                       'date_store':datetime.datetime.fromtimestamp(timetable[2]),
                       'stops': stops
                       })

    return result



connection = sqlite3.connect("mosgortrans.sqlite")
create_tables(connection)
#routes = test_routes_list(connection)
routes = get_last_snapshot(connection)





for route in routes:
    routes_info = load_routes_info_by_number(connection,route['num'],0)
    print(routes_info)
#    qualities.append(test_quality(route,route_info))
#    if route_info:
#        store_route_info(connection,route['num'],route_info,datetime.date(2022, 1, 14),0)
qualities_pd = pandas.DataFrame(qualities)
qualities_pd.to_csv('qualities.csv')



# qualities=[]
# for route in routes:
#     route_info = get_route(datetime.date(2022, 1, 14), route['num'], 0)
#     qualities.append(test_quality(route,route_info))
#     if route_info:
#         store_route_info(connection,route['num'],route_info,datetime.date(2022, 1, 14),0)
# qualities_pd = pandas.DataFrame(qualities)
# qualities_pd.to_csv('qualities.csv')


# routed_data = pd.DataFrame(routes)
# routed_data.to_csv('routes.csv')
# routes_data=pd.read_csv('routes.csv')
# routes = routes_data.to_dict()
# print(routes)
# print([route for route in routes if route['type']==0])


#route_info = parse_route_info(example)

#store_route_info(connection, 393, route_info, datetime.date(2022, 1, 14), 0)
