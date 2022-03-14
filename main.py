import datetime
import logging

import requests as requests

from auth import get_token_bot, get_path_qualities
from event_logger_impl import Event_logger_impl
from repository_sqlite import Repository_sqlite
from service_locator import Service_locator
from tools import loading, Quality_storage, loading_continue

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

service_locator = Service_locator.get_instance()
service_locator.register_service('event_logger', Event_logger_impl())

# repository = Repository_sqlite('mosgortrans_20220312.sqlite')

repository = Repository_sqlite('mosgortrans_20220115.sqlite')
# repository = Repository_sqlite('mosgortrans_coords.sqlite')
service_locator.register_service('repository', repository)

event_logger = Service_locator.get_instance().get_service('event_logger')


def send_to_telegram(event):
    result = requests.post("https://api.telegram.org/bot{}/sendMessage".format(get_token_bot()),
                           data={'chat_id': '@changes_transport_mos',
                                 'text': event.get_description()
                                 })
    if result.status_code != 200:
        print("Error with status {} body={}".format(result.status_code, result.text))
    else:
        print("body={}".format(result.text))


event_logger.register_listener(lambda event: send_to_telegram(event))

date = datetime.date(2022, 3, 15)


def send_to_file(event):
    with open("events" + date.strftime("%Y%m%d") + ".txt", 'a') as file:
        file.write(event.get_description() + "\n")
    pass


event_logger.register_listener(lambda event: send_to_file(event))

quality_storage = Quality_storage()

loading(date, 1, 0, repository, quality_storage)
loading(date, 1, 1, repository, quality_storage)
quality_storage.save(get_path_qualities() + 'qualities_' + date.strftime("%Y%m%d") + '.csv')

# date_old = date - datetime.timedelta(days=7)
#
# import matplotlib
# import matplotlib.pyplot as plt
# import numpy as np
# import datetime
#
# routes = repository.get_last_snapshot(1)
# num = list(filter(lambda route: route.get_name()=='с356',routes))[0].get_id_mgt()
#
#
# timetables = repository.load_routes_info_by_number_and_date(num, 0,date)
#
# x = list(map(lambda t: t.get_time().minute + t.get_time().hour * 60, list(timetables.get_stops())[1].get_times()))
# y = list(map(lambda coord: date.toordinal(), x))
#
#
# plt.plot(x, y, '^',rasterized=True,color="Black")
# timetables = repository.load_routes_info_by_number_and_date(num, 0,date_old)
#
# x = list(map(lambda t: t.get_time().minute + t.get_time().hour * 60, list(timetables.get_stops())[1].get_times()))
# y = list(map(lambda coord: date.toordinal(), x))
#
#
# plt.plot(x, y, 'v',rasterized=True,color="Blue")
#
#
# plt.xticks([x for x in range(0, 24 * 60, 60)], ["{}:00".format(x) for x in range(0, 24)])
# plt.yticks([date.toordinal()], [date.strftime("%d.%m.%Y")])
# plt.gcf().autofmt_xdate()
# plt.show()
