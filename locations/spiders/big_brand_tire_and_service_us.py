from json import loads
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BigBrandTireAndServiceUSSpider(Spider):
    name = "big_brand_tire_and_service_us"
    item_attributes = {"brand": "Big Brand Tire & Service", "brand_wikidata": "Q120784816"}
    allowed_domains = ["www.bigbrandtire.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.bigbrandtire.com/api/publicWeb/getLocations", data={"StoreBrandId": 1})

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for feature in response.json():
            if feature.get("storeClosed"):
                continue

            item = DictParser.parse(feature)
            item["branch"] = item.pop("name")
            item["website"] = "https://www.bigbrandtire.com/locations/" + feature["publicWebEndPoint"]

            if feature.get("storeSchedule"):
                item["opening_hours"] = OpeningHours()
                hours_dict = loads(feature["storeSchedule"])
                for day_hours in hours_dict:
                    if day_hours.get("storeClosed"):
                        continue
                    item["opening_hours"].add_range(
                        day_hours["dayName"], *day_hours["displayHours"].split(" - ", 1), "%I:%M%p"
                    )

            apply_category(Categories.SHOP_TYRES, item)
            yield item
