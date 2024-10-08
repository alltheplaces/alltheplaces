from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsTRSpider(Spider):
    name = "mcdonalds_tr"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.com.tr"]
    start_urls = ["https://www.mcdonalds.com.tr/restaurants/getstores"]
    # A significant proportion of requests are either blocked (possibly
    # by the Turkish government) or the website is very unreliable.
    # Minimise requests and retry a few extra times.
    custom_settings = {"ROBOTSTXT_OBEY": False, "RETRY_TIMES": 10}

    def start_requests(self):
        data = {
            "cityId": "0",
            "subcity": "",
            "avm": "false",
            "birthday": "false",
            "isDeliveryStore": "false",
            "open724": "false",
            "breakfast": "false",
            "mcdcafe": "false",
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data)

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["addr_full"] = location["STORE_ADDRESS"]
            item["opening_hours"] = OpeningHours()
            if location["TWENTYFOUR_HRS"]:
                item["opening_hours"].add_days_range(DAYS, "00:00", "24:00")
            else:
                open_time = (
                    str(location["STORE_OPEN_AT"]["Hours"]).zfill(2)
                    + ":"
                    + str(location["STORE_OPEN_AT"]["Minutes"]).zfill(2)
                )
                close_time = (
                    str(location["STORE_CLOSE_AT"]["Hours"]).zfill(2)
                    + ":"
                    + str(location["STORE_CLOSE_AT"]["Minutes"]).zfill(2)
                )
                item["opening_hours"].add_days_range(DAYS, open_time, close_time)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["MC_DRIVE"], False)
            apply_yes_no(Extras.DELIVERY, item, location["IS_DELIVERY_STORE"], False)
            yield item
