from typing import Iterable

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class EmberInnsGBSpider(WoosmapSpider):
    name = "ember_inns_gb"
    item_attributes = {"brand": "Ember Inns", "brand_wikidata": "Q116272278"}
    key = "woos-63fb5127-b80c-3aa9-b672-bee33a31a43d"
    origin = "https://www.emberinns.co.uk"

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
