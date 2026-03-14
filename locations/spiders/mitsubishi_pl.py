import re
from copy import deepcopy
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiPLSpider(JSONBlobSpider):
    name = "mitsubishi_pl"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi.pl/dealerzy"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            re.search(
                r"dealerLocations\":(\[.*\])}\]\],\[\[\"\$\"",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )

    def build_sales_item(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["addr_full"] = feature["full_address"]
        item["name"] = feature["dealer_name"]

        if isinstance(feature["dealer_websites"], list):
            item["website"] = feature["dealer_websites"][0]["url"]

        services = feature["services"]
        sales_available = "SHOWROOM" in services
        service_available = "SERVICE" in services

        if sales_available:
            sales_item = self.build_sales_item(item)
            if service_available:
                apply_yes_no(Extras.CAR_REPAIR, sales_item, True)
            yield sales_item

        if service_available:
            service_item = self.build_service_item(item)
            yield service_item

        if not sales_available and not service_available:
            self.logger.error(f"Unknown services: {services}, {item['name']}, {item['ref']}")
