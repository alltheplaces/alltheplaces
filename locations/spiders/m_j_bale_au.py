from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.david_jones_au_nz import DavidJonesAUNZSpider
from locations.spiders.myer_au import MyerAUSpider


class MJBaleAUSpider(JSONBlobSpider):
    name = "m_j_bale_au"
    item_attributes = {"brand": "M.J. Bale", "brand_wikidata": "Q97516243"}
    allowed_domains = ["www.mjbale.com"]
    start_urls = ["https://www.mjbale.com/apps/arcbridge/v1/shopify/stores/check"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["clickandcollect_enabled"] != 1 and feature["deptstore_enabled"] != 1:
            return

        item["ref"] = feature["code"]
        item["branch"] = item.pop("name", None)
        item["addr_full"] = merge_address_lines([feature.get("address_street_1"), feature.get("address_street_2")])

        if feature["name"].startswith("David Jones "):
            item["located_in"] = DavidJonesAUNZSpider.item_attributes["brand"]
            item["located_in_wikidata"] = DavidJonesAUNZSpider.item_attributes["brand_wikidata"]
        elif feature["name"].startswith("Myer "):
            item["located_in"] = MyerAUSpider.item_attributes["brand"]
            item["located_in_wikidata"] = MyerAUSpider.item_attributes["brand_wikidata"]

        if feature.get("data_times"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join([day_hours["title"] for day_hours in feature["data_times"]])
            )

        apply_category(Categories.SHOP_CLOTHES, item)
        item["extras"]["alt_ref"] = str(feature["store_number"])

        yield item
