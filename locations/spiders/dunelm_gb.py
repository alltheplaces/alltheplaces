from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class DunelmGBSpider(AlgoliaSpider):
    name = "dunelm_gb"
    item_attributes = {
        "name": "Dunelm",
        "brand": "Dunelm",
        "brand_wikidata": "Q5315020",
        "extras": Categories.SHOP_INTERIOR_DECORATION.value,
    }
    app_id = "FY8PLEBN34"
    api_key = "ae9bc9ca475f6c3d7579016da0305a33"
    index_name = "stores_prod"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["branch"] = item.pop("name")
        item["ref"] = feature["sapStoreId"]
        item["website"] = "https://www.dunelm.com/stores/" + feature["uri"]

        item["opening_hours"] = OpeningHours()
        for rule in feature["openingHours"]:
            item["opening_hours"].add_range(rule["day"], rule["open"], rule["close"])

        yield item
