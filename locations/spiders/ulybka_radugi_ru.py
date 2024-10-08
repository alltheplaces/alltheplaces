from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class UlybkaRadugiRUSpider(scrapy.Spider):
    name = "ulybka_radugi_ru"
    start_urls = [
        "http://delivery.shop.api.svs.tdera.ru/stores?active=1&retailPoint=1&sortBy=geoCoordinates asc&fields[0]=id&fields[1]=code&fields[2]=geoCoordinates&fields[3]=subwayStations&fields[4]=openingHours&fields[5]=address&fields[6]=retailPoint&fields[7]=new&fields[8]=openingSoon&fields[9]=temporaryClosed&fields[10]=underReconstruction&fields[11]=pickupPoint&fields[12]=dateOpening&page=1&limit=10000"
    ]
    item_attributes = {"brand": "Улыбка радуги", "brand_wikidata": "Q109734104"}

    def parse(self, response: Response) -> Iterable[Feature]:
        for poi in response.json()["_embedded"]["items"]:
            item = DictParser.parse(poi)
            if poi.get("openingSoon"):
                # TODO: also temporaryClosed and underReconstruction
                yield None
            else:
                item["lat"] = poi["geoCoordinates"][1]
                item["lon"] = poi["geoCoordinates"][0]
                apply_category(Categories.SHOP_CHEMIST, item)
                self.parse_hours(item, poi)
                yield item

    def parse_hours(self, item: Feature, poi: dict):
        if hours := poi.get("openingHours"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    day = DAYS[int(hour["weekDay"]) - 1]
                    open_time = hour["openAt"]
                    close_time = hour["closeAt"]
                    oh.add_range(day, open_time, close_time, "%H:%M:%S")
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
