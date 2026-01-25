from typing import Iterable

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class InnkeepersCollectionGBSpider(WoosmapSpider):
    name = "innkeepers_collection_gb"
    item_attributes = {"brand": "Innkeepers Collection", "brand_wikidata": "Q6035891"}
    key = "woos-e20ab4a6-1a2d-33cb-b128-3ee59d15c383"
    origin = "https://www.innkeeperscollection.co.uk"

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
