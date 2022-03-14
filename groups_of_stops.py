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
date = datetime.date(2022, 3, 14)

routes = repository.get_last_snapshot(work_time=work_time)


def has_intersection_2_and_more(route1, route2):
    stops1 = list(map(lambda stop: stop.get_stop(), route1.get_stops()))
    stops2 = list(map(lambda stop: stop.get_stop(), route2.get_stops()))

    stops1_3 = []
    for i in range(0, len(stops1) - 1):
        stops1_3.append(stops1[i:i + 2])

    stops2_3 = []
    for i in range(0, len(stops2) - 1):
        stops2_3.append(stops2[i:i + 2])

    for s in stops1_3:
        if s in stops2_3:
            #            print("{}-{}-{}".format(s[0].get_name(),s[1].get_name(),s[2].get_name()))
            yield s[0], s[1]


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
            yield s[0], s[1], s[2]


#routes = routes[0:30]

routes_info = {}
for route in routes:
    route_info = repository.load_routes_info_by_number_and_date(route.get_id_mgt(), 0, date)
    if not (route_info is None):
        routes_info[(route, 0)] = route_info
        # routes_info.append((route, 0, route_info))
    route_info = repository.load_routes_info_by_number_and_date(route.get_id_mgt(), 1, date)
    if not (route_info is None):
        routes_info[(route, 1)] = route_info
        # routes_info.append((route, 1, route_info))
    print("Loaded {}".format(route.get_name()))

dict_result = {}
# key of dict_result is pair of Stops
# value of dict_result is list of routes
# for i in range(0, len(routes_info)):
#     print("Search intersections with {}".format(routes_info[i][0]))
#     for j in range(i + 1, len(routes_info)):
#         has = False
#         for inters in has_intersection_2_and_more(routes_info[i][2], routes_info[j][2]):
#             has = True
#             if inters in dict_result:
#                 if not (routes_info[j][0], routes_info[j][1]) in dict_result[inters]:
#                     dict_result[inters].append((routes_info[j][0], routes_info[j][1]))
#             else:
#                 dict_result[inters] = [(routes_info[i][0], routes_info[i][1]), ((routes_info[j][0], routes_info[j][1]))]

print("Getting pair of stops by route")
for r in routes_info.items():
    stops1 = list(map(lambda stop: stop.get_stop(), r[1].get_stops()))
    for i in range(0, len(stops1) - 1):
        inters = (stops1[i], stops1[i + 1])
        if inters in dict_result:
            dict_result[inters].append(r[0])
        else:
            dict_result[inters] = [r[0]]

# file = open("ïnters.dat","w")
# marshal.dump(dict_result,file)
# file.close()

print("Getting pairs(set of routes,pair of stops)")
group_routes_ranges = []
for k in dict_result.keys():
    flag = True
    for g in group_routes_ranges:
        if g[0] == dict_result[k]:
            g[1].append(k)
            flag = False
    if flag:
        group_routes_ranges.append((dict_result[k], [k]))


# group_routes_ranges has pair(list_of_routes,pair of stops)

def powerset(lst):
    if not lst:
        return [[]]
    exclude_first = powerset(lst[1:])
    include_first = [[lst[0]] + x for x in exclude_first]
    return exclude_first + include_first

def powerset_1_less(lst):
    if len(lst)>1:
        yield lst[1:]
        for i in range(1,len(lst)):
            yield lst[0:i]+lst[i+1:len(lst)]

print("Getting pairs(subsets of routes,pair of stops)")
# group_routes_ranges_extend = []
# for g in group_routes_ranges:
#     for subgroup in powerset(g[0]):
#         if subgroup:
#             added = False
#             index=0
#             for gr in group_routes_ranges_extend:
#                 if gr[0] == subgroup:
#                     group_routes_ranges_extend[index] = (gr[0],[*(gr[1]),*(g[1])])
#                     added = True
#                     break
#                 index+=1
#             if not added:
#                 group_routes_ranges_extend.append((subgroup, g[1]))

group_routes_ranges_extend = {}
#TODO: if group of routes is only in one subset < set, so we can drop this group
for g in group_routes_ranges:
    for subgroup in powerset(g[0]):
        if subgroup:
            if tuple(subgroup) in group_routes_ranges_extend:
                group_routes_ranges_extend[tuple(subgroup)] = [*group_routes_ranges_extend[tuple(subgroup)], *g[1]]
            else:
                group_routes_ranges_extend[tuple(subgroup)] = g[1]




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


def rebuild_2(list_pair):
    result = []
    for i in list_pair:
        added = 0
        for r in result:
            if r[0] == i[1]:
                r.insert(0, i[0])
                added += 1
            if r[-1] == i[0]:
                r.append(i[1])
                added += 1
        if added == 2:
            # Search ranges with i[0] and i[1]
            searched_result = list(filter(lambda r: i[0] in r, result))
            result = list(filter(lambda r: not (i[0] in r), result))
            if searched_result[0][0] == i[0]:
                result.append(searched_result[1] + searched_result[0][2:])
            else:
                result.append(searched_result[0] + searched_result[1][2:])

        if added == 0:
            result.append([i[0], i[1]])
    return result


print("Rebuild set of pairs to ranges")
group_routes_ranges = map(lambda item: (item[0], rebuild_2(item[1])),
                          filter(lambda item: not(item[1] is None),group_routes_ranges_extend.items()))




result = dict(list(group_routes_ranges))
result_drop = []
print("Filter equal ranges of stops for subsets")
keys = list(result.keys())
for g in keys:
    group = list(g)
    # print("+".join(list(map(lambda r: r[0].get_name(), group))))
    for subgroup in powerset_1_less(group):
            #TODO: is has to compare as sets (but is is too rare)
            if result[tuple(subgroup)] == result[g]:
                result_drop.append(tuple(subgroup))

for r in result_drop:
    result[r] = None

result = list(filter(lambda g: not(g[1] is None),result.items()))
# print(result)

print("Trying to extent ranges")
for gr in result:
    print("+".join(list(map(lambda r: r[0].get_name(), gr[0]))))
    for parts in gr[1]:
        continuation = True
        next_stop_first = None
        last_stop = parts[-1]
        for route in gr[0]:
            #            routes_found = \
            #               list(filter(lambda r: r[0] == route[0] and r[1] == route[1], routes_info))
            route_found = routes_info[route]
            stops = route_found.get_stops()
            stops1 = list(map(lambda stop: stop.get_stop(), stops))
            index_last_stop = stops1.index(last_stop)
            if index_last_stop == len(stops1) - 1:
                continuation = False
                break
            else:
                next_stop = stops1[index_last_stop + 1]
                if next_stop_first is None:
                    next_stop_first = next_stop
                else:
                    if next_stop_first.get_name() != next_stop.get_name():
                        continuation = False
                        break
        if continuation:
            parts.append(next_stop_first)

quality_storage = Quality_storage()
print("Calculate qualities")
for gr in result:
    for parts in gr[1]:
        indexes = {}
        route_group = Route(-1, Equipment(-1),
                            "+".join(list(map(lambda r: r[0].get_name(), gr[0]))) + ": " + parts[0].get_name() + "-" +
                            parts[-1].get_name())
        timetable_builder = Timetable_builder_t_mos_ru()
        timetable_builder.set_id_route_t_mos_ru(-1).set_date(date).set_direction(len(parts))
        for s in parts:
            stop = timetable_builder.add_stop()
            stop.set_name(s.get_name())
            stop.set_coords(s.get_coords())
            for route in gr[0]:
                # routes_found = list(filter(lambda r: r[0] == route[0] and r[1] == route[1], routes_info))
                route_found = routes_info[route]
                if route in indexes:
                    times = route_found.get_stops()[indexes[route]].get_times()
                    indexes[route]+=1
                else:
                    list_for_search = [(i,route_found.get_stops()[i]) for i in range(0,len(route_found.get_stops()))]
                    times_all = list(filter(lambda r: r[1].get_stop() == s, list_for_search))
                    indexes[route]=times_all[0][0]+1
                    times = times_all[0][1].get_times()
                for t in times:
                    stop.add_item_timetable(t.get_time(), t.get_color_special_flight())
        timetable = timetable_builder.build()
        quality_storage.store_quality(route_group, timetable)
quality_storage.save('groups_qualities.csv')
