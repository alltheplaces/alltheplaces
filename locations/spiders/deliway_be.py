from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DeliwayBESpider(JSONBlobSpider):
    name = "deliway_be"
    item_attributes = {"brand": "Deliway", "brand_wikidata": "Q126195408"}
    start_urls = ["https://stores.deliway.be/locations?version=v3&fitAll=true&language=nl"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature["street_address"] = feature.pop("street")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Deliway ", "")
        item["ref"] = feature.get("externalId")

        try:
            item["opening_hours"] = self.parse_opening_hours(feature["businessHours"])
        except:
            self.logger.error("Error parsing opening hours")

        apply_category(Categories.FAST_FOOD, item)

        yield item

    def parse_opening_hours(self, business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            oh.add_range(DAYS[rule["startDay"] - 1], rule["openTimeFormat"], rule["closeTimeFormat"])
        return oh
