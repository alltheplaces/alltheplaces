from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class BigBrandTireAndServiceUSSpider(Spider):
    name = "big_brand_tire_and_service_us"
    item_attributes = {
        "brand": "Big Brand Tire & Service",
        "brand_wikidata": "Q120784816",
        "extras": Categories.SHOP_TYRES.value,
    }
    allowed_domains = ["www.bigbrandtire.com"]
    start_urls = ["https://www.bigbrandtire.com/api/publicWeb/getLocations"]

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {"appBrandId": 1}
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json():
            if feature.get("storeClosed"):
                continue

            item = DictParser.parse(feature)
            item["branch"] = feature.get("displayName")
            item.pop("name", None)
            item["website"] = "https://www.bigbrandtire.com/locations/" + feature["publicWebEndPoint"]

            if feature.get("storeSchedule"):
                item["opening_hours"] = OpeningHours()
                hours_dict = loads(feature["storeSchedule"])
                for day_hours in hours_dict:
                    if day_hours.get("storeClosed"):
                        continue
                    item["opening_hours"].add_range(
                        DAYS_EN[day_hours["dayName"]], *day_hours["displayHours"].split(" - ", 1), "%I:%M%p"
                    )

            yield item
