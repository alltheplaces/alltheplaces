from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class BurgerKingRUSpider(Spider):
    name = "burger_king_ru"
    item_attributes = {"brand": "Бургер Кинг", "brand_wikidata": "Q177054"}
    allowed_domains = ["orderapp.burgerkingrus.ru"]
    start_urls = ["https://orderapp.burgerkingrus.ru/api/v3/restaurant/list"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True  # Qrator bot blocking in use

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url)

    def parse(self, response):
        for location in response.json()["response"]["list"]:
            if location["status"] != 1:
                continue
            item = DictParser.parse(location)
            item["street_address"] = location.pop("addr_full", None)
            item["opening_hours"] = OpeningHours()
            for day_number, day_name in enumerate(DAYS):
                day_hours = location["timetable"]["hall"][day_number]
                if not day_hours["isActive"]:
                    continue
                if day_hours["isAllTime"]:
                    start_time = "00:00"
                    end_time = "23:59"
                else:
                    start_time = day_hours["timeFrom"]
                    end_time = day_hours["timeTill"]
                item["opening_hours"].add_range(day_name, start_time, end_time)
            apply_yes_no(Extras.WIFI, item, location["wifi"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["king_drive"] and location["king_drive_enabled"], False)
            yield item
