from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media
from locations.storefinders.stockist import StockistSpider


class WynsorsGBSpider(StockistSpider):
    name = "wynsors_gb"
    item_attributes = {"brand": "Wynsors World of Shoes", "brand_wikidata": "Q8040250"}
    key = "map_4q6wyk53"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        for field in location["custom_fields"]:
            if field["name"] == "Store Details":
                item["website"] = "https://www.wynsors.com{}".format(field["value"])
            elif field["name"] == "Store Facebook":
                set_social_media(item, SocialMedia.FACEBOOK, field["value"])

        apply_category(Categories.SHOP_SHOES, item)

        yield item
