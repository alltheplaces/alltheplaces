from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PioneerCASpider(scrapy.Spider):
    name = "pioneer_ca"
    item_attributes = {"brand": "Pioneer", "brand_wikidata": "Q7196684"}
    start_urls = [
        "https://journie.ca/pioneer/api/locations/nearest?country=CA&pageSize=1000&lat=43.653226&lon=-79.3831843&range=100000000&brand=Pioneer"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["street_address"] = location["siteAddressLine1"]
            item["city"] = location["siteCity"]
            item["state"] = location["siteStateProvince"]
            item["postcode"] = location["sitePostalCode"]
            item["website"] = item["extras"]["website:en"] = "https://journie.ca/pioneer/on-en/locations/{}".format(
                location["siteNumber"]
            )
            item["extras"]["website:fr"] = "https://journie.ca/pioneer/on-fr/locations/{}".format(
                location["siteNumber"]
            )
            apply_category(Categories.FUEL_STATION, item)
            item["opening_hours"] = OpeningHours()
            for day_time in location["siteRegularHours"]:
                day = day_time["dayOfWeek"]
                open_time = day_time["openTime"]
                close_time = day_time["closeTime"]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item
