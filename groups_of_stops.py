import logging
import datetime
import marshal

from moscow_routes_parser.model import Route, Equipment
from moscow_routes_parser.model_impl import Timetable_builder_t_mos_ru

from repository_sqlite import Repository_sqlite
from tools import Quality_storage

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
repository = Repository_sqlite('mosgortrans_20220115.sqlite')

work_time = 1
date = datetime.date(2022, 3, 12)

routes = repository.get_last_snapshot(work_time=work_time)


def has_intersection_3_and_more(route1, route2):
    stops1 = list(map(lambda stop: stop.get_stop(), route1.get_stops()))
    stops2 = list(map(lambda stop: stop.get_stop(), route2.get_stops()))

    stops1_3 = []
    for i in range(0, len(stops1) - 2):
        stops1_3.append(stops1[i:i + 3])

    stops2_3 = []
    for i in range(0, len(stops2) - 2):
        stops2_3.append(stops2[i:i + 3])

    for s in stops1_3:
        if s in stops2_3:
            #            print("{}-{}-{}".format(s[0].get_name(),s[1].get_name(),s[2].get_name()))
            yield (s[0], s[1], s[2])

    return False


#routes = routes[0:10]

routes_info = []
for route in routes:
    route_info = repository.load_routes_info_by_number_and_date(route.get_id_mgt(), 0, date)
    if not (route_info is None):
        routes_info.append((route, 0, route_info))
    route_info = repository.load_routes_info_by_number_and_date(route.get_id_mgt(), 1, date)
    if not (route_info is None):
        routes_info.append((route, 1, route_info))
    print("Loaded {}".format(route.get_name()))

dict_result = {}
for i in range(0, len(routes_info)):
    print("Search intersections with {}".format(routes_info[i][0]))
    for j in range(i + 1, len(routes_info)):
        for inters in has_intersection_3_and_more(routes_info[i][2], routes_info[j][2]):
            if inters in dict_result:
                dict_result[inters].append((routes_info[j][0], routes_info[j][1]))
            else:
                dict_result[inters] = [(routes_info[i][0], routes_info[i][1]), ((routes_info[j][0], routes_info[j][1]))]

# file = open("ïnters.dat","w")
# marshal.dump(dict_result,file)
# file.close()

group_routes_ranges = []
for k in dict_result.keys():
    flag = True
    for g in group_routes_ranges:
        if g[0] == dict_result[k]:
            g[1].append(k)
            flag = False
    if flag:
        group_routes_ranges.append((dict_result[k], [k]))


def rebuild(list_triples):
    result = []
    for i in list_triples:
        added = False
        for r in result:
            if r[0] == i[1] and r[1] == i[2]:
                r.insert(0, i[0])
                added = True
            if r[-1] == i[1] and r[-2] == i[0]:
                r.append(i[2])
                added = True
        if not added:
            result.append([i[0], i[1], i[2]])
    return result


group_routes_ranges = map(lambda item: (item[0], rebuild(item[1])), group_routes_ranges)

result = list(group_routes_ranges)

quality_storage= Quality_storage()
for gr in result:
    for parts in gr[1]:
        route_group = Route(-1, Equipment(-1), "+".join(list(map(lambda r: r[0].get_name(), gr[0])))+": "+parts[0].get_name()+"-"+parts[-1].get_name())
        timetable_builder = Timetable_builder_t_mos_ru()
        timetable_builder.set_id_route_t_mos_ru(-1).set_date(date).set_direction(-1)
        for s in parts:
            stop = timetable_builder.add_stop()
            stop.set_name(s.get_name())
            stop.set_coords(s.get_coords())
            for route in gr[0]:
                routes_found = list(filter(lambda r: r[0]==route[0] and r[1]==route[1],routes_info))
                route_found=routes_found[0]
                times_all = list(filter(lambda r: r.get_stop()==s,route_found[2].get_stops()))
                times = times_all[0].get_times()
                for t in times:
                    stop.add_item_timetable(t.get_time(),t.get_color_special_flight())
        timetable = timetable_builder.build()
        quality_storage.store_quality(route_group,timetable)
quality_storage.save('groups_qualities.csv')
