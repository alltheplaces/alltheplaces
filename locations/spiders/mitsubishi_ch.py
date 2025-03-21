import re
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiCHSpider(JSONBlobSpider):
    name = "mitsubishi_ch"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.ch/haendler/"]

    def extract_json(self, response: Response) -> list[dict]:
        return [
            chompjs.parse_js_object(location)
            for location in re.findall(
                r"locations\[\d+\]\s*=\s*(.+?}\));",
                response.xpath('//script[contains(text(), "locationData")]/text()').get(""),
                re.DOTALL,
            )
        ]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("marker", {}) | feature.pop("locationData", {}))
        feature["id"] = feature.get("externalId")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["name"] = feature.get("organisation")
        item["website"] = response.urljoin(feature.get("www"))

        if feature.get("hasSales"):
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, feature.get("hasService"))
        elif feature.get("hasService"):
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
