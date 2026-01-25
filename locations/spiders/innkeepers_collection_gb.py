from typing import Iterable

from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class InnkeepersCollectionGBSpider(WoosmapSpider):
    name = "innkeepers_collection_gb"
    item_attributes = {"brand": "Innkeeper's Collection", "brand_wikidata": "Q6035891"}
    key = "woos-e20ab4a6-1a2d-33cb-b128-3ee59d15c383"
    origin = "https://www.innkeeperscollection.co.uk"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["website"] = feature.get("properties").get("user_properties").get("primaryWebsiteUrl")
        item["branch"] = item.pop("name").replace("Innkeeper's Collection ", "")
        item["name"] = feature.get("properties").get("user_properties").get("pubName")
        yield item
