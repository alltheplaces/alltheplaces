from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class TelstraAUSpider(Spider):
    name = "telstra_au"
    item_attributes = {"brand": "Telstra", "brand_wikidata": "Q721162"}

    @staticmethod
    def make_request(offset: int, category: str, size: int = 50) -> JsonRequest:
        return JsonRequest(
            url=f"https://tapi.telstra.com/v1/gcm-geoprocessing-service/telstra/{category}/list",
            headers={"apikey": "tAqmM4O7ROFgWXYXiqAICbozH6UACU8K"},
            data={
                "point": {"lat": 0, "lon": 0},
                "pagination": {"size": size, "from": offset},
            },
            meta={"category": category},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for category in [
            "shops",
            # "air",  # Hot spots
            # "payphones",
            # "businesscentres",  # "Business technology centre"
        ]:
            yield self.make_request(0, category)

    def parse(self, response, **kwargs):
        for location in response.json()["results"][0]["value"][0]["featureList"]:
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            if location["type"] == "store":
                item["ref"] = location["storecode"]
                item["email"] = location["store_email"]
                item["opening_hours"] = OpeningHours()
                for day in DAYS_FULL:
                    if rule := location[f"hrs_{day.lower()[:3]}"]:
                        if rule == "Closed":
                            continue
                        opening, closing = rule.split(" - ", maxsplit=1)
                        item["opening_hours"].add_range(day, opening, closing, time_format="%I:%M %p")
                apply_category(Categories.SHOP_MOBILE_PHONE, item)
            elif location["type"] == "payphone":
                item["ref"] = location["cabinet_id"]
                item["phone"] = location["cli"]
                apply_category(Categories.TELEPHONE, item)
            elif location["type"] == "hotspot":
                continue
            elif location["type"] == "TECHNOLOGY_CENTRE":
                continue
            yield item

        pagination = response.json()["results"][0]["value"][0]["pagination"]
        if pagination["count"] == pagination["size"]:
            yield self.make_request(pagination["from"] + pagination["size"], response.meta["category"])
