from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MerkalESSpider(Spider):
    name = "merkal_es"
    item_attributes = {"brand": "Merkal", "brand_wikidata": "Q126894589"}
    start_urls = ["https://www.merkal.com/checkout/GetProvinces"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for province in response.json():
            yield JsonRequest(
                url="https://www.merkal.com/checkout/GetStoresByProvince?provinceId={}".format(province["id"]),
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["orgUnitNumber"]
            item["lat"], item["lon"] = location["latLng"].split(",")

            item["opening_hours"] = OpeningHours()
            for day, times in location["workingHours"].items():
                if times:
                    item["opening_hours"].add_range(
                        day,
                        "{}:{}".format(times["openTime"]["hour"], times["openTime"]["minutes"]),
                        "{}:{}".format(times["closeTime"]["hour"], times["closeTime"]["minutes"]),
                    )

            apply_category(Categories.SHOP_SHOES, item)

            yield item
