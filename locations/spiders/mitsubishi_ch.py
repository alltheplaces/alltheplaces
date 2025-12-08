import re
from typing import Any

import chompjs
from scrapy import Request
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

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Any:
        item["street_address"] = item.pop("addr_full", None)
        item["name"] = feature.get("organisation")
        item["website"] = response.urljoin(feature.get("www"))

        # hasSales, hasService fields are always false.Hence, we need to determine category from the POI pages.

        yield Request(url=item["website"], callback=self.parse_location, cb_kwargs=dict(item=item))

    def parse_location(self, response: Response, item: Feature) -> Any:
        location_type = (
            response.xpath('//*[@class="haendler-heading-details"]//*[@class="haendler-icon-text"]').get("").lower()
        )

        if "verkauf und service" in location_type:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, True)
        elif "verkauf" in location_type:
            apply_category(Categories.SHOP_CAR, item)
        elif "service" in location_type:
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
