from urllib.parse import urljoin

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, OpeningHours


class WinelabRUSpider(scrapy.Spider):
    name = "winelab_ru"
    item_attributes = {"brand_wikidata": "Q109907753"}
    start_urls = ["https://www.winelab.ru/store-map/results"]

    def parse(self, response):
        for poi in response.json()["results"]:
            poi.update(poi.pop("address", {}))
            poi.update(poi.pop("geoPoint", {}))
            item = DictParser.parse(poi)
            item["ref"] = item["name"]
            item["name"] = None  # name is a store number
            item["addr_full"] = poi.get("formattedAddress")
            item["website"] = urljoin("https://www.winelab.ru/stores/", item["ref"])
            if hours := poi.get("openingHours", {}).get("weekDayOpeningList", []):
                oh = OpeningHours()
                for hour in hours:
                    open = hour.get("openingTime", {}).get("formattedHour")
                    close = hour.get("closingTime", {}).get("formattedHour")
                    oh.add_range(DAYS_RU[hour["weekDay"]], open, close)
                item["opening_hours"] = oh.as_opening_hours()
            yield item
