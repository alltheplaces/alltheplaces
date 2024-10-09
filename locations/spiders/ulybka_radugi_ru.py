from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class UlybkaRadugiRUSpider(scrapy.Spider):
    name = "ulybka_radugi_ru"
    item_attributes = {"brand": "Улыбка радуги", "brand_wikidata": "Q109734104"}
    start_urls = [
        "http://delivery.shop.api.svs.tdera.ru/stores?active=1&retailPoint=1&sortBy=geoCoordinates asc&page=1&limit=10000"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json()["_embedded"]["items"]:
            item = DictParser.parse(poi)
            item["city"] = poi["city"]["title"]
            item["lon"], item["lat"] = poi["geoCoordinates"]
            item["housenumber"] = poi.get("house")
            item["street_address"] = poi.get("addressSMS")
            item["lon"], item["lat"] = poi["geoCoordinates"]
            if start_date := poi.get("dateOpening"):
                item["extras"]["start_date"] = "-".join(reversed(start_date.split(".")))
            if poi.get("openingSoon"):
                # TODO: also temporaryClosed and underReconstruction
                yield None
            else:
                apply_category(Categories.SHOP_CHEMIST, item)
                self.parse_hours(item, poi)
                yield item

    def parse_hours(self, item: Feature, poi: dict):
        if hours := poi.get("openingHours"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    day = DAYS[int(hour["weekDay"]) - 1]
                    if hour.get("closed") is True:
                        oh.set_closed(day)
                        continue
                    open_time = hour["openAt"]
                    close_time = hour["closeAt"]
                    oh.add_range(day, open_time, close_time, "%H:%M:%S")
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
