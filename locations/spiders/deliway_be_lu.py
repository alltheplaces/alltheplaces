from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DeliwayBELUSpider(JSONBlobSpider):
    name = "deliway_be_lu"
    start_urls = ["https://stores.deliway.be/api/v3/locations"]
    item_attributes = {"brand": "Deliway", "brand_wikidata": "Q126195408"}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature["street_address"] = feature.pop("street")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Deliway ", "")
        item["ref"] = feature.get("externalId")
        item["opening_hours"] = OpeningHours()
        for rule in feature["businessHours"]:
            item["opening_hours"].add_range(
                DAYS[rule.get("startDay") - 1], rule.get("openTimeFormat"), rule.get("closeTimeFormat"), "%H:%M"
            )
        apply_category(Categories.FAST_FOOD, item)

        yield item
