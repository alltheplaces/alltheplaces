import re
from json import loads
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BonmarcheGBSpider(JSONBlobSpider):
    name = "bonmarche_gb"
    item_attributes = {"brand": "Bonmarché", "brand_wikidata": "Q4942146"}
    allowed_domains = ["www.bonmarche.co.uk"]
    locations_key = "stores"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("GB", 500):
            lat, lon = city["latitude"], city["longitude"]
            yield JsonRequest(
                url=f"https://www.bonmarche.co.uk/on/demandware.store/Sites-BONMARCHE-GB-Site/en_GB/Stores-FindStores?lat={lat}&long={lon}"
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["name"]
        item.pop("name", None)
        item["addr_full"] = feature["address2"]
        item.pop("street_address", None)
        item.pop("website", None)

        try:
            item["opening_hours"] = OpeningHours()
            hours = loads(re.sub(r"\s+", "", feature["storeHours"]).replace(".", ":"))
            for day_name, day_hours in hours.items():
                if "CLOSED" in day_hours.upper():
                    item["opening_hours"].set_closed(day_name)
                else:
                    start_time, end_time = day_hours.split("-", 1)
                    end_time = end_time.replace("17:30pm", "5:30pm").replace("16:00pm", "4:00pm").replace("om", "pm")
                    if "AM" in start_time.upper() or "PM" in start_time.upper():
                        time_format = "%I:%M%p"
                    else:
                        time_format = "%H:%M"
                    item["opening_hours"].add_range(day_name.title(), start_time, end_time, time_format=time_format)
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {e}")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
