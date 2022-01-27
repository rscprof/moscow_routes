from repository_sqlite import Repository_sqlite
from tools import calculate_quality_set, calculate_quality_count

repository = Repository_sqlite('mosgortrans_20220115.sqlite')
snapshot = repository.get_last_snapshot(1)
found_routes = list(filter(lambda route: route.get_name() == "м16", snapshot))
route_info = repository.load_routes_info_by_number(found_routes[-1].get_id_mgt(), 0)
result = calculate_quality_set(route_info[-1])
print(route_info[-1])
print(result)
print(', '.join(map(lambda r: "{} - {}".format(r[0].strftime("%H:%M"), r[1].strftime("%H:%M")), result)))
result = calculate_quality_count(route_info[-1])
print(list(result))
