# This is a sample Python script.

import datetime
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests

from auth import get_token_bot
from event_logger_impl import Event_logger_impl
from repository_sqlite import Repository_sqlite
from service_locator import Service_locator
from tools import loading

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


service_locator = Service_locator.get_instance()
service_locator.register_service('event_logger', Event_logger_impl())

repository = Repository_sqlite('mosgortrans_20220115.sqlite')
loading(datetime.date(2022, 1, 16), 1, 0, repository)

event_logger = Service_locator.get_instance().get_service('event_logger')

# with open("events20220116.txt", 'w') as file:
#     file.write("\n".join(event_logger.get_descriptions()))

# requests.post("https://api.telegram.org/{}/sendMessage".format(get_token_bot()),
#               params={'chat_id':'@changes_transport_mos',
#                       'text': "\n".join(event_logger.get_descriptions())
#                       })


#routes_info = repository.load_routes_info_by_number(393, 1)
#print(routes_info)

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
