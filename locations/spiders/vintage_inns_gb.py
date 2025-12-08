from typing import Iterable

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class VintageInnsGBSpider(WoosmapSpider):
    name = "vintage_inns_gb"
    item_attributes = {"brand": "Vintage Inns", "brand_wikidata": "Q87067899"}
    key = "woos-f6518149-ce6e-365c-b912-12ae5d6c8b2f"
    origin = "https://www.vintageinn.co.uk"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["website"] = feature.get("properties").get("user_properties").get("primaryWebsiteUrl")
        oh = OpeningHours()
        try:
            for day_time in feature["properties"]["user_properties"].get("tradingHours"):
                day = day_time["day"]
                open_time = day_time["openTime"]
                close_time = day_time["closeTime"]
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        except:
            pass
        item["opening_hours"] = oh
        yield item
