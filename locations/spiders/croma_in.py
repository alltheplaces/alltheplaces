import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CromaINSpider(JSONBlobSpider):
    name = "croma_in"
    item_attributes = {"brand": "Cromā", "brand_wikidata": "Q5187683"}
    start_urls = [
        "https://api.croma.com/lookup/mobile-app/v1/storelocation?pageSize=2001&sort=asc&radius=25000&fields=FULL"
    ]
    locations_key = "stores"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        if city := feature.get("city"):
            feature["city"] = city["name"].title()
        if country := feature.get("country"):
            feature["country"] = country["isocode"]
        feature["ref"] = feature.pop("name")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["formattedAddress"]
        item["image"] = feature.get("storeImageUrl")
        if url := feature.get("url"):
            item["website"] = "https://www.croma.com" + url.split("?")[0]
        if item.get("email") == "customersupport@croma.com":
            item["email"] = None
        if isinstance(item.get("state"), dict):
            item["state"] = item["state"].get("name").title()
        if opening_hours := feature.get("openingHours"):
            item["opening_hours"] = self.parse_hours(opening_hours)
        apply_category(Categories.SHOP_ELECTRONICS, item)
        item["branch"] = item.pop("name").replace("Croma ", "").lstrip("- ")
        yield item

    def parse_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        times = re.findall(r"(\d{1,2}:\d{2})\s*([apAP][mM])", opening_hours.get("code") or "")
        if len(times) >= 2:
            (open_time, open_ap), (close_time, close_ap) = times[0], times[1]
            oh.add_days_range(
                DAYS, f"{open_time} {open_ap.upper()}", f"{close_time} {close_ap.upper()}", time_format="%I:%M %p"
            )
        return oh
