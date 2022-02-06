import datetime

import requests as requests

from auth import get_token_bot, get_path_qualities
from event_logger_impl import Event_logger_impl
from repository_sqlite import Repository_sqlite
from service_locator import Service_locator
from tools import loading, Quality_storage, loading_continue

service_locator = Service_locator.get_instance()
service_locator.register_service('event_logger', Event_logger_impl())

repository = Repository_sqlite('mosgortrans_20220115.sqlite')
service_locator.register_service('repository', repository)

event_logger = Service_locator.get_instance().get_service('event_logger')


def send_to_telegram(event):
    result = requests.post("https://api.tlgr.org/bot{}/sendMessage".format(get_token_bot()),
                           data={'chat_id': '@changes_transport_mos',
                                 'text': event.get_description()
                                 })
    if result.status_code != 200:
        print("Error with status {} body={}".format(result.status_code, result.text))
    else:
        print("body={}".format(result.text))


event_logger.register_listener(lambda event: send_to_telegram(event))

date = datetime.date(2022, 2, 7)


def send_to_file(event):
    with open("events" + date.strftime("%Y%m%d") + ".txt", 'a') as file:
        file.write(event.get_description() + "\n")
    pass


event_logger.register_listener(lambda event: send_to_file(event))

quality_storage = Quality_storage()

loading_continue(date, 1, 0, repository, quality_storage)
loading(date, 1, 1, repository, quality_storage)
quality_storage.save(get_path_qualities() + 'qualities_' + date.strftime("%Y%m%d") + '.csv')
