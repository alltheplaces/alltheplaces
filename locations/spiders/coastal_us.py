from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider


class CoastalUSSpider(AlgoliaSpider):
    name = "coastal_us"
    item_attributes = {"brand": "Coastal", "brand_wikidata": "Q134452319"}
    api_key = "f63cb6e4867bb439abde23d6dfb957b5"
    app_id = "8PZVMJ4BDW"
    index_name = "Stores_Coastal_Production"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("address2"), feature.get("address1")])
        item["website"] = feature["detailsUrl"]
        if image := feature.get("imageUrl"):
            if "/coastal_store_exterior_general.png" not in image:
                item["image"] = image.split("?", 1)[0]
        item.pop("email", None)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature["storeHours"])
        apply_category(Categories.SHOP_COUNTRY_STORE, item)
        yield item
