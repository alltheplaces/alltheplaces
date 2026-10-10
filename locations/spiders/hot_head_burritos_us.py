from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# The locations page's JS bundle fetches this JSON API directly; it is grouped
# by state and includes locations not yet open, marked with status "Coming
# Soon", which are skipped here.


class HotHeadBurritosUSSpider(Spider):
    name = "hot_head_burritos_us"
    item_attributes = {"brand": "Hot Head Burritos", "brand_wikidata": "Q5910008"}
    allowed_domains = ["hotheadburritos.com"]
    start_urls = ["https://hotheadburritos.com/api/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for state in response.json():
            for location in state["stores"]:
                if location.get("status") != "Open":
                    continue

                item = Feature()
                item["ref"] = location["id"]
                item["branch"] = location.get("name")
                item["street_address"] = location.get("address")
                item["city"] = location.get("city")
                item["state"] = location.get("state")
                item["postcode"] = str(location["zip"]).zfill(5) if location.get("zip") else None
                item["lat"] = location.get("lat")
                item["lon"] = location.get("lng")
                item["phone"] = location.get("phone")
                item["website"] = location.get("webpage")

                item["opening_hours"] = OpeningHours()
                for day, hours in (location.get("hours") or {}).items():
                    if not hours or " - " not in hours:
                        continue
                    open_time, close_time = hours.split(" - ", 1)
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M%p")

                apply_category(Categories.FAST_FOOD, item)

                yield item
