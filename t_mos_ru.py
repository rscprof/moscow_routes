import re
from abc import abstractmethod
from datetime import datetime, time
from typing import Optional

import requests

from logger import Logger
from model import Equipment, Route, Timetable, Timetable_builder
from model_impl import Timetable_builder_t_mos_ru
from printer import Printer, PrinterDoNothing


class parser_timetable:
    """"Interface for parser"""

    @abstractmethod
    def parse(self, text: str) -> Timetable_builder:
        pass


class parser_timetable_t_mos_ru(parser_timetable):
    """"Parser for timetable from t.mos.ru implementation"""

    def __init__(self, builder: Timetable_builder, printer: Printer = PrinterDoNothing()):
        """"Initialize parser
        :param builder: Builder for Timetable for route
        :param printer: Object for printing timetable during parse (usually object do nothing)
        """
        self.builder = lambda: builder
        self.printer = lambda: printer

    def parse(self, text: str) -> Timetable_builder:
        """Parse text from https://transport.mos.ru/ru/ajax/App/ScheduleController/getRoute (for format using
        2022-Jan-11)

        Since 12.01.2022 t.mos.ru drop data-services from results

        @param text: text for parse
        @return Timetable for route
        """
        result_stops = type(self.builder())()
        # stops = re.finditer(r'data-stop="([^"]*?)".*?data-services="([^"]*?)".*?d-inline.*?>(.*?)<(.*?)</li>', text,
        #                     re.M + re.S
        #                     )
        stops = re.finditer(r'data-stop="(.*?)".*?d-inline.*?>(.*?)<(.*?)</li>', text,
                            re.M + re.S
                            )

        for stop in stops:
            id_stop = stop.group(1)
            # data_services = stop.group(2)
            name_stop = stop.group(2)
            description = stop.group(3)
            self.printer().print(name_stop)
            hours = re.finditer(r'dt1.*?(\d\d):(.*?)</div>\s*</div>\s*</div>', description, re.M + re.S)
            # result_stops.set_data_services(int(data_services))
            timetable_stop = result_stops.add_stop(id_stop, name_stop)
            for hour in hours:
                num_hour = int(hour.group(1))
                minutes_text = hour.group(2)
                self.printer().print(str(num_hour), end=": ")
                minutes = re.finditer(r'div10([^>]*)>\s*(\d\d)', minutes_text, re.M + re.S)
                for minute in minutes:
                    num_minute = int(minute.group(2))
                    if minute.group(1).find('red') >= 0:
                        min_red = True
                    else:
                        min_red = False
                    if min_red:
                        self.printer().print("{}red".format(num_minute), end=" ")
                        pass
                    else:
                        self.printer().print(str(num_minute), end=" ")
                        pass
                    time_flight = time(num_hour, num_minute)
                    timetable_stop.add_item_timetable(time_flight, min_red)
                self.printer().print()
        return result_stops


class Parser_routes:

    @abstractmethod
    def parse(self, text: str) -> [Route]:
        pass


class Parser_routes_t_mos_ru(Parser_routes):

    def __init__(self, logger: Logger):
        self.logger = lambda: logger

    def parse(self, text: str) -> [Route]:
        """"Parses route info from transport.mos.ru (name, id, type)
        :param text: text for parsing from t.mos.ru
        :return list of Route
        """
        result = re.finditer(r'<a.*?href=.*?route/(\d+).*?<div.*?ic[ ]([a-z-]+).*?</i>\s*(\S+?)\s*</div>', text,
                             re.M + re.S)
        list_routes = []

        for route in result:
            num = int(route.group(1))
            type_route = route.group(2)
            if type_route.find('-bus') >= 0:
                type_route = Equipment.bus()
            elif type_route.find('tramway') >= 0:
                type_route = Equipment.tramway()
            elif type_route.find('trolleybus') >= 0:
                type_route = Equipment.trolleybus()
            else:
                self.logger().error("Debug: {}".format(type_route))
                type_route = None
            name = route.group(3)
            list_routes.append(Route(num, type_route, name))
        return list_routes


def get_route(date: datetime.date, id_route_t_mos_ru: str, direction: int, logger: Logger,
              get_route_url: str = 'https://transport.mos.ru/ru/ajax/App/ScheduleController/getRoute',
              parser: parser_timetable = parser_timetable_t_mos_ru(builder=Timetable_builder_t_mos_ru())
              ) -> Timetable:
    """Get timetable for route by date and direction
        :param date: date of timetable for route
        :param id_route_t_mos_ru: id of route from t.mos.ru
        :param direction: direction for route (0 or 1)
        :param logger: Logger object for printing or saving log
        :param get_route_url URL for requesting timetable
        :param parser for timetable
        :return timetable for route by date and direction
    """
    try:
        response = requests.get(get_route_url,
                                params={
                                    'mgt_schedule[date]': date.strftime("%d.%m.%Y"),
                                    'mgt_schedule[route]': id_route_t_mos_ru,
                                    'mgt_schedule[page]': '',
                                    'mgt_schedule[direction]': direction,
                                }
                                )
        if response.status_code == 200:
            logger.print("Get route #{}".format(id_route_t_mos_ru))
            route_info = parser.parse(response.text)
        else:
            logger.error("Error status: {}".format(response.status_code))
            route_info = None
    except requests.exceptions.RequestException as e:
        logger.error("Error " + str(e.strerror))
        route_info = None

    if not (route_info is None):
        result = route_info.set_id_route_t_mos_ru(id_route_t_mos_ru).set_direction(direction).set_date(date).build()
    else:
        result = None
    return result


def get_list_routes(work_time: int, direction: int, logger: Logger,
                    parser: Parser_routes = None,
                    get_routes_url: str = 'https://transport.mos.ru/ru/ajax/App/ScheduleController/getRoutesList'
                    ) -> Optional[list[Route]]:
    """get list routes by work_time and direction from transport.mos.ru
        :param parser: function to parse got string
        :param logger: Logger for printing or saving messages
        :param get_routes_url: url for requesting routes
        :param work_time: work day or not (1 or 0)
        :param direction: 0
        :return list of Route
    """
    if parser is None:
        parser = Parser_routes_t_mos_ru(logger)
    try:
        page = 1
        result_routes = []
        while True:
            response = requests.get(get_routes_url,
                                    params={
                                        'mgt_schedule[search]': '',
                                        'mgt_schedule[filters]': '',
                                        'mgt_schedule[work_time]': work_time,
                                        'mgt_schedule[page]': page,
                                        'mgt_schedule[direction]': direction,
                                    }
                                    )
            if response.status_code == 200:
                logger.print("Get page #{}".format(page))
                routes = parser.parse(response.text)
                result_routes += routes
                if not routes:
                    break
            else:
                logger.error("Error status: {}".format(response.status_code))
            page = page + 1
    except requests.exceptions.RequestException as e:
        logger.error("Error " + e.strerror)
        result_routes = None

    return result_routes
